import json

from temperate import DemandSchedule


class WiserJSONEncoder(json.JSONEncoder):
    """
    Implements a JSON encoding for heating schedules accepted by the HubR API
    """

    _DAY_NAMES = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday",
    }

    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)
        self.zone_schedule_ids = {
            None if zone == "default" else zone: int(schedule_id)
            for zone, schedule_id in config["wiser.zones"].items()
        }

    @classmethod
    def _empty_schedule(cls, schedule_id, daily_setpoints=None):
        return {"id": schedule_id, "Type": "Heating"} | {
            dayname: {"SetPoints": daily_setpoints or []}
            for dayname in cls._DAY_NAMES.values()
        }

    @classmethod
    def _nightly_shutdown(cls):
        return {"DegreesC": -200, "Time": 2300}

    @classmethod
    def _shutdown_every_night(cls, schedule_id):
        return cls._empty_schedule(
            schedule_id=schedule_id,
            daily_setpoints=[cls._nightly_shutdown()],
        )

    def encode(self, o):
        # Ensure that zones missing from the schedule list are shutdown nightly
        if isinstance(o, list) and o and isinstance(o[0], DemandSchedule):
            shutdowns = []
            zones = {schedule.zone for schedule in o}
            for zone, schedule_id in self.zone_schedule_ids.items():
                if zone not in zones:
                    shutdowns.append(self._shutdown_every_night(schedule_id))
            o.extend(shutdowns)
        return super().encode(o)

    def default(self, o):
        schedule = self._empty_schedule(self.zone_schedule_ids[o.zone])
        for interval in o.intervals:
            dayname = self._DAY_NAMES[interval.start.day]
            if interval.temperature is None:
                request_temperature = -200
            else:
                request_temperature = interval.temperature * 10
            schedule[dayname]["SetPoints"].append(
                {
                    "DegreesC": request_temperature,
                    "Time": int(interval.start.strftime("%H%M")),
                }
            )

        # Wiser's API rejects days that contain no setpoints, so add a shutdown
        for dayname in self._DAY_NAMES.values():
            if not schedule[dayname]["SetPoints"]:
                schedule[dayname]["SetPoints"].append(self._nightly_shutdown())

        return schedule
