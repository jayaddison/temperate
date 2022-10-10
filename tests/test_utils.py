import unittest
from datetime import datetime, timezone

import temperate.utils as utils

valid_timepoints = {
    # day, timestring, expected
    (0, "21:00", "1970-01-01T21:00:00"),
    (0, "18:00", "1970-01-01T18:00:00"),
    (0, "01:30", "1970-01-01T01:30:00"),
    (4, "12:00", "1970-01-05T12:00:00"),
}

invalid_timepoints = [
    # day, timestring
    (0, "24:00"),
    (0, "PT25H"),
]


class UtilsTest(unittest.TestCase):
    def _utc_datetime(self, date_string):
        return datetime.fromisoformat(date_string).replace(tzinfo=timezone.utc)

    def test_valid_timepoints(self):
        for day, timestring, expected in valid_timepoints:
            with self.subTest(day=day, timestring=timestring):
                timepoint = utils.create_timepoint(day, timestring)
                self.assertEqual(timepoint, self._utc_datetime(expected))

    def test_invalid_timepoints(self):
        for day, timestring in invalid_timepoints:
            with self.subTest(timestring=timestring):
                with self.assertRaises(ValueError):
                    utils.create_timepoint(day, timestring)
