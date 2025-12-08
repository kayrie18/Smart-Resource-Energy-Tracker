from app import app
from modules import User
from werkzeug.security import check_password_hash

with app.app_context():
    user = User.query.filter_by(username='john_doe').first()
    if user:
        print(f"User found: {user.username}")
        print(f"Password hash: {user.password}")
        is_valid = check_password_hash(user.password, 'password123')
        print(f"Password 'password123' valid? {is_valid}")
    else:
        print("User 'john_doe' not found")
