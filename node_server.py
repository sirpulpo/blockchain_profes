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
        block_string = json.dumps(self.__dict__, sort_keys = True)
        return sha256(block_string.encode()).hexdigest()

class Blockchain:
    #dificultad de calculo para generar un nuevo bloque y añadirlo al Blockchain
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions= []
        self.chain = []
        self.create_genesis_block()

    # bloque génesis y anexarlo a la cadena. Tiene índice 0, hash anterior 0 y un hash válido.
    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]
