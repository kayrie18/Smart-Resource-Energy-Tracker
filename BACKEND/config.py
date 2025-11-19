import os

class Config:
    SECRET_KEY = 'smart-energy-tracker-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///energy_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False