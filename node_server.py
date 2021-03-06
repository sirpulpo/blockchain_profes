from hashlib import sha256
import json
import time
from flask import Flask, request
import requests


class Block:

    def __init__(self, index, transactions, timestamp, previus_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previus_hash = previus_hash
        self.nonce = 0

    # creamos el hash del blocke y su contenido.
    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys = True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    #dificultad de calculo para PoW.
    difficulty = 1 # no dejarla en 1.

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    # bloque génesis para anexarlo a la cadena.
    # Tiene índice 0, hash anterior 0 y un hash válido.
    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), '0') # se instancia un objeto Block para el génesis.
        genesis_block.hash = genesis_block.compute_hash() # se calcula su hash.
        self.chain.append(genesis_block) # se añade el génesis al chain.

    @property
    def last_block(self):
        return self.chain[-1] # verificar lo del génesis, ¿si se regresa a sí mismo?

    # se intentarán distintos valores en nonce hasta obtener un hash que satisfaga el criterio.
    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    # verificar el block para agregarlo al chain.
    def add_block(self, block, proof):
        previous_hash = self.last_block.hash # se carga el hash del blocke anterior.
        # se verifica si el hash anterior hace referencia al referido en este bloque.
        if previous_hash != block.previus_hash:
            return False
        # se verifica si la prueba de trabajo es valida.
        # if not Blockchain.is_valid_proof(block, proof):
        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previus_hash = '0'

        for block in chain:
            block_hash = block.hash
            # se elimina el hash para volver a calcularlosh usando el método compute_hash().
            delattr(block, 'hash')

            if not cls.is_valid_proof(block, block.hash) or \
                    previus_hash != block.previus_hash:
                result = False
                break

            block.hash, previus_hash = block_hash, block_hash

        return result

    # las transacciones pendientes se añaden al bloque y se calcula su prueba de trabajo.
    def mine(self):

        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index = last_block.index + 1,
                            transactions = self.unconfirmed_transactions,
                            timestamp = time.time(),
                            previus_hash = last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        # se anuncia a la red que se mino y agrego un nuevo bloque.
        announce_new_block(new_block)
        return new_block.index


app = Flask(__name__)

# una copia del nodo del Blockchain
blockchain = Blockchain()

# la dirección de otros miembros participantes en la red.
peers = set()


# punto de acceso para enviar nuevas transacciones (publicaciones en el blockchain).
@app.route('/new_transaction', methods = ['POST'])
def new_transaction():
    txt_data = request.get_json()
    # añadir campos para profesor y calificación.
    required_fields = ['author', 'content']

    for field in required_fields:
        if not txt_data.get(field):
            return 'Invalid transaction data', 404

    txt_data['timestamp'] = time.time()

    blockchain.add_new_transaction(txt_data)

    return 'Success', 201


# punto de acceso para retornar la copia del blockchain que tiene el nodo.
@app.route('/chain', methods = ['GET'])
def get_chain():
    # nos aseguramos de tener la cadena más larga.
    consensus()
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)

    return json.dumps({'length': len(chain_data),
                        'chain': chain_data})


# punto de acceso para minar las transacciones sin confirmar.
@app.route('/mine', methods = ['GET'])
def mine_unconfirmed_transactions():

    result = blockchain.mine()
    if not result:
        return 'No transactions to mine.'

    return 'Block #{} is mined'.format(result)


# punto de accesp para obtener las transacciones sin minar.
@app.route('/pending.txt')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


# punto de acceso para añadir nuevos miembros (peers) a la red.
@app.route('/add_nodes', methods = ['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return 'Invalid data', 400

    for node in nodes:
        peers.add(node)

    return 'Success', 201


# punto de acceso para añadir un bloque minado.
@app.route('/add_block', methods = ['POST'])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data['index'],
                    block_data['transactions'],
                    block_data['timestamp'],
                    block_data['previus_hash'])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return 'The block was discarted by the node', 400

    return 'Block added to the chain', 201


# algoritmo para resolver conflictos y concensuar, busca la cadena valida más larga y reemplaza la nuestra por aquella.
def consensus():

    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = request.get('http://{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']

        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


# se anuncia a la red que un nuevo bloque a sido minado.
# Otros bloques podran verificar la PoW y agregarla a sus respectivas cadenas.
def announce_new_block(block):
    for peer in peers:
        url = 'http://{}/add_block'.format(peer)
        request.post(url, data = json.dumps(block.__dict__, sort_keys = True))


app.run(debug = True, port = 8000)
