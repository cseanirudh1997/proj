#!/usr/bin/env python3
"""
Setup Script for Restaurant Invigilation System
"""

import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    print("Creating necessary directories...")
    
    directories = [
        "data",
        "logs",
        "models",
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def download_models():
    """Download YOLO models"""
    print("Setting up detection models...")
    
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    try:
        # This would download YOLO models in a real implementation
        print("✅ YOLOv8 will be downloaded automatically on first run")
        print("✅ MediaPipe models will be downloaded automatically")
    except Exception as e:
        print(f"⚠️  Model setup info: {e}")

def setup_database():
    """Initialize database"""
    print("Setting up database...")
    
    try:
        # Import database manager and initialize
        sys.path.append('src')
        from database.db_manager import DatabaseManager
        
        db_config = {"path": "data/restaurant_analytics.db"}
        db_manager = DatabaseManager(db_config)
        db_manager.initialize_database()
        
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"⚠️  Database will be initialized on first run: {e}")

def main():
    """Main setup function"""
    print("=" * 60)
    print("Restaurant Invigilation System - Setup")
    print("=" * 60)
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed during requirements installation")
        return
    
    # Create directories
    create_directories()
    
    # Download models
    download_models()
    
    # Setup database
    setup_database()
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Configure your camera settings in config/config.json")
    print("2. Run 'python demo.py' to see the dashboard with sample data")
    print("3. Run 'python main.py' to start the full system")
    print("4. Access the dashboard at http://localhost:8501")
    print("\nFor camera setup:")
    print("- Update RTSP URLs in config/config.json")
    print("- Or use USB camera indices (0, 1, 2, 3)")
    print("- Adjust detection zones as needed")

if __name__ == "__main__":
    main()