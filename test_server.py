import unittest
import sqlite3
from fastapi.testclient import TestClient
from server import app, init_db

class TestFastAPIServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize the database before running tests."""
        init_db()  # Initialize the database schema

    def setUp(self):
        """Set up the TestClient and clean mock test data before each test."""
        self.client = TestClient(app)

        # clean test data from the previous runs before the test
        conn = sqlite3.connect('dicom_series.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM series WHERE SeriesInstanceUID LIKE 'test_%'")
        conn.commit()
        conn.close()

    def tearDown(self):
        """Remove only test data (with SeriesInstanceUID starting with 'test_') after each test case."""
        conn = sqlite3.connect('dicom_series.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM series WHERE SeriesInstanceUID LIKE 'test_%'")
        conn.commit()
        conn.close()

    def test_post_series_data(self):
        """Test the API with valid series data, using 'test_' prefix in SeriesInstanceUID."""
        data = {
            'PatientID': '12345',
            'PatientName': 'Hanwool Park',
            'StudyInstanceUID': '1.2.3',
            'SeriesInstanceUID': 'test_4.5.6',
            'InstanceInSeries': 10
        }

        response = self.client.post("/series", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json()["status"])

        # Verify the data is in the database
        conn = sqlite3.connect('dicom_series.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM series WHERE SeriesInstanceUID = ?', ('test_4.5.6',))
        record = cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 'test_4.5.6')  # SeriesInstanceUID
        self.assertEqual(record[1], '12345')  # PatientID
        self.assertEqual(record[2], 'Hanwool Park')  # PatientName
        self.assertEqual(record[4], 10)  # InstanceInSeries

    def test_post_invalid_data(self):
        """Test the API with invalid data."""
        invalid_data = {
            'PatientID': '12345',
            # Missing fields
        }
        response = self.client.post("/series", json=invalid_data)
        self.assertEqual(response.status_code, 422)  # 422 Unprocessable Entity


if __name__ == "__main__":
    unittest.main()
