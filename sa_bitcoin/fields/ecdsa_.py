# -*- coding: utf-8 -*-

from sqlalchemy import *

from bitcoin.crypto import CompactSignature
from bitcoin.tools import StringIO

class EcdsaCompactSignature(TypeDecorator):
    impl = LargeBinary

    def __init__(self, length=65, *args, **kwargs):
        super(EcdsaCompactSignature, self).__init__(length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        return value.serialize()
    def process_result_value(self, value, dialect):
        return CompactSignature.deserialize(StringIO(value))
    def copy(self):
        return self.__class__(self.impl.length)
