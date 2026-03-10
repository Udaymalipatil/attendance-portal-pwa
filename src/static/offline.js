// ============================================================
// offline.js — PWA Client-Side Manager
// Handles: SW registration, IndexedDB, offline form submit,
//          auto sync, manual sync, online/offline UI banner
// ============================================================

const SYNC_TAG = "sync-attendance";
const DB_NAME = "AttendanceOfflineDB";
const DB_VERSION = 1;

// ─── SERVICE WORKER REGISTRATION ────────────────────────────
if ("serviceWorker" in navigator) {
  window.addEventListener("load", async () => {
    try {
      const reg = await navigator.serviceWorker.register("/sw.js");
      console.log("[PWA] Service Worker registered:", reg.scope);

      // Listen for messages from SW (sync complete)
      navigator.serviceWorker.addEventListener("message", (event) => {
        if (event.data.type === "SYNC_COMPLETE") {
          showBanner(
            `✅ Synced ${event.data.synced} of ${event.data.total} attendance records!`,
            "success"
          );
          updatePendingCount();
        }
      });
    } catch (err) {
      console.error("[PWA] SW registration failed:", err);
    }
  });
}

// ─── INDEXEDDB ───────────────────────────────────────────────
function openIDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
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

async function saveAttendanceOffline(data) {
  const db = await openIDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("pending", "readwrite");
    const req = tx.objectStore("pending").add({ ...data, savedAt: new Date().toISOString() });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function getPendingCount() {
  const db = await openIDB();
  return new Promise((resolve) => {
    const tx = db.transaction("pending", "readonly");
    const req = tx.objectStore("pending").count();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve(0);
  });
}

async function getAllPending() {
  const db = await openIDB();
  return new Promise((resolve) => {
    const tx = db.transaction("pending", "readonly");
    const req = tx.objectStore("pending").getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve([]);
  });
}

async function deletePending(id) {
  const db = await openIDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("pending", "readwrite");
    const req = tx.objectStore("pending").delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// ─── MANUAL SYNC ─────────────────────────────────────────────
async function manualSync() {
  const btn = document.getElementById("sync-btn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Syncing...";
  }

  if (!navigator.onLine) {
    showBanner("❌ No internet connection. Please try again later.", "error");
    if (btn) { btn.disabled = false; btn.textContent = "🔄 Sync Now"; }
    return;
  }

  const pending = await getAllPending();
  if (pending.length === 0) {
    showBanner("✅ Nothing to sync — you're all up to date!", "success");
    if (btn) { btn.disabled = false; btn.textContent = "🔄 Sync Now"; }
    return;
  }

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
        await deletePending(record.id);
        synced++;
      }
    } catch (err) {
      console.warn("[PWA] Failed to sync record:", err);
    }
  }

  showBanner(`✅ Synced ${synced} of ${pending.length} records successfully!`, "success");
  updatePendingCount();

  if (btn) { btn.disabled = false; btn.textContent = "🔄 Sync Now"; }
}

// ─── AUTO SYNC on reconnect ───────────────────────────────────
window.addEventListener("online", async () => {
  updateNetworkBanner();
  showBanner("🌐 Back online! Syncing pending records...", "info");

  // Try Background Sync API first
  if ("serviceWorker" in navigator && "SyncManager" in window) {
    const reg = await navigator.serviceWorker.ready;
    try {
      await reg.sync.register(SYNC_TAG);
      console.log("[PWA] Background sync registered");
    } catch (err) {
      console.warn("[PWA] Background sync failed, falling back to manual:", err);
      await manualSync();
    }
  } else {
    await manualSync();
  }
});

window.addEventListener("offline", () => {
  updateNetworkBanner();
});

// ─── UI HELPERS ──────────────────────────────────────────────
function updateNetworkBanner() {
  const banner = document.getElementById("network-banner");
  if (!banner) return;
  if (navigator.onLine) {
    banner.style.display = "none";
  } else {
    banner.style.display = "flex";
    banner.innerHTML = `
      <span>📡 You are offline — attendance will be saved locally and synced automatically.</span>
    `;
  }
}

function showBanner(message, type = "info") {
  let toast = document.getElementById("toast-banner");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast-banner";
    toast.style.cssText = `
      position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
      padding:12px 22px; border-radius:8px; font-size:14px; font-weight:600;
      z-index:9999; box-shadow:0 4px 15px rgba(0,0,0,0.2);
      transition: opacity 0.4s; max-width:90vw; text-align:center;
    `;
    document.body.appendChild(toast);
  }
  const colors = {
    success: { bg: "#dcfce7", color: "#166534" },
    error: { bg: "#fee2e2", color: "#991b1b" },
    info: { bg: "#dbeafe", color: "#1e40af" },
  };
  const c = colors[type] || colors.info;
  toast.style.background = c.bg;
  toast.style.color = c.color;
  toast.textContent = message;
  toast.style.opacity = "1";
  toast.style.display = "block";
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => { toast.style.opacity = "0"; }, 4000);
}

async function updatePendingCount() {
  const count = await getPendingCount();
  const badge = document.getElementById("pending-badge");
  if (!badge) return;
  if (count > 0) {
    badge.textContent = `${count} pending sync`;
    badge.style.display = "inline-block";
  } else {
    badge.style.display = "none";
  }
}

// ─── OFFLINE ATTENDANCE FORM HANDLER ─────────────────────────
// Called from teacher_attendance.html on form submit
async function submitAttendanceWithOffline(event, form) {
  event.preventDefault();

  const classVal = form.querySelector('[name="class"]').value;
  const timeSlot = form.querySelector('[name="time_slot"]').value;
  const dateVal = form.querySelector('[name="date"]').value;

  if (!dateVal) { showBanner("❌ Please select a date.", "error"); return; }

  const statuses = {};
  form.querySelectorAll('[name^="status_"]').forEach((sel) => {
    const sid = sel.name.replace("status_", "");
    statuses[sid] = sel.value;
  });

  if (navigator.onLine) {
    // Online: submit normally
    form.submit();
  } else {
    // Offline: save to IndexedDB
    try {
      await saveAttendanceOffline({
        class_name: classVal,
        time_slot: timeSlot,
        date: dateVal,
        statuses,
      });
      showBanner("💾 Saved offline! Will sync when internet is available.", "info");
      updatePendingCount();
      setTimeout(() => { window.location.href = "/teacher-dashboard"; }, 2000);
    } catch (err) {
      showBanner("❌ Failed to save offline. Please try again.", "error");
      console.error(err);
    }
  }
}

// ─── INIT ─────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  updateNetworkBanner();
  updatePendingCount();

  // Cache student list for offline use
  if (navigator.onLine && window.location.pathname.includes("teacher-attendance")) {
    caches.open("attendance-portal-v1").then((cache) => {
      cache.add(window.location.href);
    });
  }
});
