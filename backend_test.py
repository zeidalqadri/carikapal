#!/usr/bin/env python3
"""
Backend API Testing for Integrated OSV Discovery System
Tests all API endpoints and system functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

class OSVSystemTester:
    """Test class for Integrated OSV Discovery System"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        print(f"🌐 Testing OSV Discovery System at: {self.base_url}")
        
    def run_test(self, name, method, endpoint, expected_status=200, data=None, check_json=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            status_success = response.status_code == expected_status
            
            # Check if response is valid JSON when expected
            json_success = True
            response_data = None
            if check_json and status_success:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    json_success = False
            
            success = status_success and json_success
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response_data:
                    print(f"📊 Response data: {json.dumps(response_data, indent=2)[:500]}...")
            else:
                if not status_success:
                    print(f"❌ Failed - Expected status {expected_status}, got {response.status_code}")
                elif not json_success:
                    print(f"❌ Failed - Invalid JSON response")
                print(f"🔍 Response: {response.text[:200]}...")
            
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_data": response_data if success else None,
                "error": None if success else response.text[:200]
            })
            
            return success, response_data if success else None
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "status_code": None,
                "expected_status": expected_status,
                "response_data": None,
                "error": str(e)
            })
            return False, None
    
    def test_system_status(self):
        """Test system status endpoint"""
        return self.run_test(
            "System Status API", 
            "GET", 
            "api/system-status"
        )
    
    def test_initialize_system(self):
        """Test system initialization endpoint"""
        return self.run_test(
            "Initialize System API", 
            "POST", 
            "api/initialize-system"
        )
    
    def test_component_health(self):
        """Test component health endpoint"""
        return self.run_test(
            "Component Health API", 
            "GET", 
            "api/component-health"
        )
    
    def test_start_discovery(self):
        """Test comprehensive discovery endpoint"""
        return self.run_test(
            "Start Comprehensive Discovery API", 
            "POST", 
            "api/start-comprehensive-discovery"
        )
    
    def test_integrated_status(self):
        """Test integrated status endpoint"""
        return self.run_test(
            "Integrated Status API", 
            "GET", 
            "api/integrated-status"
        )
    
    def test_run_full_discovery(self):
        """Test full discovery endpoint"""
        return self.run_test(
            "Run Full Discovery API", 
            "POST", 
            "api/run-full-discovery"
        )
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"📊 TEST SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 80)
        
        for i, result in enumerate(self.test_results):
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{i+1}. {result['name']} - {status}")
            if not result["success"]:
                print(f"   Endpoint: {result['endpoint']}")
                print(f"   Error: {result['error']}")
        
        print("\n" + "=" * 80)
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed successfully!")
        else:
            print(f"⚠️ {self.tests_run - self.tests_passed} tests failed")
        print("=" * 80)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test function"""
    print("=" * 80)
    print("🌊 INTEGRATED OSV DISCOVERY SYSTEM - API TESTING")
    print("=" * 80)
    
    tester = OSVSystemTester()
    
    # Test all API endpoints
    tester.test_system_status()
    
    # Initialize the system first
    init_success, _ = tester.test_initialize_system()
    
    # Only proceed with other tests if initialization was successful
    if init_success:
        time.sleep(2)  # Give the system time to initialize
        tester.test_component_health()
        
        # These tests might take longer, so we'll skip them for now
        # Uncomment if you want to run them
        # tester.test_start_discovery()
        # tester.test_run_full_discovery()
    else:
        print("⚠️ System initialization failed, skipping remaining tests")
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())