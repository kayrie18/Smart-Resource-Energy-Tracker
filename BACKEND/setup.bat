@echo off
echo 🔧 SMART ENERGY TRACKER - AUTOMATIC SETUP
echo ==========================================

echo 📦 Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found!

echo 🗂️ Creating project structure...
if not exist "..\frontend" mkdir "..\frontend"

echo 📥 Installing dependencies...
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install flask==2.3.3 flask-cors==4.0.0 flask-sqlalchemy==3.0.5 python-dotenv==1.0.0 werkzeug==2.3.7

echo 📄 Creating required files...

:: Create requirements.txt
echo Flask==2.3.3 > requirements.txt
echo Flask-CORS==4.0.0 >> requirements.txt
echo Flask-SQLAlchemy==3.0.5 >> requirements.txt
echo python-dotenv==1.0.0 >> requirements.txt
echo Werkzeug==2.3.7 >> requirements.txt

:: Create database.py
echo from flask_sqlalchemy import SQLAlchemy > database.py
echo. >> database.py
echo db = SQLAlchemy() >> database.py

:: Create config.py
echo import os > config.py
echo. >> config.py
echo class Config: >> config.py
echo     SECRET_KEY = 'smart-energy-tracker-secret-key-2024' >> config.py
echo     SQLALCHEMY_DATABASE_URI = 'sqlite:///energy_tracker.db' >> config.py
echo     SQLALCHEMY_TRACK_MODIFICATIONS = False >> config.py

:: Create models.py
echo from database import db > models.py
echo from datetime import datetime >> models.py
echo. >> models.py
echo class User(db.Model): >> models.py
echo     id = db.Column(db.Integer, primary_key=True) >> models.py
echo     username = db.Column(db.String(80), unique=True, nullable=False) >> models.py
echo     email = db.Column(db.String(120), unique=True, nullable=False) >> models.py
echo     password = db.Column(db.String(200), nullable=False) >> models.py
echo     created_at = db.Column(db.DateTime, default=datetime.utcnow) >> models.py
echo. >> models.py
echo class EnergyEntry(db.Model): >> models.py
echo     id = db.Column(db.Integer, primary_key=True) >> models.py
echo     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) >> models.py
echo     electricity_usage = db.Column(db.Float, nullable=False) >> models.py
echo     cost = db.Column(db.Float, nullable=False) >> models.py
echo     reading_date = db.Column(db.DateTime, nullable=False) >> models.py
echo     created_at = db.Column(db.DateTime, default=datetime.utcnow) >> models.py
echo. >> models.py
echo     def to_dict(self): >> models.py
echo         return { >> models.py
echo             'id': self.id, >> models.py
echo             'electricity_usage': self.electricity_usage, >> models.py
echo             'cost': self.cost, >> models.py
echo             'reading_date': self.reading_date.isoformat(), >> models.py
echo             'created_at': self.created_at.isoformat() >> models.py
echo         } >> models.py
echo. >> models.py
echo class WaterEntry(db.Model): >> models.py
echo     id = db.Column(db.Integer, primary_key=True) >> models.py
echo     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) >> models.py
echo     water_usage = db.Column(db.Float, nullable=False) >> models.py
echo     cost = db.Column(db.Float, nullable=False) >> models.py
echo     reading_date = db.Column(db.DateTime, nullable=False) >> models.py
echo     created_at = db.Column(db.DateTime, default=datetime.utcnow) >> models.py
echo. >> models.py
echo     def to_dict(self): >> models.py
echo         return { >> models.py
echo             'id': self.id, >> models.py
echo             'water_usage': self.water_usage, >> models.py
echo             'cost': self.cost, >> models.py
echo             'reading_date': self.reading_date.isoformat(), >> models.py
echo             'created_at': self.created_at.isoformat() >> models.py
echo         } >> models.py
echo. >> models.py
echo class Notification(db.Model): >> models.py
echo     id = db.Column(db.Integer, primary_key=True) >> models.py
echo     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) >> models.py
echo     message = db.Column(db.String(500), nullable=False) >> models.py
echo     type = db.Column(db.String(50), nullable=False) >> models.py
echo     is_read = db.Column(db.Boolean, default=False) >> models.py
echo     created_at = db.Column(db.DateTime, default=datetime.utcnow) >> models.py

:: Create app.py
echo from flask import Flask, request, jsonify > app.py
echo from flask_cors import CORS >> app.py
echo from database import db >> app.py
echo from models import User, EnergyEntry, WaterEntry, Notification >> app.py
echo from config import Config >> app.py
echo from datetime import datetime, timedelta >> app.py
echo. >> app.py
echo app = Flask(__name__) >> app.py
echo app.config.from_object(Config) >> app.py
echo CORS(app) >> app.py
echo db.init_app(app) >> app.py
echo. >> app.py
echo with app.app_context(): >> app.py
echo     db.create_all() >> app.py
echo. >> app.py
echo @app.route('/') >> app.py
echo def home(): >> app.py
echo     return jsonify({'message': 'Smart Energy Tracker API is running!'}) >> app.py
echo. >> app.py
echo @app.route('/api/register', methods=['POST']) >> app.py
echo def register(): >> app.py
echo     data = request.get_json() >> app.py
echo     user = User(username=data['username'], email=data['email'], password=data['password']) >> app.py
echo     db.session.add(user) >> app.py
echo     db.session.commit() >> app.py
echo     return jsonify({'message': 'User created', 'user_id': user.id}) >> app.py
echo. >> app.py
echo @app.route('/api/login', methods=['POST']) >> app.py
echo def login(): >> app.py
echo     data = request.get_json() >> app.py
echo     user = User.query.filter_by(username=data['username'], password=data['password']).first() >> app.py
echo     if user: >> app.py
echo         return jsonify({'message': 'Login successful', 'user_id': user.id}) >> app.py
echo     return jsonify({'error': 'Invalid credentials'}), 401 >> app.py
echo. >> app.py
echo if __name__ == '__main__': >> app.py
echo     print("🚀 Server starting on http://localhost:5000") >> app.py
echo     app.run(debug=True, port=5000) >> app.py

echo 📁 Creating frontend files...

:: Create frontend/index.html
echo ^<!DOCTYPE html^> > ..\frontend\index.html
echo ^<html lang="en"^> >> ..\frontend\index.html
echo ^<head^> >> ..\frontend\index.html
echo     ^<meta charset="UTF-8"^> >> ..\frontend\index.html
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0"^> >> ..\frontend\index.html
echo     ^<title^>Smart Energy Tracker^</title^> >> ..\frontend\index.html
echo     ^<style^> >> ..\frontend\index.html
echo         body { font-family: Arial, sans-serif; margin: 40px; background: #f0f2f5; } >> ..\frontend\index.html
echo         .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } >> ..\frontend\index.html
echo         h1 { color: #2c3e50; text-align: center; } >> ..\frontend\index.html
echo         .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; } >> ..\frontend\index.html
echo         .btn:hover { background: #2980b9; } >> ..\frontend\index.html
echo     ^</style^> >> ..\frontend\index.html
echo ^</head^> >> ..\frontend\index.html
echo ^<body^> >> ..\frontend\index.html
echo     ^<div class="container"^> >> ..\frontend\index.html
echo         ^<h1^>⚡ Smart Energy ^& Resource Tracker^</h1^> >> ..\frontend\index.html
echo         ^<p^>Backend setup complete! The API is ready to use.^</p^> >> ..\frontend\index.html
echo         ^<button class="btn" onclick="testAPI()"^>Test API Connection^</button^> >> ..\frontend\index.html
echo         ^<div id="result"^>^</div^> >> ..\frontend\index.html
echo     ^</div^> >> ..\frontend\index.html
echo     ^<script^> >> ..\frontend\index.html
echo         async function testAPI() { >> ..\frontend\index.html
echo             try { >> ..\frontend\index.html
echo                 const response = await fetch('http://localhost:5000/'); >> ..\frontend\index.html
echo                 const data = await response.json(); >> ..\frontend\index.html
echo                 document.getElementById('result').innerHTML = '✅ API Response: ' + JSON.stringify(data); >> ..\frontend\index.html
echo             } catch (error) { >> ..\frontend\index.html
echo                 document.getElementById('result').innerHTML = '❌ Error: ' + error; >> ..\frontend\index.html
echo             } >> ..\frontend\index.html
echo         } >> ..\frontend\index.html
echo     ^</script^> >> ..\frontend\index.html
echo ^</body^> >> ..\frontend\index.html
echo ^</html^> >> ..\frontend\index.html

echo.
echo ✅ SETUP COMPLETE!
echo.
echo 🎯 WHAT TO DO NEXT:
echo 1. Backend is ready! Run: python app.py
echo 2. Open frontend/index.html in your browser
echo 3. Test the connection by clicking "Test API Connection"
echo.
echo 📍 Your API will run on: http://localhost:5000
echo.

pause