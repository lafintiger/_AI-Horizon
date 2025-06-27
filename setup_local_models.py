#!/usr/bin/env python3
"""
AI-Horizon Local Models Setup Script

Guides users through setting up local models (Perplexical + Ollama)
and validates the complete local stack configuration.
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, List

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step: str, status: str = ""):
    """Print a setup step."""
    if status:
        print(f"📋 {step} ... {status}")
    else:
        print(f"📋 {step}")

def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")

def print_warning(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")

def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}")

def check_docker():
    """Check if Docker is installed and running."""
    print_step("Checking Docker installation")
    
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker found: {result.stdout.strip()}")
            return True
        else:
            print_error("Docker command failed")
            return False
    except FileNotFoundError:
        print_error("Docker not found. Please install Docker first.")
        return False

def check_docker_compose():
    """Check if Docker Compose is available."""
    print_step("Checking Docker Compose")
    
    try:
        # Try docker compose (new syntax)
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker Compose found: {result.stdout.strip()}")
            return True
        
        # Try docker-compose (old syntax)
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker Compose found: {result.stdout.strip()}")
            return True
        
        print_error("Docker Compose not found")
        return False
        
    except FileNotFoundError:
        print_error("Docker Compose not available")
        return False

def setup_config_file():
    """Create local configuration file."""
    print_step("Setting up configuration file")
    
    config_file = Path("config.env")
    template_file = Path("config.env.local")
    
    if config_file.exists():
        print_warning("config.env already exists. Creating backup...")
        backup_file = Path("config.env.backup")
        config_file.rename(backup_file)
        print_success(f"Backup created: {backup_file}")
    
    if template_file.exists():
        # Copy template to config.env
        with open(template_file, 'r') as src, open(config_file, 'w') as dst:
            dst.write(src.read())
        print_success("Created config.env from template")
        return True
    else:
        print_error("Template file config.env.local not found")
        return False

def start_ollama():
    """Start Ollama service."""
    print_step("Starting Ollama service")
    
    try:
        # Check if Ollama is already running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_success("Ollama already running")
            return True
    except:
        pass
    
    try:
        # Try to start Ollama with Docker
        result = subprocess.run([
            'docker', 'run', '-d', 
            '--name', 'ollama',
            '-p', '11434:11434',
            '-v', 'ollama:/root/.ollama',
            'ollama/ollama'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Ollama container started")
            time.sleep(5)  # Wait for startup
            return True
        else:
            print_error(f"Failed to start Ollama: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error starting Ollama: {e}")
        return False

def download_models():
    """Download required Ollama models."""
    print_step("Downloading Ollama models")
    
    models = [
        "llama3.1:8b",
        "qwen2.5:14b", 
        "deepseek-r1:7b"
    ]
    
    for model in models:
        print_step(f"Downloading {model}")
        
        try:
            result = subprocess.run([
                'docker', 'exec', 'ollama', 
                'ollama', 'pull', model
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                print_success(f"Downloaded {model}")
            else:
                print_error(f"Failed to download {model}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print_error(f"Timeout downloading {model}")
            return False
        except Exception as e:
            print_error(f"Error downloading {model}: {e}")
            return False
    
    return True

def start_perplexical():
    """Start Perplexical service."""
    print_step("Starting Perplexical service")
    
    try:
        # Check if Perplexical is already running
        response = requests.get("http://localhost:3000/health", timeout=5)
        if response.status_code == 200:
            print_success("Perplexical already running")
            return True
    except:
        pass
    
    try:
        # Try to start Perplexical with Docker
        result = subprocess.run([
            'docker', 'run', '-d',
            '--name', 'perplexical',
            '-p', '3000:3000',
            'perplexical/perplexical:latest'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Perplexical container started")
            time.sleep(10)  # Wait for startup
            return True
        else:
            print_error(f"Failed to start Perplexical: {result.stderr}")
            print_warning("You may need to build or pull the Perplexical image manually")
            return False
            
    except Exception as e:
        print_error(f"Error starting Perplexical: {e}")
        return False

def test_local_stack():
    """Test the complete local stack."""
    print_step("Testing local model stack")
    
    # Test Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print_success(f"Ollama: {len(models)} models available")
        else:
            print_error("Ollama not responding correctly")
            return False
    except Exception as e:
        print_error(f"Ollama test failed: {e}")
        return False
    
    # Test Perplexical
    try:
        response = requests.get("http://localhost:3000/health", timeout=10)
        if response.status_code == 200:
            print_success("Perplexical: Service healthy")
        else:
            print_error("Perplexical not responding correctly")
            return False
    except Exception as e:
        print_error(f"Perplexical test failed: {e}")
        return False
    
    return True

def run_comprehensive_test():
    """Run the comprehensive test script."""
    print_step("Running comprehensive model tests")
    
    try:
        result = subprocess.run([sys.executable, 'test_local_models.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print_success("All model tests passed!")
            print("Test output:")
            print(result.stdout)
            return True
        else:
            print_error("Model tests failed")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print_error("Model tests timed out")
        return False
    except Exception as e:
        print_error(f"Error running tests: {e}")
        return False

def docker_compose_setup():
    """Set up using Docker Compose."""
    print_step("Setting up with Docker Compose")
    
    try:
        # Build and start services
        result = subprocess.run([
            'docker', 'compose', 'up', '-d', '--build'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Docker Compose services started")
            print("Waiting for services to initialize...")
            time.sleep(30)  # Wait for all services
            return True
        else:
            print_error(f"Docker Compose failed: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Docker Compose error: {e}")
        return False

def main():
    """Main setup function."""
    print_header("AI-Horizon Local Models Setup")
    
    print("This script will set up AI-Horizon with local models:")
    print("- Ollama (LLM processing)")
    print("- Perplexical (local search)")
    print("- Complete Docker containerization")
    
    # Ask user for setup preference
    print("\nSetup Options:")
    print("1. Docker Compose (recommended - complete stack)")
    print("2. Manual setup (individual services)")
    print("3. Test existing setup")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Docker Compose setup
        if not check_docker() or not check_docker_compose():
            print_error("Docker requirements not met")
            return False
        
        setup_config_file()
        
        if docker_compose_setup():
            print_success("Docker Compose setup complete!")
            time.sleep(5)
            if test_local_stack():
                print_success("🎉 Local model stack is ready!")
                print("\nNext steps:")
                print("1. Access AI-Horizon at http://localhost:5000")
                print("2. All models are running locally with zero API costs")
                print("3. Check logs with: docker compose logs")
                return True
        
        return False
    
    elif choice == "2":
        # Manual setup
        if not check_docker():
            return False
        
        setup_config_file()
        
        success = True
        success &= start_ollama()
        success &= download_models()
        success &= start_perplexical()
        
        if success and test_local_stack():
            print_success("🎉 Manual setup complete!")
            print("\nNext steps:")
            print("1. Start AI-Horizon: python status_server.py")
            print("2. Access at http://localhost:5000")
            return True
        
        return False
    
    elif choice == "3":
        # Test existing setup
        if test_local_stack():
            if run_comprehensive_test():
                print_success("🎉 Existing setup is working perfectly!")
                return True
        
        print_error("Setup issues detected. Try option 1 or 2 to fix.")
        return False
    
    else:
        print_error("Invalid choice")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 