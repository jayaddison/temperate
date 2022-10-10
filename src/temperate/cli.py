import json
from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path

from temperate import DemandSchedule
from temperate.wiser import WiserJSONEncoder


def _write_wiser_json(schedules, config):
    data = json.dumps(
        obj=schedules,
        cls=WiserJSONEncoder,
        config=config,
    )

    wiser_schedule_names = {v: k for k, v in config["wiser.zones"].items()}
    output_directory = config["temperate"]["output_directory"]

    # Split the data per-zone to be sent to the Wiser API
    for item in json.loads(data):
        schedule_id = str(item["id"])
        zone = wiser_schedule_names[schedule_id]
        p = Path() / output_directory / "wiser" / f"{schedule_id}-{zone}.json"
        p.write_text(json.dumps(item, indent=4))


def main():
    parser = ArgumentParser(description="Generate a heating schedule")
    parser.add_argument("rules", nargs="+")
    parser.add_argument("--config", nargs=1, required=True)
    args = parser.parse_args()

    nt = str().join(Path(rules_file).read_text() for rules_file in args.rules)
    config = ConfigParser()
    config.read(args.config)

    schedules = DemandSchedule.from_nestedtext(nt)
    format_processors = {"wiser": _write_wiser_json}

    formats = set(map(str.strip, config["temperate"]["formats"].split(",")))
    for format in format_processors:
        if format in formats:
            format_processors[format](schedules, config)
