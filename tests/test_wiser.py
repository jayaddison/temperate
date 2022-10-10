import json
import unittest
from configparser import ConfigParser
from pathlib import Path

from temperate import DemandSchedule
from temperate.wiser import WiserJSONEncoder


class DemandScheduleTest(unittest.TestCase):
    def _home_config(self):
        config = ConfigParser()
        config.read_string(
            """
            [wiser.zones]
            default = 1001
            office = 1002
            spareroom = 1003
        """
        )
        return config

    def test_schedule_parser(self):
        for path_in in Path("tests/inputs").glob("*.nt"):
            path_out = Path(f"tests/outputs/{path_in.stem}-wiser.json")
            with self.subTest(file=path_in.name):
                schedules = DemandSchedule.from_nestedtext(path_in.read_text())
                schedule_json = json.dumps(
                    obj=schedules,
                    indent=4,
                    cls=WiserJSONEncoder,
                    config=self._home_config(),
                )
                self.assertEqual(schedule_json, path_out.read_text())
