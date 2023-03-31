import sys

from datetime import datetime, timedelta, timezone

REF_DT = datetime(year=2000, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timezone.utc)
"""
A DTN time is an unsigned integer indicating the number of milliseconds that have elapsed since the
DTN Epoch, 2000-01-01 00:00:00 +0000 (UTC). DTN time is not affected by leap seconds.
(RFC 9171, Section 4.2.6.)
"""

RUNNING_MICROPYTHON = sys.implementation.name == "micropython"


def from_dtn_timestamp(timestamp: int) -> datetime:
    """
    Converts a DTN timestamp to a Python datetime object
    :param timestamp: DTN timestamp
    :return: a Python datetime object representing the DTN timestamp
    """
    return REF_DT + timedelta(milliseconds=timestamp)


def to_dtn_timestamp(dt: datetime = None) -> int:
    if dt is None:
        dt = datetime.now(timezone.utc)

    """
    Converts a Python datetime object into a DTN timestamp
    :param dt:
    :return:
    """
    return int((dt - REF_DT).total_seconds() * 1000)  # cutoff beyond milliseconds, no rounding here
