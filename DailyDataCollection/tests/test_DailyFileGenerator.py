import unittest
from DailyDataCollection.DailyFileGenerator import DailyFileGenerator



class TestCurrentDateFiles(unittest.TestCase):

    # def setUp(self):
    #     # Initialize the DailyFileGenerator object before each test
    #     self.generator = DailyFileGenerator()
    #     self.test_data = [
    #         {"name": "Test Point 1", "coordinates": (1, 2)},
    #         {"name": "Test Point 2", "coordinates": (3, 4)},
    #         {"name": "Test Point 3", "coordinates": (5, 6)},
    #     ]

    def test_mapsInfo(self):
        
        # Initialize the DailyFileGenerator object
        generator = DailyFileGenerator()

        # Call the mapsInfo method
        result = generator.mapsInfo()

        # Check if the result is a dictionary
        self.assertIsInstance(result, dict)

        # Check if the dictionary contains the expected keys