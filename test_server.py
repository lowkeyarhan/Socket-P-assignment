#!/usr/bin/env python3
"""
Test script for the Multi-threaded HTTP Server
Run various tests to verify server functionality
"""

import requests
import sys
import time
import os
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import subprocess

def test_basic_functionality():
    """Test basic server functionality"""
    print("🧪 Basic Functionality Tests")
    base_url = "http://localhost:8080"
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: HTML serving
    print("\n1. HTML File Serving:")
    try:
        response = requests.get(f"{base_url}/")
        total_tests += 1
        if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
            print("   ✅ Root path serves HTML correctly")
            tests_passed += 1
        else:
            print(f"   ❌ Root path failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Root path error: {e}")
        total_tests += 1
    
    # Test 2: Binary file download
    print("\n2. Binary File Download:")
    try:
        response = requests.get(f"{base_url}/sample.txt")
        total_tests += 1
        if response.status_code == 200 and 'octet-stream' in response.headers.get('Content-Type', ''):
            print("   ✅ Binary file download works")
            tests_passed += 1
        else:
            print(f"   ❌ Binary download failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Binary download error: {e}")
        total_tests += 1
    
    # Test 3: JSON POST
    print("\n3. JSON POST Request:")
    try:
        test_data = {"test": "data", "timestamp": "2024-10-05"}
        response = requests.post(f"{base_url}/upload", 
                               json=test_data,
                               headers={'Content-Type': 'application/json'})
        total_tests += 1
        if response.status_code == 201 and 'success' in response.text:
            print("   ✅ JSON POST works correctly")
            tests_passed += 1
        else:
            print(f"   ❌ JSON POST failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ JSON POST error: {e}")
        total_tests += 1
    
    # Test 4: 404 Error
    print("\n4. 404 Error Handling:")
    try:
        response = requests.get(f"{base_url}/nonexistent.html")
        total_tests += 1
        if response.status_code == 404:
            print("   ✅ 404 handling works correctly")
            tests_passed += 1
        else:
            print(f"   ❌ 404 handling failed: got {response.status_code}")
    except Exception as e:
        print(f"   ❌ 404 test error: {e}")
        total_tests += 1
    
    # Test 5: Unsupported method
    print("\n5. Method Validation:")
    try:
        response = requests.put(f"{base_url}/")
        total_tests += 1
        if response.status_code == 405:
            print("   ✅ Method validation works correctly")
            tests_passed += 1
        else:
            print(f"   ❌ Method validation failed: got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Method validation error: {e}")
        total_tests += 1
    
    print(f"\n📊 Basic Tests: {tests_passed}/{total_tests} passed")
    return tests_passed, total_tests

def test_security_features():
    """Test security features"""
    print("\n🔒 Security Tests")
    base_url = "http://localhost:8080"
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Path traversal protection
    print("\n1. Path Traversal Protection:")
    try:
        response = requests.get(f"{base_url}/../etc/passwd")
        total_tests += 1
        if response.status_code == 403:
            print("   ✅ Path traversal blocked correctly")
            tests_passed += 1
        else:
            print(f"   ❌ Path traversal not blocked: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Path traversal test error: {e}")
        total_tests += 1
    
    # Test 2: Invalid host header
    print("\n2. Host Header Validation:")
    try:
        response = requests.get(f"{base_url}/", headers={'Host': 'evil.com'})
        total_tests += 1
        if response.status_code == 403:
            print("   ✅ Invalid host header blocked")
            tests_passed += 1
        else:
            print(f"   ❌ Invalid host header not blocked: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Host header test error: {e}")
        total_tests += 1
    
    # Test 3: Unsupported media type
    print("\n3. Content-Type Validation:")
    try:
        response = requests.post(f"{base_url}/upload", 
                               data="not json",
                               headers={'Content-Type': 'text/plain'})
        total_tests += 1
        if response.status_code == 415:
            print("   ✅ Unsupported media type blocked")
            tests_passed += 1
        else:
            print(f"   ❌ Content-type validation failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Content-type test error: {e}")
        total_tests += 1
    
    print(f"\n📊 Security Tests: {tests_passed}/{total_tests} passed")
    return tests_passed, total_tests

def test_file_integrity():
    """Test file integrity for downloads"""
    print("\n📁 File Integrity Tests")
    base_url = "http://localhost:8080"
    
    tests_passed = 0
    total_tests = 0
    
    # Test small image integrity
    print("\n1. Small Image Integrity:")
    original_path = "resources/logo.png"
    if os.path.exists(original_path):
        try:
            with open(original_path, 'rb') as f:
                original_data = f.read()
            
            response = requests.get(f"{base_url}/logo.png")
            total_tests += 1
            
            if response.status_code == 200 and response.content == original_data:
                print(f"   ✅ Small image integrity verified ({len(original_data)} bytes)")
                tests_passed += 1
            else:
                print(f"   ❌ Small image integrity failed")
                print(f"     Original: {len(original_data)} bytes")
                print(f"     Downloaded: {len(response.content)} bytes")
        except Exception as e:
            print(f"   ❌ Small image test error: {e}")
            total_tests += 1
    
    # Test large image integrity
    print("\n2. Large Image Integrity:")
    original_path = "resources/large_image.png"
    if os.path.exists(original_path):
        try:
            with open(original_path, 'rb') as f:
                original_data = f.read()
            
            response = requests.get(f"{base_url}/large_image.png", timeout=30)
            total_tests += 1
            
            if response.status_code == 200 and response.content == original_data:
                print(f"   ✅ Large image integrity verified ({len(original_data)} bytes)")
                tests_passed += 1
            else:
                print(f"   ❌ Large image integrity failed")
                print(f"     Original: {len(original_data)} bytes")
                print(f"     Downloaded: {len(response.content)} bytes")
        except Exception as e:
            print(f"   ❌ Large image test error: {e}")
            total_tests += 1
    
    print(f"\n📊 Integrity Tests: {tests_passed}/{total_tests} passed")
    return tests_passed, total_tests

def test_concurrency():
    """Test concurrent requests"""
    print("\n🚀 Concurrency Tests")
    base_url = "http://localhost:8080"
    
    tests_passed = 0
    total_tests = 1
    
    print("\n1. Concurrent Downloads:")
    try:
        def download_file(url):
            try:
                response = requests.get(url, timeout=10)
                return response.status_code == 200
            except:
                return False
        
        # Test concurrent downloads
        urls = [f"{base_url}/sample.txt" for _ in range(10)]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(download_file, urls))
        
        successful = sum(results)
        
        if successful >= 8:  # Allow for some timing issues
            print(f"   ✅ Concurrent downloads: {successful}/10 successful")
            tests_passed += 1
        else:
            print(f"   ❌ Concurrent downloads: only {successful}/10 successful")
            
    except Exception as e:
        print(f"   ❌ Concurrency test error: {e}")
    
    print(f"\n📊 Concurrency Tests: {tests_passed}/{total_tests} passed")
    return tests_passed, total_tests

def main():
    """Run all tests"""
    print("🧪 Multi-threaded HTTP Server Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8080/", timeout=5)
    except:
        print("❌ Server is not running on localhost:8080")
        print("   Please start the server first: python3 server.py")
        return
    
    print("✅ Server is running, starting tests...\n")
    
    total_passed = 0
    total_tests = 0
    
    # Run all test suites
    passed, tests = test_basic_functionality()
    total_passed += passed
    total_tests += tests
    
    passed, tests = test_security_features()
    total_passed += passed
    total_tests += tests
    
    passed, tests = test_file_integrity()
    total_passed += passed
    total_tests += tests
    
    passed, tests = test_concurrency()
    total_passed += passed
    total_tests += tests
    
    # Final results
    print("\n" + "=" * 50)
    print(f"🏁 FINAL RESULTS: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Server is working correctly.")
    else:
        print(f"⚠️  {total_tests - total_passed} tests failed.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()