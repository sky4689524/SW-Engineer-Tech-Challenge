import unittest
from unittest.mock import patch, AsyncMock
from pydicom.dataset import Dataset
from client import SeriesCollector, SeriesDispatcher
import time


class TestSeriesCollector(unittest.TestCase):

    def setUp(self):
        """Create mock dataset for testing."""
        self.dataset1 = Dataset()
        self.dataset1.PatientID = '12345'
        self.dataset1.PatientName = 'Hanwool Park'
        self.dataset1.StudyInstanceUID = '1.2.3'
        self.dataset1.SeriesInstanceUID = '4.5.6'
        self.dataset1.SOPInstanceUID = '1.1.1'

        self.dataset2 = Dataset()
        self.dataset2.PatientID = '12345'
        self.dataset2.PatientName = 'Hanwool Park'
        self.dataset2.StudyInstanceUID = '1.2.3'
        self.dataset2.SeriesInstanceUID = '4.5.6'
        self.dataset2.SOPInstanceUID = '1.1.2'

    def test_add_instance(self):
        """Test that a series collector correctly collects DICOM instances."""
        collector = SeriesCollector(self.dataset1)
        self.assertEqual(collector.series_instance_uid, '4.5.6')
        self.assertEqual(len(collector.series), 1)

        # Add another instance with the same SeriesInstanceUID
        added = collector.add_instance(self.dataset2)
        self.assertTrue(added)
        self.assertEqual(len(collector.series), 2)

        # Try to add an instance with a different SeriesInstanceUID
        dataset3 = Dataset()
        dataset3.SeriesInstanceUID = '1.2.840.10008.1.1'
        added = collector.add_instance(dataset3)
        self.assertFalse(added)
        self.assertEqual(len(collector.series), 2)  # No new instance added


class TestSeriesDispatcher(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up the SeriesDispatcher."""
        self.dispatcher = SeriesDispatcher()

        # Create mock datasets
        self.dataset1 = Dataset()
        self.dataset1.PatientID = '12345'
        self.dataset1.PatientName = 'Hanwool Park'
        self.dataset1.StudyInstanceUID = '1.2.3'
        self.dataset1.SeriesInstanceUID = '4.5.6'
        self.dataset1.SOPInstanceUID = '1.1.1'

    @patch('client.aiohttp.ClientSession.post')
    async def test_dispatch_series_collector(self, mock_post):
        """Test that series is dispatched correctly after timeout."""
        # Mocking the POST request response
        mock_post.return_value.__aenter__.return_value.status = 200

        # Mock the json() method to return a mock response when awaited
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"message": "Test message from server"}
        )

        # Add dataset to the dispatcher
        await self.dispatcher.run_series_collectors(self.dataset1)

        # Simulate the passage of time to exceed the maximum wait time
        series_uid = self.dataset1.SeriesInstanceUID
        self.dispatcher.series_collectors[series_uid].last_update_time = time.time(
        ) - 2

        await self.dispatcher.dispatch_series_collector()

        # Check that the dispatch was called and data was sent
        self.assertTrue(mock_post.called)
        self.assertEqual(mock_post.call_count, 1)

        # Validate that the correct message was returned from the mocked server
        response_data = await mock_post.return_value.__aenter__.return_value.json()
        self.assertEqual(response_data.get('message'),
                         'Test message from server')

    @patch('client.aiohttp.ClientSession.post')
    async def test_send_data_to_server(self, mock_post):
        """Test that the correct data is sent to the server."""
        mock_post.return_value.__aenter__.return_value.status = 200

        # Mock the JSON response to simulate a real server response
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"message": "Test message from server"}
        )

        collector = SeriesCollector(self.dataset1)
        await self.dispatcher.extract_and_send_series_info(collector)

        expected_data = {
            'PatientID': '12345',
            'PatientName': 'Hanwool Park',
            'StudyInstanceUID': '1.2.3',
            'SeriesInstanceUID': '4.5.6',
            'InstanceInSeries': 1
        }

        # Ensure the correct data was sent
        mock_post.assert_called_once_with(
            'http://localhost:8000/series', json=expected_data)

        # Ensure the response was parsed correctly
        response_data = await mock_post.return_value.__aenter__.return_value.json()
        self.assertEqual(response_data.get('message'),
                         'Test message from server')


if __name__ == "__main__":
    unittest.main()
