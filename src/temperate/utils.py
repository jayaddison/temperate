from datetime import datetime, time, timezone


def create_timepoint(day, timestring):
    return datetime.combine(
        date=datetime.fromtimestamp(day * 86400, tz=timezone.utc),
        time=time.fromisoformat(timestring),
        tzinfo=timezone.utc,
    )
