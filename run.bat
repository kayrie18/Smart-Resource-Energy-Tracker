@echo off
echo 🚀 SMART ENERGY TRACKER - COMPLETE SETUP & RUN
echo ==============================================

echo 🔧 Starting Backend Server...
cd backend
start cmd /k "python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python init_database.py && python app.py"

echo ⏳ Waiting for backend to start...
timeout /t 5

echo 🌐 Starting Frontend Server...
cd ..\frontend
start cmd /k "python -m http.server 8000"

echo ⏳ Waiting for frontend to start...
timeout /t 3

echo ✅ SETUP COMPLETE!
echo.
echo 🎯 ACCESS YOUR APPLICATION:
echo    Frontend: http://localhost:8000
echo    Backend API: http://localhost:5000
echo.
echo 👤 SAMPLE LOGINS:
echo    Username: john_doe, Password: password123 (Single User)
echo    Username: family_banda, Password: password123 (Family of 4)
echo    Username: hostel_mgr, Password: password123 (Hostel)
echo.
pause