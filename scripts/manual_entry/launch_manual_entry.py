#!/usr/bin/env python3
"""
AI-Horizon Manual Entry System Launcher

Comprehensive launcher for the enhanced manual entry system with academic logging,
prompt management, and integration with the AI-Horizon pipeline.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        ('flask', 'Flask'),
        ('PyPDF2', 'PyPDF2'), 
        ('pdfplumber', 'pdfplumber'),
        ('docx', 'python-docx'),
        ('youtube_transcript_api', 'youtube-transcript-api'),
        ('yt_dlp', 'yt-dlp')
    ]
    
    missing = []
    
    for package, pip_name in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {pip_name}")
        except ImportError:
            print(f"  ❌ {pip_name} (missing)")
            missing.append(pip_name)
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} dependencies:")
        for package in missing:
            print(f"    • {package}")
        
        print(f"\n📦 Install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        
        response = input("\nWould you like to install them now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
                print("✅ Dependencies installed successfully!")
            except subprocess.CalledProcessError:
                print("❌ Failed to install dependencies. Please install manually.")
                return False
        else:
            print("⚠️  Some features may not work without these dependencies.")
    
    return True

def setup_environment():
    """Set up the environment for the manual entry system."""
    print("\n🔧 Setting up environment...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    manual_entry_dir = project_root / "manual_entry"
    
    if not manual_entry_dir.exists():
        print("❌ Manual entry directory not found!")
        print("   Expected location: manual_entry/")
        print("   Please ensure the manual entry files are properly organized.")
        return False
    
    # Check for required files
    required_files = [
        "manual_entry_app.py",
        "manual_entry_processors.py",
        "templates/base.html",
        "templates/index.html",
        "templates/manage_prompts.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (manual_entry_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"    • manual_entry/{file_path}")
        return False
    
    # Ensure data directories exist
    data_dirs = [
        project_root / "data" / "uploads",
        project_root / "data" / "logs" / "searches",
        project_root / "logs"
    ]
    
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")
    
    print("  ✅ Environment setup complete!")
    return True

def run_tests():
    """Run the manual entry system tests."""
    print("\n🧪 Running system tests...")
    
    manual_entry_dir = Path(__file__).parent / "manual_entry"
    test_file = manual_entry_dir / "test_manual_entry.py"
    
    if not test_file.exists():
        print("⚠️  Test file not found, skipping tests.")
        return True
    
    try:
        # Change to manual_entry directory and run tests
        os.chdir(manual_entry_dir)
        result = subprocess.run([sys.executable, "test_manual_entry.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            
            response = input("Continue anyway? (y/n): ")
            return response.lower() in ['y', 'yes']
    except Exception as e:
        print(f"⚠️  Could not run tests: {e}")
        return True
    finally:
        # Change back to project root
        os.chdir(Path(__file__).parent)

def start_manual_entry_system():
    """Start the manual entry Flask application."""
    print("\n🚀 Starting AI-Horizon Manual Entry System...")
    print("=" * 60)
    
    manual_entry_dir = Path(__file__).parent / "manual_entry"
    app_file = manual_entry_dir / "manual_entry_app.py"
    
    if not app_file.exists():
        print("❌ Manual entry app not found!")
        return False
    
    try:
        # Change to manual_entry directory
        os.chdir(manual_entry_dir)
        
        print("🌐 Starting Flask application...")
        print("   URL: http://localhost:5000")
        print("   Features:")
        print("     • Manual URL entry with duplicate detection")
        print("     • File upload (PDF, TXT, DOCX) with text extraction")
        print("     • YouTube transcript processing")
        print("     • Search prompts management interface")
        print("     • Comprehensive logging and academic citations")
        print("\n⚠️  Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Run the Flask app
        subprocess.run([sys.executable, "manual_entry_app.py"])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        return False
    finally:
        # Change back to project root
        os.chdir(Path(__file__).parent)
    
    return True

def show_launch_options():
    """Show available launch options."""
    print("🎯 AI-Horizon Manual Entry System")
    print("=" * 50)
    print("Choose an option:")
    print("  1. Full system check and launch")
    print("  2. Quick launch (skip tests)")
    print("  3. Run tests only")
    print("  4. Check dependencies only")
    print("  5. Show system information")
    print("  0. Exit")
    print()
    
    choice = input("Enter your choice (0-5): ").strip()
    return choice

def show_system_info():
    """Display system information and status."""
    print("\n📊 AI-Horizon Manual Entry System Information")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    manual_entry_dir = project_root / "manual_entry"
    
    print(f"Project Root: {project_root}")
    print(f"Manual Entry: {manual_entry_dir}")
    print(f"Manual Entry Exists: {'✅' if manual_entry_dir.exists() else '❌'}")
    
    # Check key files
    key_files = [
        ("Flask App", "manual_entry/manual_entry_app.py"),
        ("Processors", "manual_entry/manual_entry_processors.py"),
        ("Test Suite", "manual_entry/test_manual_entry.py"),
        ("Base Template", "manual_entry/templates/base.html"),
        ("Prompts Manager", "manual_entry/templates/manage_prompts.html"),
        ("Academic References", "aih/utils/academic_references.py"),
        ("Search Logger", "aih/utils/search_logger.py"),
    ]
    
    print("\n📁 File Status:")
    for name, path in key_files:
        file_path = project_root / path
        status = "✅" if file_path.exists() else "❌"
        print(f"  {status} {name}: {path}")
    
    # Check data directories
    data_dirs = [
        ("Database", "data/aih_database.db"),
        ("Upload Folder", "data/uploads/"),
        ("Search Logs", "data/logs/searches/"),
        ("Reports", "data/reports/"),
    ]
    
    print("\n📂 Data Directories:")
    for name, path in data_dirs:
        dir_path = project_root / path
        if path.endswith('/'):
            status = "✅" if dir_path.exists() else "❌"
            print(f"  {status} {name}: {path}")
        else:
            status = "✅" if dir_path.exists() else "❌"
            print(f"  {status} {name}: {path}")
    
    # Check dependencies
    print("\n📦 Dependencies:")
    packages = ['flask', 'PyPDF2', 'pdfplumber', 'docx', 'youtube_transcript_api', 'yt_dlp']
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")

def main():
    """Main launcher function."""
    while True:
        choice = show_launch_options()
        
        if choice == "1":
            # Full system check and launch
            if check_dependencies() and setup_environment():
                if run_tests():
                    start_manual_entry_system()
            break
            
        elif choice == "2":
            # Quick launch
            if check_dependencies() and setup_environment():
                start_manual_entry_system()
            break
            
        elif choice == "3":
            # Run tests only
            if setup_environment():
                run_tests()
            
        elif choice == "4":
            # Check dependencies only
            check_dependencies()
            
        elif choice == "5":
            # Show system information
            show_system_info()
            
        elif choice == "0":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please try again.")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    main() 