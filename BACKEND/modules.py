from database import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15))  # For SMS notifications
    user_category = db.Column(db.String(50), default='single')  # single, family, hostel, company
    family_members = db.Column(db.Integer, default=1)  # For family category
    custom_energy_limit = db.Column(db.Float, default=0)  # 0 means use default, >0 means custom limit
    custom_water_limit = db.Column(db.Float, default=0)   # 0 means use default, >0 means custom limit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    energy_entries = db.relationship('EnergyEntry', backref='user', lazy=True)
    water_entries = db.relationship('WaterEntry', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class EnergyEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    electricity_usage = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    reading_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'electricity_usage': self.electricity_usage,
            'cost': self.cost,
            'reading_date': self.reading_date.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class WaterEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    water_usage = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    reading_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'water_usage': self.water_usage,
            'cost': self.cost,
            'reading_date': self.reading_date.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    sms_sent = db.Column(db.Boolean, default=False)  # Track SMS delivery
    created_at = db.Column(db.DateTime, default=datetime.utcnow)