# -*- coding: utf-8 -*-

# SQLAlchemy object-relational mapper
from sqlalchemy import *

from bitcoin.script import Script

class BitcoinScript(TypeDecorator):
    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        return value
    def process_result_value(self, value, dialect):
        return Script(value)
    def copy(self):
        return self.__class__(self.impl.length)
