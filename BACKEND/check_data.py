from app import app
from modules import User, EnergyEntry

with app.app_context():
    user = User.query.filter_by(username='john_doe').first()
    if user:
        print(f"Checking entries for {user.username} (ID: {user.id})")
        entries = EnergyEntry.query.filter_by(user_id=user.id).order_by(EnergyEntry.reading_date.desc()).limit(10).all()
        for e in entries:
            print(f"Date: {e.reading_date.date()}, Usage: {e.electricity_usage} kWh, Cost: {e.cost}")
    else:
        print("User john_doe not found")
