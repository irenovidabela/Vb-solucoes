import requests
import unittest
import random
import string
from datetime import datetime

class VBSolucoesAPITester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(VBSolucoesAPITester, self).__init__(*args, **kwargs)
        self.base_url = "https://4d2a15ca-7963-47bd-ad9f-b40225691d51.preview.emergentagent.com/api"
        self.admin_token = None
        self.user_token = None
        self.admin_user = None
        self.regular_user = None
        self.test_incident_id = None

    def random_string(self, length=8):
        """Generate a random string for test data"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def setUp(self):
        """Set up for each test - ensure we have admin and user tokens"""
        # First check if the API is healthy
        self.test_health_endpoint()
        
        # Login as admin
        self.admin_login()
        
        # Create a test user if needed
        if not self.user_token:
            self.test_user_registration()

    def test_health_endpoint(self):
        """Test the health endpoint"""
        print("\n🔍 Testing health endpoint...")
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print("✅ Health endpoint is working")

    def admin_login(self):
        """Login as admin user"""
        print("\n🔍 Testing admin login...")
        response = requests.post(
            f"{self.base_url}/login",
            json={"username": "admin", "password": "admin123"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.admin_token = data["access_token"]
        self.admin_user = data["user"]
        print(f"✅ Admin login successful - Role: {self.admin_user['role']}")

    def test_user_registration(self):
        """Test user registration"""
        print("\n🔍 Testing user registration...")
        username = f"testuser_{self.random_string()}"
        email = f"{username}@test.com"
        password = "Test123!"
        
        response = requests.post(
            f"{self.base_url}/register",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.user_token = data["access_token"]
        self.regular_user = data["user"]
        print(f"✅ User registration successful - Username: {username}")

    def test_user_login(self):
        """Test regular user login"""
        if not self.regular_user:
            self.test_user_registration()
            return
            
        print("\n🔍 Testing regular user login...")
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "username": self.regular_user["username"],
                "password": "Test123!"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.user_token = data["access_token"]
        print("✅ User login successful")

    def test_create_incident(self):
        """Test creating a new incident"""
        print("\n🔍 Testing incident creation...")
        if not self.user_token:
            self.test_user_login()
            
        headers = {"Authorization": f"Bearer {self.user_token}"}
        incident_data = {
            "title": f"Test Incident {self.random_string()}",
            "description": "This is a test incident created by automated testing",
            "type": "acidente",
            "location": "Test Location",
            "people_involved": "Test Person 1, Test Person 2",
            "severity": "baixa"
        }
        
        response = requests.post(
            f"{self.base_url}/incidents",
            json=incident_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.test_incident_id = data["id"]
        print(f"✅ Incident created successfully - ID: {self.test_incident_id}")
        return data

    def test_get_incidents(self):
        """Test getting all incidents"""
        print("\n🔍 Testing get all incidents...")
        # Ensure we have at least one incident
        if not self.test_incident_id:
            self.test_create_incident()
            
        # Test as regular user
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = requests.get(
            f"{self.base_url}/incidents",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        user_incidents = response.json()
        self.assertIsInstance(user_incidents, list)
        print(f"✅ Regular user can see {len(user_incidents)} incidents")
        
        # Test as admin
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(
            f"{self.base_url}/incidents",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        admin_incidents = response.json()
        self.assertIsInstance(admin_incidents, list)
        print(f"✅ Admin can see {len(admin_incidents)} incidents")
        
        # Admin should see at least as many incidents as the regular user
        self.assertGreaterEqual(len(admin_incidents), len(user_incidents))

    def test_get_incident_details(self):
        """Test getting incident details"""
        print("\n🔍 Testing get incident details...")
        # Ensure we have an incident
        if not self.test_incident_id:
            incident = self.test_create_incident()
            self.test_incident_id = incident["id"]
            
        # Test as the user who created it
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = requests.get(
            f"{self.base_url}/incidents/{self.test_incident_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        incident = response.json()
        self.assertEqual(incident["id"], self.test_incident_id)
        print("✅ User can view their own incident details")
        
        # Test as admin
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(
            f"{self.base_url}/incidents/{self.test_incident_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        incident = response.json()
        self.assertEqual(incident["id"], self.test_incident_id)
        print("✅ Admin can view any incident details")

    def test_update_incident_status(self):
        """Test updating incident status (admin only)"""
        print("\n🔍 Testing update incident status (admin only)...")
        # Ensure we have an incident
        if not self.test_incident_id:
            incident = self.test_create_incident()
            self.test_incident_id = incident["id"]
            
        # Try as regular user (should fail)
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = requests.put(
            f"{self.base_url}/incidents/{self.test_incident_id}/status",
            json={"status": "em_andamento"},
            headers=headers
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        print("✅ Regular user cannot update incident status (403 Forbidden)")
        
        # Try as admin (should succeed)
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.put(
            f"{self.base_url}/incidents/{self.test_incident_id}/status",
            json={"status": "em_andamento"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Admin can update incident status")
        
        # Verify the status was updated
        response = requests.get(
            f"{self.base_url}/incidents/{self.test_incident_id}",
            headers=headers
        )
        incident = response.json()
        self.assertEqual(incident["status"], "em_andamento")
        print("✅ Status was successfully updated to 'em_andamento'")
        
        # Update to resolved
        response = requests.put(
            f"{self.base_url}/incidents/{self.test_incident_id}/status",
            json={"status": "resolvida"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the status was updated
        response = requests.get(
            f"{self.base_url}/incidents/{self.test_incident_id}",
            headers=headers
        )
        incident = response.json()
        self.assertEqual(incident["status"], "resolvida")
        print("✅ Status was successfully updated to 'resolvida'")

def run_tests():
    """Run all the API tests"""
    print("🚀 Starting VB Soluções API Tests")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add test methods
    tester = VBSolucoesAPITester()
    suite.addTest(VBSolucoesAPITester('test_health_endpoint'))
    suite.addTest(VBSolucoesAPITester('admin_login'))
    suite.addTest(VBSolucoesAPITester('test_user_registration'))
    suite.addTest(VBSolucoesAPITester('test_user_login'))
    suite.addTest(VBSolucoesAPITester('test_create_incident'))
    suite.addTest(VBSolucoesAPITester('test_get_incidents'))
    suite.addTest(VBSolucoesAPITester('test_get_incident_details'))
    suite.addTest(VBSolucoesAPITester('test_update_incident_status'))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    if not result.wasSuccessful():
        print("\n❌ Some tests failed:")
        for failure in result.failures:
            print(f"- {failure[0]}")
        for error in result.errors:
            print(f"- {error[0]}")
    else:
        print("\n✅ All API tests passed successfully!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests()