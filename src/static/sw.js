// ============================================================
// SERVICE WORKER — Attendance Portal PWA
// Handles: Offline caching, Background Sync, Push Notifications
// ============================================================

const CACHE_NAME = "attendance-portal-v1";
const SYNC_TAG = "sync-attendance";

// Pages & assets to cache on install (App Shell)
const APP_SHELL = [
  "/teacher",
  "/teacher-dashboard",
  "/teacher-attendance",
  "/static/teacher.css",
  "/static/admin.css",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/offline.html"
];

// ─── INSTALL ────────────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[SW] Caching app shell");
      return cache.addAll(APP_SHELL).catch((err) => {
        console.warn("[SW] Some shell resources failed to cache:", err);
      });
    })
  );
  self.skipWaiting();
});

// ─── ACTIVATE ───────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => {
            console.log("[SW] Deleting old cache:", key);
            return caches.delete(key);
          })
      )
    )
  );
  self.clients.claim();
});

// ─── FETCH — Network first, fallback to cache ────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin
  if (request.method !== "GET" || !url.origin.includes(self.location.origin)) return;

  // API / POST routes — don't intercept
  if (request.method === "POST") return;

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful GET responses
        if (response && response.status === 200) {
          const cloned = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, cloned));
        }
        return response;
      })
      .catch(() => {
        // Offline fallback
        return caches.match(request).then((cached) => {
          if (cached) return cached;
          // For navigation requests, show offline page
          if (request.mode === "navigate") {
            return caches.match("/offline.html");
          }
        });
      })
  );
});

// ─── BACKGROUND SYNC ────────────────────────────────────────
self.addEventListener("sync", (event) => {
  if (event.tag === SYNC_TAG) {
    console.log("[SW] Background sync triggered");
    event.waitUntil(syncPendingAttendance());
  }
});

async function syncPendingAttendance() {
  const db = await openIDB();
  const pending = await getAllPending(db);

  if (pending.length === 0) {
    console.log("[SW] Nothing to sync");
    return;
  }

  console.log(`[SW] Syncing ${pending.length} pending records...`);
  let synced = 0;

  for (const record of pending) {
    try {
      const formData = new FormData();
      formData.append("class", record.class_name);
      formData.append("time_slot", record.time_slot);
      formData.append("date", record.date);
      for (const [sid, status] of Object.entries(record.statuses)) {
        formData.append(`status_${sid}`, status);
      }

      const res = await fetch("/teacher-mark-attendance", {
        method: "POST",
        body: formData,
      });

      if (res.ok || res.redirected) {
        await deletePending(db, record.id);
        synced++;
        console.log(`[SW] Synced record id=${record.id}`);
      }
    } catch (err) {
      console.warn(`[SW] Failed to sync record id=${record.id}:`, err);
    }
  }

  // Notify all open clients
  const clients = await self.clients.matchAll();
  clients.forEach((client) =>
    client.postMessage({
      type: "SYNC_COMPLETE",
      synced,
      total: pending.length,
    })
  );
}

// ─── INDEXEDDB HELPERS ──────────────────────────────────────
function openIDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("AttendanceOfflineDB", 1);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains("pending")) {
        const store = db.createObjectStore("pending", {
          keyPath: "id",
          autoIncrement: true,
        });
        store.createIndex("synced", "synced", { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function getAllPending(db) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("pending", "readonly");
    const req = tx.objectStore("pending").getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function deletePending(db, id) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("pending", "readwrite");
    const req = tx.objectStore("pending").delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}
