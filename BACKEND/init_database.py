from app import app, db
from modules import User, EnergyEntry, WaterEntry, Notification
from datetime import datetime, timedelta

def init_database():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        print("🗃️ Creating sample users...")
        
        # Create sample users for different categories with custom limits
        users = [
            User(
                username="john_doe",
                email="john@example.com",
                password="password123",
                phone_number="+265991234567",
                user_category="single",
                family_members=1,
                custom_energy_limit=80,  # Custom limit below default
                custom_water_limit=4000  # Custom limit below default
            ),
            User(
                username="family_banda", 
                email="banda@example.com",
                password="password123",
                phone_number="+265992345678",
                user_category="family",
                family_members=4,
                custom_energy_limit=0,  # Use default limit
                custom_water_limit=0    # Use default limit
            ),
            User(
                username="hostel_mgr",
                email="hostel@example.com", 
                password="password123",
                phone_number="+265993456789",
                user_category="hostel",
                custom_energy_limit=1200,  # Custom limit above default
                custom_water_limit=0       # Use default limit
            ),
            User(
                username="custom_user",
                email="custom@example.com",
                password="password123",
                user_category="single",
                custom_energy_limit=50,   # Very low custom limit
                custom_water_limit=2000   # Very low custom limit
            )
        ]
        
        for user in users:
            db.session.add(user)
        db.session.commit()
        
        print("✅ Database initialized successfully!")
        print("👤 Sample users created:")
        print("   - john_doe (Single User) - Custom limits: 80 kWh, 4000 L")
        print("   - family_banda (Family of 4) - Using default limits")
        print("   - hostel_mgr (Hostel) - Custom energy limit: 1200 kWh")
        print("   - custom_user (Single) - Very low limits: 50 kWh, 2000 L")
        print("   All passwords: password123")
        
        # Add sample energy and water entries for testing reports and charts
        print("\n📊 Adding sample consumption data...")
        from modules import EnergyEntry, WaterEntry
        
        today = datetime.now()
        user1 = User.query.filter_by(username="john_doe").first()
        
        # Add last 10 days of data for john_doe
        for i in range(10, 0, -1):
            reading_date = today - timedelta(days=i)
            energy = EnergyEntry(
                user_id=user1.id,
                electricity_usage=15 + (i % 5),
                cost=1200 + (i * 50),
                reading_date=reading_date
            )
            water = WaterEntry(
                user_id=user1.id,
                water_usage=800 + (i * 20),
                cost=2000 + (i * 30),
                reading_date=reading_date
            )
            db.session.add(energy)
            db.session.add(water)
        
        db.session.commit()
        print("✅ Sample entries created for reports and charts!")

if __name__ == "__main__":
    init_database()