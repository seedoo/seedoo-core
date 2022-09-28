import datetime
from typing import Union

import pytz

from odoo import models, api, fields

DATETIME_TIMEZONE_LOCAL_DEFAULT: str = "Europe/Rome"

DATETIME_TIMEZONE_UTC: str = "UTC"

UTC_TIMEZONE = pytz.timezone("UTC")


class UtilityDt(models.AbstractModel):
    _name = "fl.utility.dt"
    _description = "Utility for Datetime manipulation"

    @api.model
    def convert(self, dt, tz_from: str, tz_to: str):
        if not isinstance(dt, datetime.datetime):
            return False
        timezone_from = pytz.timezone(tz_from)
        timezone_to = pytz.timezone(tz_to)
        dt_from = timezone_from.localize(dt)
        dt_to = dt_from.astimezone(timezone_to)
        return dt_to

    @api.model
    def local_to_utc(self, dt, tz_local: str = DATETIME_TIMEZONE_LOCAL_DEFAULT):
        return self.convert(dt, tz_local, DATETIME_TIMEZONE_UTC)

    @api.model
    def utc_to_local(self, dt, tz_local: str = DATETIME_TIMEZONE_LOCAL_DEFAULT):
        return self.convert(dt, DATETIME_TIMEZONE_UTC, tz_local)

    @api.model
    def dt_to_str(self, dt, fmt: str = fields.DATETIME_FORMAT) -> str:
        return dt.strftime(fmt)

    @api.model
    def dt_to_iso_z(self, dt: datetime.datetime):
        if not dt:
            return ""

        if dt.tzinfo is None:
            dt = dt.astimezone(UTC_TIMEZONE)

        if dt.tzinfo != UTC_TIMEZONE:
            dt = dt.astimezone(UTC_TIMEZONE)

        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @api.model
    def dt_from_timestamp(self, ts) -> Union[None, datetime.datetime]:
        ts_final: int

        if not ts:
            return None

        elif isinstance(ts, int):
            ts_final = ts

        elif isinstance(ts, float):
            ts_final = int(ts)

        else:
            raise ValueError("Input format not recognized: %s" % ts)

        if ts_final > 100000000000000:
            ts_final /= 1000
        if ts_final > 100000000000:
            ts_final /= 1000

        return datetime.datetime.fromtimestamp(ts_final)
