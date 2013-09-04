# -*- coding: utf-8 -*-

from .patricia import PatriciaNode
from bitcoin.ledger import (
    BaseTxIdIndex, UnspentTransaction,
    BaseContractIndex, ContractOutPoint, OutputData)

class TxIdIndex(BaseTxIdIndex, PatriciaNode):
    __mapper_args__ = {
        'polymorphic_identity': 'txid_index'}
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('type', 'txid_index')
        super(TxIdIndex, self).__init__(*args, **kwargs)
TxIdIndex.node_class = TxIdIndex

class ContractIndex(BaseContractIndex, PatriciaNode):
    __mapper_args__ = {
        'polymorphic_identity': 'contract_index'}
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('type', 'contract_index')
        super(ContractIndex, self).__init__(*args, **kwargs)
ContractIndex.node_class = ContractIndex
