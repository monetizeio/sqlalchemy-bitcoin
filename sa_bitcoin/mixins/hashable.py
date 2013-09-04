# -*- coding: utf-8 -*-

from sqlalchemy.ext.hybrid import hybrid_property

from bitcoin.mixins import HashableMixin
class HybridHashableMixin(HashableMixin):
    hash = hybrid_property(HashableMixin.hash.fget,
                           HashableMixin.hash.fset,
                           HashableMixin.hash.fdel,
                           lambda cls:cls._hash)
