from datetime import datetime, timedelta

REF_DT = datetime(year=2000, month=1, day=1, hour=0, minute=0, second=0)
"""
A DTN time is an unsigned integer indicating the number of milliseconds that have elapsed since the
DTN Epoch, 2000-01-01 00:00:00 +0000 (UTC). DTN time is not affected by leap seconds.
(RFC 9171, Section 4.2.6.)
"""


def from_dtn_timestamp(timestamp: int) -> datetime:
    """
    Converts a DTN timestamp to a Python datetime object
    :param timestamp: DTN timestamp
    :return: a Python datetime object representing the DTN timestamp
    """
    return REF_DT + timedelta(milliseconds=timestamp)


def to_dtn_timestamp(dt: datetime = datetime.utcnow()) -> int:
    """
    Converts a Python datetime object into a DTN timestamp
    :param dt:
    :return:
    """
    return (dt - REF_DT).seconds * 1000
