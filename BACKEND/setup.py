import os
import subprocess
import sys

def setup_project():
    print("🔧 Setting up Smart Energy Tracker...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = os.path.join("venv", "Scripts", "pip")
        python_path = os.path.join("venv", "Scripts", "python")
    else:  # Linux/Mac
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    
    # Install requirements
    print("📥 Installing dependencies...")
    subprocess.run([pip_path, "install", "-r", "requirements.txt"])
    
    print("✅ Setup complete!")
    print("\n🎯 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Run the application:")
    print("   python app.py")
    print("3. Open frontend in browser:")
    print("   Open frontend/index.html")

if __name__ == "__main__":
    setup_project()