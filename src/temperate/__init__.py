from collections import defaultdict

import nestedtext

from temperate.utils import create_timepoint


class DemandInterval:
    """
    A demand interval represents a request for a given temperature within a
    zoned area between two points in time.

    Intervals are combined and consolidated during schedule tabulation, so a
    demand interval supplied to the schedule processor may not be completely
    apparent (or visible at all, in some cases) in the finalized schedule; this
    can happen, for example, when overlapping demand intervals supercede it.
    """

    def __init__(self, zone, start, end, temperature):
        self.zone = zone
        self.start = start
        self.end = end
        self.temperature = temperature


class DemandSchedule:
    """
    Represents an abstract seven-day heating demand schedule for a single zone
    (for example, a room in a residential house).

    Constructing a schedule can be performed directly, by providing a list of
    demand intervals, or indirectly, by reading from a rules file.
    """

    @classmethod
    def _process_intervals(cls, zone, intervals):
        start_of_week, end_of_week = (
            create_timepoint(0, "00:00"),
            create_timepoint(7, "00:00"),
        )

        timepoints = defaultdict(list)
        for interval in intervals:
            timepoints[interval.start].append(interval)
            timepoints[interval.end].append(interval)

        active_intervals = set()
        configured_intervals = []

        prev_timepoint, prev_temperature = start_of_week, None
        for timepoint in sorted(timepoints.keys()):

            # Keep track of which demand intervals are active at each timepoint
            for interval in timepoints[timepoint]:
                if timepoint == interval.start:
                    active_intervals.add(interval)
                if timepoint == interval.end:
                    active_intervals.remove(interval)

            # Determine the demand temperature at this timepoint
            if active_intervals:
                temperature = max(i.temperature for i in active_intervals)
            else:
                temperature = None

            # Emit a demand interval when the demand temperature changes
            if prev_temperature != temperature:
                if prev_timepoint != start_of_week or prev_temperature:
                    configured_intervals.append(
                        DemandInterval(
                            zone=zone,
                            start=prev_timepoint,
                            end=timepoint,
                            temperature=prev_temperature,
                        )
                    )
            prev_timepoint, prev_temperature = timepoint, temperature

        # Ensure that there is a closing interval defined for the week
        if prev_timepoint != end_of_week:
            configured_intervals.append(
                DemandInterval(
                    zone=zone,
                    start=prev_timepoint,
                    end=end_of_week,
                    temperature=prev_temperature,
                )
            )
        return configured_intervals

    def __init__(self, zone, intervals):
        self.zone = zone
        self.intervals = self._process_intervals(zone, intervals)

    @classmethod
    def _parse_dayspec(cls, dayspec):
        return {
            "daily": [0, 1, 2, 3, 4, 5, 6],
            "weekday": [0, 1, 2, 3, 4],
            "weekend": [5, 6],
            "monday": [0],
            "tuesday": [1],
            "wednesday": [2],
            "thursday": [3],
            "friday": [4],
            "saturday": [5],
            "sunday": [6],
        }[dayspec]

    @classmethod
    def _construct_intervals(cls, day, rules):
        for name, data in rules.items():
            start, end = data["interval"].split("/")
            yield DemandInterval(
                zone=data.get("room"),
                start=create_timepoint(day, start),
                end=create_timepoint(day, end),
                temperature=int(data["temperature"]),
            )

    @classmethod
    def from_nestedtext(cls, content):
        nt = nestedtext.loads(content)

        # Within each dayspec (for example, 'weekend'), generate all intervals
        # described within the rules, and add them all to the list of intervals
        # for each covered day
        zone_intervals = defaultdict(list)
        for dayspec, spec in nt.items():
            days = cls._parse_dayspec(dayspec)
            for day in days:
                for interval in cls._construct_intervals(day, spec["rules"]):
                    zone_intervals[interval.zone].append(interval)

        return [
            DemandSchedule(zone=zone, intervals=intervals)
            for zone, intervals in zone_intervals.items()
        ]
