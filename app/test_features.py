import unittest
import requests
import os
from dotenv import load_dotenv
from app.main import app

class TestFireLeadFeatures(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.app = app.test_client()
        self.test_url = "[https://example.com](https://example.com)"
        self.test_lead = {
            "company_name": "Test Corp",
            "email": "test@example.com",
            "phone_number": "1234567890",
            "website_url": "[https://testcorp.com](https://testcorp.com)",
            "industry": "Technology"
        }

    def test_firecrawl_extraction(self):
        """Test basic data extraction"""
        response = self.app.post('/api/extract/firecrawl', json={
            "url": self.test_url,
            "selected_fields": {
                "company_name": True,
                "email": True,
                "phone_number": True
            }
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue('data' in data)

    def test_data_enrichment(self):
        """Test multi-source data enrichment"""
        response = self.app.post('/api/extract/firecrawl', json={
            "url": self.test_url
        })
        data = response.get_json()
        self.assertTrue('confidence_score' in data)
        self.assertTrue('data_sources' in data)

    def test_lead_scoring(self):
        """Test lead scoring functionality"""
        response = self.app.post('/api/score_lead', json=self.test_lead)
        data = response.get_json()
        self.assertTrue('score' in data)
        self.assertTrue(0 <= data['score'] <= 100)

    def test_crm_export(self):
        """Test CRM export functionality"""
        # Test Pipedrive export
        response = self.app.post('/api/export/pipedrive', json=self.test_lead)
        self.assertEqual(response.status_code, 200)
        
        # Test CSV export
        response = self.app.post('/api/export/csv', json=self.test_lead)
        self.assertEqual(response.status_code, 200)

    def test_analytics_dashboard(self):
        """Test analytics dashboard data"""
        response = self.app.get('/api/dashboard-data')
        data = response.get_json()
        self.assertTrue('totalLeads' in data)
        self.assertTrue('averageScore' in data)

    def test_error_handling(self):
        """Test error handling"""
        # Test invalid URL
        response = self.app.post('/api/extract/firecrawl', json={
            "url": "invalid-url"
        })
        self.assertEqual(response.status_code, 400)

        # Test missing required fields
        response = self.app.post('/api/extract/firecrawl', json={})
        self.assertEqual(response.status_code, 400)

    def test_rate_limiting(self):
        """Test rate limiting"""
        for _ in range(101):  # Exceed rate limit
            response = self.app.post('/api/extract/firecrawl', json={
                "url": self.test_url
            })
        self.assertEqual(response.status_code, 429)  # Too Many Requests

if __name__ == '__main__':
    unittest.main()