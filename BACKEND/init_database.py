from app import app, db
from modules import User, EnergyEntry, WaterEntry, Notification
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        print("Creating sample users...")
        
        # Create sample users for different categories with custom limits
        users = [
            User(
                username="john_doe",
                email="john@example.com",
                password=generate_password_hash("password123"),
                phone_number="+265991234567",
                user_category="single",
                family_members=1,
                custom_energy_limit=80,  # Custom limit below default
                custom_water_limit=4000  # Custom limit below default
            ),
            User(
                username="family_banda", 
                email="banda@example.com",
                password=generate_password_hash("password123"),
                phone_number="+265992345678",
                user_category="family",
                family_members=4,
                custom_energy_limit=0,  # Use default limit
                custom_water_limit=0    # Use default limit
            ),
            User(
                username="hostel_mgr",
                email="hostel@example.com", 
                password=generate_password_hash("password123"),
                phone_number="+265993456789",
                user_category="hostel",
                custom_energy_limit=1200,  # Custom limit above default
                custom_water_limit=0       # Use default limit
            ),
            User(
                username="custom_user",
                email="custom@example.com",
                password=generate_password_hash("password123"),
                user_category="single",
                custom_energy_limit=50,   # Very low custom limit
                custom_water_limit=2000   # Very low custom limit
            )
        ]
        
        for user in users:
            db.session.add(user)
        db.session.commit()
        
        print("Database initialized successfully!")
        print("Sample users created:")
        print("   - john_doe (Single User) - Custom limits: 80 kWh, 4000 L")
        print("   - family_banda (Family of 4) - Using default limits")
        print("   - hostel_mgr (Hostel) - Custom energy limit: 1200 kWh")
        print("   - custom_user (Single) - Very low limits: 50 kWh, 2000 L")
        print("   All passwords: password123")
        
        # Add sample energy and water entries for testing reports and charts
from app import app, db
from modules import User, EnergyEntry, WaterEntry, Notification
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        print("Creating sample users...")
        
        # Create sample users for different categories with custom limits
        users = [
            User(
                username="john_doe",
                email="john@example.com",
                password=generate_password_hash("password123"),
                phone_number="+265991234567",
                user_category="single",
                family_members=1,
                custom_energy_limit=80,  # Custom limit below default
                custom_water_limit=4000  # Custom limit below default
            ),
            User(
                username="family_banda", 
                email="banda@example.com",
                password=generate_password_hash("password123"),
                phone_number="+265992345678",
                user_category="family",
                family_members=4,
                custom_energy_limit=0,  # Use default limit
                custom_water_limit=0    # Use default limit
            ),
            User(
                username="hostel_mgr",
                email="hostel@example.com", 
                password=generate_password_hash("password123"),
                phone_number="+265993456789",
                user_category="hostel",
                custom_energy_limit=1200,  # Custom limit above default
                custom_water_limit=0       # Use default limit
            ),
            User(
                username="custom_user",
                email="custom@example.com",
                password=generate_password_hash("password123"),
                user_category="single",
                custom_energy_limit=50,   # Very low custom limit
                custom_water_limit=2000   # Very low custom limit
            ),
            User(
                username="admin",
                email="admin@sret.com",
                password=generate_password_hash("admin123"),
                user_category="single",
                is_admin=True
            )
        ]
        
        for user in users:
            db.session.add(user)
        db.session.commit()
        
        print("Database initialized successfully!")
        print("Sample users created:")
        print("   - john_doe (Single User) - Custom limits: 80 kWh, 4000 L")
        print("   - family_banda (Family of 4) - Using default limits")
        print("   - hostel_mgr (Hostel) - Custom energy limit: 1200 kWh")
        print("   - custom_user (Single) - Very low limits: 50 kWh, 2000 L")
        print("   - admin (Admin User) - Password: admin123")
        print("   All other passwords: password123")
        
        # Add sample energy and water entries for testing reports and charts
        print("\nAdding sample consumption data...")
        from modules import EnergyEntry, WaterEntry
        
        today = datetime.now()
        user1 = User.query.filter_by(username="john_doe").first()
        
        # Add last 10 days of data for john_doe
        for i in range(10, 0, -1):
            reading_date = today - timedelta(days=i)
            energy = EnergyEntry(
                user_id=user1.id,
                electricity_usage=2 + (i % 2), # Reduced to ~2-3 kWh per day (60-90/month)
                cost=150 + (i * 10),
                reading_date=reading_date
            )
            water = WaterEntry(
                user_id=user1.id,
                water_usage=100 + (i * 10), # Reduced to ~100-200 L per day (3000-6000/month)
                cost=250 + (i * 5),
                reading_date=reading_date
            )
            db.session.add(energy)
            db.session.add(water)
        
        db.session.commit()
        print("Sample entries created for reports and charts!")

        # Initialize Tariffs
        from modules import Tariff
        from utils.helpers import DEFAULT_ELECTRICITY_TARIFFS, DEFAULT_WATER_RATES
        
        print("\nInitializing Dynamic Tariffs...")
        # Energy Tariffs
        for category, rates in DEFAULT_ELECTRICITY_TARIFFS.items():
            if category in ['single', 'family']:
                tariff = Tariff(
                    resource_type='energy',
                    user_category=category,
                    tier_1_limit=50,
                    tier_1_rate=rates['first_50_kwh'],
                    tier_2_rate=rates['above_50_kwh'],
                    fixed_charge=rates['monthly_fixed'],
                    default_limit=rates['default_energy_limit']
                )
            else:
                 tariff = Tariff(
                    resource_type='energy',
                    user_category=category,
                    rate_per_unit=rates['rate'],
                    fixed_charge=rates['monthly_fixed'],
                    default_limit=rates['default_energy_limit']
                )
            db.session.add(tariff)
            
        # Water Tariffs
        for category, rate in DEFAULT_WATER_RATES.items():
            # Use defaults from helpers/ELECTRICITY_TARIFFS structure for limits as fallbacks or hardcode based on helpers
            # For simplicity, using values from original helpers.py structure for limits
            default_limits = DEFAULT_ELECTRICITY_TARIFFS[category]['default_water_limit']
            
            tariff = Tariff(
                resource_type='water',
                user_category=category,
                rate_per_unit=rate,
                default_limit=default_limits
            )
            db.session.add(tariff)
            
        db.session.commit()
        print("Tariff table populated with default values.")

if __name__ == "__main__":
    init_database()