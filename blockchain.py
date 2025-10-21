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
        self.blockchain_file = 'blockchain.json'

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
        index = len(self.chain)
        timestamp = time.time()
        previous_hash = self.chain[-1].hash if self.chain else "0"
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
        
        Args:
            filename: Optional custom filename (default: blockchain.json)
        """
        if filename:
            self.blockchain_file = filename
            
        try:
            data = []
            for block in self.chain:
                block_data = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'filename': block.filename,
                    'ipfs_hash': block.ipfs_hash,
                    'previous_hash': block.previous_hash,
                    'hash': block.hash
                }
                data.append(block_data)
            
            with open(self.blockchain_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving blockchain: {str(e)}")

    def load_from_file(self, filename=None):
        """
        Load blockchain from JSON file
        
        Args:
            filename: Optional custom filename (default: blockchain.json)
        """
        if filename:
            self.blockchain_file = filename
            
        try:
            if os.path.exists(self.blockchain_file):
                with open(self.blockchain_file, 'r') as f:
                    data = json.load(f)
                
                self.chain = []
                for block_data in data:
                    block = Block(
                        block_data['index'],
                        block_data['timestamp'],
                        block_data['filename'],
                        block_data['ipfs_hash'],
                        block_data['previous_hash']
                    )
                    # Verify the loaded hash matches
                    if block.hash != block_data['hash']:
                        print(f"Warning: Block {block.index} hash mismatch!")
                    self.chain.append(block)
                    
                print(f"Loaded {len(self.chain)} blocks from {self.blockchain_file}")
            else:
                # No existing blockchain file, create genesis block
                self.create_genesis_block()
                self.save_to_file()
                print("Created new blockchain with genesis block")
                
        except Exception as e:
            print(f"Error loading blockchain: {str(e)}")
            # Fallback to creating new blockchain
            self.chain = []
            self.create_genesis_block()
            self.save_to_file()