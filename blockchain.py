# blockchain.py
import hashlib
import time
import json
import os


class Block:
    def __init__(self, index, timestamp, filename, ipfs_hash, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.filename = filename
        self.ipfs_hash = ipfs_hash
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Calculate SHA-256 hash of block contents"""
        value = f"{self.index}{self.timestamp}{self.filename}{self.ipfs_hash}{self.previous_hash}"
        return hashlib.sha256(value.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = []
        # self.blockchain_file = 'blockchain.json' # Removed for persistence

    def create_genesis_block(self):
        """Create the first block in the blockchain"""
        genesis_block = Block(0, time.time(), "Genesis", "0", "0")
        self.chain.append(genesis_block)

    def create_block(self, filename, ipfs_hash):
        """
        Create a new block and add it to the chain

        Args:
            filename: Name of the uploaded file
            ipfs_hash: IPFS CID of the file

        Returns:
            Block: The newly created block
        """
        # If chain is empty, create genesis block first
        if not self.chain:
            self.create_genesis_block()

        index = len(self.chain)
        timestamp = time.time()
        previous_hash = self.chain[-1].hash
        new_block = Block(index, timestamp, filename, ipfs_hash, previous_hash)
        self.chain.append(new_block)
        return new_block

    def get_chain(self):
        """Return the entire blockchain"""
        return self.chain

    def is_valid(self):
        """
        Validate the blockchain integrity

        Returns:
            bool: True if blockchain is valid, False if tampered
        """
        if not self.chain:
            return True

        # Skip genesis block
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if current block's hash is correct
            if current_block.hash != current_block.calculate_hash():
                return False

            # Check if current block points to correct previous hash
            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def save_to_file(self, filename=None):
        """
        Save blockchain to JSON file for persistence
        """
        # Logic removed as blockchain.json is no longer used for persistence
        pass

    def load_from_file(self, filename=None):
        """
        Load blockchain from JSON file
        """
        # Logic removed as blockchain.json is no longer used for persistence
        if not self.chain:
<<<<<<< HEAD
            self.create_genesis_block()
=======
            self.create_genesis_block()
>>>>>>> 9d412e3b7dec77adff260fa7c2b563790b435f65
