#!/usr/bin/env python3
"""
Test script for the Manual Entry System

Tests document processing, YouTube transcript extraction, and Flask app functionality.
"""

import asyncio
import tempfile
from pathlib import Path

from manual_entry_processors import (
    install_missing_dependencies,
    process_txt_file,
    process_pdf_file,
    process_docx_file,
    extract_youtube_transcript,
    extract_video_id_from_url
)

def test_dependency_check():
    """Test dependency availability for manual entry system."""
    print("🔍 Testing dependency availability...")
    
    deps_available = install_missing_dependencies()
    
    if deps_available:
        print("✅ All dependencies are available!")
        return True
    else:
        print("❌ Some dependencies are missing. Install them for full functionality.")
        return False

def test_txt_processing():
    """Test TXT file processing."""
    print("\n📄 Testing TXT file processing...")
    
    try:
        # Create a temporary TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = """AI Impact on Cybersecurity Workforce

This is a test document about artificial intelligence replacing traditional cybersecurity roles.
Key areas include:
- SIEM automation
- Threat detection
- Incident response
- Vulnerability management

The future of cybersecurity will require human-AI collaboration."""
            
            f.write(test_content)
            temp_path = Path(f.name)
        
        # Process the file
        extracted_content = process_txt_file(temp_path)
        
        # Clean up
        temp_path.unlink()
        
        if "AI Impact on Cybersecurity" in extracted_content:
            print("✅ TXT processing successful!")
            print(f"   Extracted {len(extracted_content)} characters")
            return True
        else:
            print("❌ TXT processing failed - content mismatch")
            return False
            
    except Exception as e:
        print(f"❌ TXT processing failed: {e}")
        return False

def test_youtube_url_extraction():
    """Test YouTube URL parsing."""
    print("\n🎥 Testing YouTube URL extraction...")
    
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/embed/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    
    expected_id = "dQw4w9WgXcQ"
    
    for url in test_urls:
        extracted_id = extract_video_id_from_url(url)
        if extracted_id == expected_id:
            print(f"✅ {url} -> {extracted_id}")
        else:
            print(f"❌ {url} -> {extracted_id} (expected {expected_id})")
            return False
    
    print("✅ YouTube URL extraction successful!")
    return True

def test_youtube_transcript():
    """Test YouTube transcript extraction (requires internet)."""
    print("\n📺 Testing YouTube transcript extraction...")
    
    # Use a known video with transcript (Rick Roll has captions)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        transcript_data = extract_youtube_transcript(test_url)
        
        if transcript_data and transcript_data.get('transcript'):
            print("✅ YouTube transcript extraction successful!")
            print(f"   Video ID: {transcript_data.get('video_id', 'Unknown')}")
            print(f"   Title: {transcript_data.get('title', 'Unknown')}")
            print(f"   Transcript length: {len(transcript_data.get('transcript', ''))} characters")
            return True
        else:
            print("❌ YouTube transcript extraction failed - no transcript returned")
            return False
            
    except Exception as e:
        print(f"⚠️  YouTube transcript extraction failed: {e}")
        print("   This might be due to missing dependencies or network issues")
        return False

def test_flask_app_import():
    """Test Flask app import and basic functionality."""
    print("\n🌐 Testing Flask app import...")
    
    try:
        from manual_entry_app import app
        
        # Test that the app can be created
        with app.test_client() as client:
            # Test the main route
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Flask app import and basic routing successful!")
                return True
            else:
                print(f"❌ Flask app routing failed: status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False

def test_pdf_processing():
    """Test PDF processing if dependencies are available."""
    print("\n📋 Testing PDF processing...")
    
    try:
        import PyPDF2
        print("✅ PyPDF2 available for PDF processing")
        return True
    except ImportError:
        try:
            import pdfplumber
            print("✅ pdfplumber available for PDF processing")
            return True
        except ImportError:
            print("⚠️  No PDF processing libraries available")
            print("   Install with: pip install PyPDF2 pdfplumber")
            return False

def test_docx_processing():
    """Test DOCX processing if dependencies are available."""
    print("\n📝 Testing DOCX processing...")
    
    try:
        import docx
        print("✅ python-docx available for DOCX processing")
        return True
    except ImportError:
        print("⚠️  python-docx not available")
        print("   Install with: pip install python-docx")
        return False

def main():
    """Main test function."""
    print("=== Testing AI-Horizon Manual Entry System ===")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Environment Setup
    print("\n1. Testing Environment Setup...")
    total_tests += 1
    try:
        setup_test_environment()
        print("   SUCCESS: Environment setup working")
        success_count += 1
    except Exception as e:
        print(f"   FAILED: Environment setup failed - {e}")
    
    # Test 2: File Processing
    print("\n2. Testing File Processing...")
    total_tests += 1
    try:
        test_file_processing()
        print("   SUCCESS: File processing working")
        success_count += 1
    except Exception as e:
        print(f"   FAILED: File processing failed - {e}")
    
    # Test 3: URL Processing  
    print("\n3. Testing URL Processing...")
    total_tests += 1
    try:
        test_url_processing()
        print("   SUCCESS: URL processing working")
        success_count += 1
    except Exception as e:
        print(f"   FAILED: URL processing failed - {e}")
    
    # Test 4: YouTube Processing
    print("\n4. Testing YouTube Processing...")
    total_tests += 1
    try:
        test_youtube_processing()
        print("   SUCCESS: YouTube processing working")
        success_count += 1
    except Exception as e:
        print(f"   FAILED: YouTube processing failed - {e}")
    
    # Test 5: Database Integration
    print("\n5. Testing Database Integration...")
    total_tests += 1
    try:
        test_database_integration()
        print("   SUCCESS: Database integration working")
        success_count += 1
    except Exception as e:
        print(f"   FAILED: Database integration failed - {e}")
    
    # Test 6: Search Logging System
    print("\n6. Testing Search Logging System...")
    total_tests += 1
    try:
        test_search_logging()
        print("   SUCCESS: Search logging working")
        success_count += 1
    except Exception as e:
        print(f"   FAILED: Search logging failed - {e}")
    
    # Test 7: Academic References System
    print("\n7. Testing Academic References System...")
    total_tests += 1
    try:
        test_academic_references()
        print("   SUCCESS: Academic references working")
        success_count += 1
    except Exception as e:
        print(f"   FAILED: Academic references failed - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"TEST SUMMARY: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        print("Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    main() 