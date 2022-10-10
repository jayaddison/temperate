import json
from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path

from temperate import DemandSchedule
from temperate.wiser import WiserJSONEncoder


def main():
    parser = ArgumentParser(description="Generate a heating schedule")
    parser.add_argument("rules", nargs="+")
    parser.add_argument("--config", nargs=1, required=True)
    args = parser.parse_args()

    nt = str().join(Path(rules_file).read_text() for rules_file in args.rules)
    config = ConfigParser()
    config.read(args.config)

    schedules = DemandSchedule.from_nestedtext(nt)
    data = json.dumps(
        obj=schedules,
        cls=WiserJSONEncoder,
        config=config,
    )

    # Split the data per-zone to be sent to the Wiser API
    wiser_schedule_names = {v: k for k, v in config["wiser.zones"].items()}
    for item in json.loads(data):
        schedule_id = str(item["id"])
        zone = wiser_schedule_names[schedule_id]
        filename = f"{schedule_id}-{zone}.json"
        with open(filename, mode="w") as f:
            f.write(json.dumps(item, indent=4))
