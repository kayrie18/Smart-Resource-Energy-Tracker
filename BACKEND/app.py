from flask import Flask, send_from_directory
from flask_cors import CORS
from database import db
from config import Config
from routes.auth import auth_bp
from routes.entries import entries_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(entries_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')

# Serve Frontend Files
@app.route('/')
def serve_frontend():
    """Serve the main index.html file"""
    return send_from_directory('../FRONTEND', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images, etc.)"""
    return send_from_directory('../FRONTEND', path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)