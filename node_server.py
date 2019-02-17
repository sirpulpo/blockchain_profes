from hashlib import sha256
import json
import time


class Block:

    def __init__(self, transactions, timestamp, previus_hash):
        self.index = index
        sefl.transactions = transactions
        self.timestamp = timestamp
        self.previus_hash = previus_hash
        self.nonce = 0

    # creamos el hash del blocke y su contenido.
    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
