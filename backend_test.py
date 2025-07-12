#!/usr/bin/env python3
"""
VB Soluções Backend API Test Suite
Tests all new functionalities: Comments, File Upload, Status Filtering, Password Change
"""

import requests
import sys
import json
from datetime import datetime
from io import BytesIO

class VBSolucoesAPITester:
    def __init__(self, base_url="https://4d2a15ca-7963-47bd-ad9f-b40225691d51.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.test_incident_id = None
        self.test_comment_id = None
        self.test_file_id = None
        self.test_username = None
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚀 Starting VB Soluções API Tests")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        if details:
            print(f"   {details}")

    def make_request(self, method, endpoint, data=None, files=None, token=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        if files:
            # Remove Content-Type for file uploads
            headers.pop('Content-Type', None)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            success = response.status_code == expected_status
            return success, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}, 0
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}, response.status_code

    def test_health_check(self):
        """Test API health endpoint"""
        success, data, status = self.make_request('GET', 'health')
        self.log_test("Health Check", success and data.get('status') == 'healthy')
        return success

    def test_admin_login(self):
        """Test admin login"""
        login_data = {"username": "admin", "password": "admin123"}
        success, data, status = self.make_request('POST', 'login', login_data)
        
        if success and 'access_token' in data:
            self.admin_token = data['access_token']
            self.log_test("Admin Login", True, f"Role: {data['user']['role']}")
            return True
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Data: {data}")
            return False

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "testpass123"
        }
        
        success, data, status = self.make_request('POST', 'register', user_data)
        
        if success and 'access_token' in data:
            self.user_token = data['access_token']
            self.test_username = user_data['username']
            self.log_test("User Registration", True, f"User: {data['user']['username']}")
            return True
        else:
            self.log_test("User Registration", False, f"Status: {status}, Data: {data}")
            return False

    def test_create_incident(self):
        """Test incident creation"""
        incident_data = {
            "title": "Test Incident for API Testing",
            "description": "This is a test incident created by automated testing",
            "type": "acidente",
            "location": "Apt 101",
            "people_involved": "Bloco A",
            "severity": "media"
        }
        
        success, data, status = self.make_request('POST', 'incidents', incident_data, token=self.user_token)
        
        if success and 'id' in data:
            self.test_incident_id = data['id']
            self.log_test("Create Incident", True, f"ID: {self.test_incident_id}")
            return True
        else:
            self.log_test("Create Incident", False, f"Status: {status}, Data: {data}")
            return False

    def test_get_incidents(self):
        """Test getting incidents list"""
        success, data, status = self.make_request('GET', 'incidents', token=self.user_token)
        
        if success and isinstance(data, list):
            self.log_test("Get Incidents", True, f"Found {len(data)} incidents")
            return True
        else:
            self.log_test("Get Incidents", False, f"Status: {status}")
            return False

    def test_get_incidents_by_status(self):
        """Test filtering incidents by status"""
        statuses = ['nova', 'em_andamento', 'resolvida', 'cancelada']
        all_passed = True
        
        for status in statuses:
            success, data, http_status = self.make_request('GET', f'incidents?status={status}', token=self.user_token)
            if success:
                self.log_test(f"Filter by Status '{status}'", True, f"Found {len(data)} incidents")
            else:
                self.log_test(f"Filter by Status '{status}'", False, f"HTTP {http_status}")
                all_passed = False
                
        return all_passed

    def test_update_incident_status(self):
        """Test updating incident status (admin only)"""
        if not self.test_incident_id:
            self.log_test("Update Incident Status", False, "No test incident available")
            return False
            
        status_data = {"status": "em_andamento"}
        success, data, status = self.make_request('PUT', f'incidents/{self.test_incident_id}/status', 
                                                 status_data, token=self.admin_token)
        
        self.log_test("Update Incident Status", success, f"Status: {status}")
        return success

    def test_create_comment(self):
        """Test creating comments"""
        if not self.test_incident_id:
            self.log_test("Create Comment", False, "No test incident available")
            return False
            
        # Test user comment
        comment_data = {"message": "This is a test comment from user"}
        success, data, status = self.make_request('POST', f'incidents/{self.test_incident_id}/comments', 
                                                 comment_data, token=self.user_token)
        
        if success and 'id' in data:
            self.test_comment_id = data['id']
            self.log_test("Create User Comment", True, f"Comment ID: {self.test_comment_id}")
            
            # Test admin comment
            admin_comment_data = {"message": "This is an admin response"}
            success2, data2, status2 = self.make_request('POST', f'incidents/{self.test_incident_id}/comments', 
                                                        admin_comment_data, token=self.admin_token)
            
            self.log_test("Create Admin Comment", success2, f"Admin comment created")
            return success and success2
        else:
            self.log_test("Create Comment", False, f"Status: {status}, Data: {data}")
            return False

    def test_get_comments(self):
        """Test getting comments for incident"""
        if not self.test_incident_id:
            self.log_test("Get Comments", False, "No test incident available")
            return False
            
        success, data, status = self.make_request('GET', f'incidents/{self.test_incident_id}/comments', 
                                                 token=self.user_token)
        
        if success and isinstance(data, list):
            self.log_test("Get Comments", True, f"Found {len(data)} comments")
            # Check if admin flag is properly set
            admin_comments = [c for c in data if c.get('is_admin')]
            user_comments = [c for c in data if not c.get('is_admin')]
            print(f"   Admin comments: {len(admin_comments)}, User comments: {len(user_comments)}")
            return True
        else:
            self.log_test("Get Comments", False, f"Status: {status}")
            return False

    def test_file_upload(self):
        """Test file upload functionality"""
        if not self.test_incident_id:
            self.log_test("File Upload", False, "No test incident available")
            return False
            
        # Create a test image file (small PNG)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {'file': ('test_image.png', BytesIO(test_image_data), 'image/png')}
        
        success, data, status = self.make_request('POST', f'incidents/{self.test_incident_id}/files', 
                                                 files=files, token=self.user_token)
        
        if success and 'file_id' in data:
            self.test_file_id = data['file_id']
            self.log_test("File Upload", True, f"File ID: {self.test_file_id}")
            return True
        else:
            self.log_test("File Upload", False, f"Status: {status}, Data: {data}")
            return False

    def test_get_files(self):
        """Test getting files for incident"""
        if not self.test_incident_id:
            self.log_test("Get Files", False, "No test incident available")
            return False
            
        success, data, status = self.make_request('GET', f'incidents/{self.test_incident_id}/files', 
                                                 token=self.user_token)
        
        if success and isinstance(data, list):
            self.log_test("Get Files", True, f"Found {len(data)} files")
            return True
        else:
            self.log_test("Get Files", False, f"Status: {status}")
            return False

    def test_file_upload_validation(self):
        """Test file upload validation (size, type limits)"""
        if not self.test_incident_id:
            self.log_test("File Upload Validation", False, "No test incident available")
            return False
            
        # Test invalid file type
        invalid_file = {'file': ('test.txt', BytesIO(b'test content'), 'text/plain')}
        success, data, status = self.make_request('POST', f'incidents/{self.test_incident_id}/files', 
                                                 files=invalid_file, token=self.user_token, expected_status=400)
        
        self.log_test("File Type Validation", success, "Rejected invalid file type")
        return success

    def test_delete_file(self):
        """Test file deletion"""
        if not self.test_file_id:
            self.log_test("Delete File", False, "No test file available")
            return False
            
        success, data, status = self.make_request('DELETE', f'files/{self.test_file_id}', 
                                                 token=self.user_token)
        
        self.log_test("Delete File", success, f"File deleted")
        return success

    def test_change_password(self):
        """Test password change functionality"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newtestpass123"
        }
        
        success, data, status = self.make_request('PUT', 'change-password', password_data, token=self.user_token)
        self.log_test("Change Password", success, f"Password updated")
        return success

    def test_permissions(self):
        """Test permission restrictions"""
        if not self.test_incident_id:
            self.log_test("Permission Tests", False, "No test incident available")
            return False
            
        # Test that regular user cannot update incident status
        status_data = {"status": "resolvida"}
        success, data, status = self.make_request('PUT', f'incidents/{self.test_incident_id}/status', 
                                                 status_data, token=self.user_token, expected_status=403)
        
        self.log_test("User Status Update Restriction", success, "User correctly denied status update")
        return success

    def run_all_tests(self):
        """Run complete test suite"""
        print("🔍 Starting API Test Suite...")
        
        # Basic functionality tests
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return False
            
        if not self.test_admin_login():
            print("❌ Admin login failed, stopping tests")
            return False
            
        if not self.test_user_registration():
            print("❌ User registration failed, stopping tests")
            return False
            
        # Core incident functionality
        self.test_create_incident()
        self.test_get_incidents()
        self.test_get_incidents_by_status()
        self.test_update_incident_status()
        
        # New features testing
        self.test_create_comment()
        self.test_get_comments()
        self.test_file_upload()
        self.test_get_files()
        self.test_file_upload_validation()
        self.test_delete_file()
        self.test_change_password()
        self.test_permissions()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test execution"""
    tester = VBSolucoesAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())