# -*- coding: utf-8 -*-

import calendar
from datetime import datetime
import numbers

# SQLAlchemy object-relational mapper
from sqlalchemy import *

class UNIXDateTime(TypeDecorator):
    impl = DateTime

    def __init__(self, *args, **kwargs):
        super(UNIXDateTime, self).__init__(*args, **kwargs)
    def process_bind_param(self, value, dialect):
        if isinstance(value, numbers.Integral):
            value = datetime.utcfromtimestamp(value)
        return value
    def copy(self):
        return self.__class__(self.impl.timezone)

class BlockTime(TypeDecorator):
    impl = DateTime

    from bitcoin.defaults import LOCKTIME_THRESHOLD as THRESHOLD_UNIXTIME
    THRESHOLD_DATETIME = datetime.utcfromtimestamp(THRESHOLD_UNIXTIME)

    def __init__(self, *args, **kwargs):
        super(BlockTime, self).__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime):
            if value < self.THRESHOLD_DATETIME:
                raise ValueError(u"unixtime below lock-time threshold")
            else:
                return value
        if isinstance(value, numbers.Integral):
            if value < self.THRESHOLD_UNIXTIME:
                return datetime.utcfromtimestamp(value)
            else:
                raise ValueError(u"block height above lock-time threshold")
        raise TypeError(u"unexpected data type: %s" % repr(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value < self.THRESHOLD_DATETIME:
            return calendar.timegm(value.utctimetuple())
        return value

    def copy(self):
        return self.__class__(self.impl.timezone)
