======================================
  ATTENDANCE PORTAL — PWA (Offline)
  Built for Rural Schools
======================================

SETUP INSTRUCTIONS
------------------

1. Install Python (3.8 or above)
   Download from: https://www.python.org/downloads/

2. Install dependencies:
   Open terminal/cmd in this folder and run:
   
      pip install flask flask-cors

3. Initialize the database (first time only):
   
      python init_db.py

4. Run the app:
   
      python app.py

5. Open browser and go to:
   
      http://localhost:5000          → Admin Login
      http://localhost:5000/teacher  → Teacher Login

======================================
DEFAULT ADMIN LOGIN
  Username: shreedhar
  Password: shree123
======================================

PWA / OFFLINE SETUP
-------------------
- Open the teacher login page on the school device's browser
- Click "Add to Home Screen" (on Android/Chrome)
- App will work offline after first load!
- Add your school logo as:
    static/icons/icon-192.png  (192x192 px)
    static/icons/icon-512.png  (512x512 px)

======================================
