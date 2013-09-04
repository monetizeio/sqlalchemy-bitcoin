# -*- coding: utf-8 -*-

from .integer import LittleEndian

class Hash160(LittleEndian):
    def __init__(self, length=20, *args, **kwargs):
        super(Hash160, self).__init__(length, *args, **kwargs)

class Hash256(LittleEndian):
    def __init__(self, length=32, *args, **kwargs):
        super(Hash256, self).__init__(length, *args, **kwargs)
