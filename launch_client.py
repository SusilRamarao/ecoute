#!/usr/bin/env python3
"""
Quick launcher for Ecoute Desktop Client
This script checks dependencies and launches the client application.
"""

import sys
import subprocess
import platform
import os

def check_python_version():
    """Check if Python version is 3.7+"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'tkinter',
        'socketio',
        'pyaudio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'socketio':
                import socketio
            elif package == 'pyaudio':
                import pyaudio
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    # Check for Windows-specific package
    if platform.system() == "Windows":
        try:
            import PyAudioWPatch
            print("✅ PyAudioWPatch (Windows system audio)")
        except ImportError:
            print("⚠️  PyAudioWPatch - Missing (recommended for Windows system audio)")
            missing_packages.append('PyAudioWPatch')
    
    return missing_packages

def install_dependencies(missing_packages):
    """Attempt to install missing dependencies"""
    print(f"\nAttempting to install missing packages: {', '.join(missing_packages)}")
    
    try:
        # Map package names to pip install names
        pip_packages = []
        for package in missing_packages:
            if package == 'socketio':
                pip_packages.append('python-socketio==5.8.0')
            elif package == 'pyaudio':
                pip_packages.append('pyaudio==0.2.11')
            elif package == 'PyAudioWPatch':
                pip_packages.append('PyAudioWPatch==0.2.12.14')
        
        if pip_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + pip_packages)
            print("✅ Dependencies installed successfully!")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("\nManual installation required:")
        print("pip install -r client_requirements.txt")
        return False
    
    return True

def launch_client():
    """Launch the main client application"""
    try:
        print("\n🚀 Launching Ecoute Desktop Client...")
        
        # Check if client_app.py exists
        if not os.path.exists('client_app.py'):
            print("❌ client_app.py not found in current directory!")
            print("Please make sure you're running this from the correct directory.")
            return False
        
        # Import and run the client
        import client_app
        client_app.EcouteClient().run()
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch client: {e}")
        return False

def main():
    """Main launcher function"""
    print("🎧 Ecoute Desktop Client Launcher")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        input("\nPress Enter to exit...")
        return
    
    print("\n📦 Checking dependencies...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        response = input("Would you like to install them automatically? (y/N): ").lower().strip()
        
        if response in ['y', 'yes']:
            if not install_dependencies(missing_packages):
                input("\nPress Enter to exit...")
                return
        else:
            print("\nPlease install the missing dependencies manually:")
            print("pip install -r client_requirements.txt")
            input("\nPress Enter to exit...")
            return
    
    print("\n✅ All dependencies satisfied!")
    
    # Launch the client
    if not launch_client():
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("\nPress Enter to exit...")