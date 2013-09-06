# -*- coding: utf-8 -*-

# SQLAlchemy object-relational mapper
from sqlalchemy import *

from bitcoin.serialize import serialize_varint, deserialize_varint
from bitcoin.tools import Bits, StringIO

class BitField(TypeDecorator):
    impl = LargeBinary

    def __init__(self, implicit=Bits(), *args, **kwargs):
        super(BitField, self).__init__(*args, **kwargs)
        self._implicit = implicit

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        assert value.startswith(self._implicit)
        return b''.join([
            serialize_varint(len(value)-len(self._implicit)),
            value[len(self._implicit):].tobytes()])
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        file_ = StringIO(value)
        bitlength = deserialize_varint(file_)
        return self._implicit + Bits(bytes=file_.read(), length=bitlength)
    def copy(self):
        return self.__class__(implicit=self._implicit, length=self.impl.length)
