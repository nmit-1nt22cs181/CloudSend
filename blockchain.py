import hashlib
import time

class Block:
    def __init__(self, index, timestamp, filename, ipfs_hash, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.filename = filename
        self.ipfs_hash = ipfs_hash
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        value = f"{self.index}{self.timestamp}{self.filename}{self.ipfs_hash}{self.previous_hash}"
        return hashlib.sha256(value.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), "Genesis", "0", "0")
        self.chain.append(genesis_block)

    def create_block(self, filename, ipfs_hash):
        index = len(self.chain)
        timestamp = time.time()
        previous_hash = self.chain[-1].hash
        new_block = Block(index, timestamp, filename, ipfs_hash, previous_hash)
        self.chain.append(new_block)
        return new_block

    def get_chain(self):
        return self.chain
