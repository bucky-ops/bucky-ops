import hashlib
import json
import time
from typing import List, Dict

class Block:
    def __init__(self, index: int, transactions: List[Dict], timestamp: float, previous_hash: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate the hash of the block."""
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int) -> None:
        """Mine the block with the given difficulty."""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined! Hash: {self.hash}")

class Blockchain:
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.pending_transactions: List[Dict] = []
        self.mining_reward = 10
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        """Create the first block in the chain."""
        genesis_block = Block(0, [], time.time(), "0")
        self.chain.append(genesis_block)

    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain."""
        return self.chain[-1]

    def mine_pending_transactions(self, miner_address: str) -> None:
        """Mine all pending transactions and add them to the blockchain."""
        block = Block(
            len(self.chain),
            self.pending_transactions,
            time.time(),
            self.get_latest_block().hash
        )
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = [
            {"from": "network", "to": miner_address, "amount": self.mining_reward}
        ]

    def add_transaction(self, sender: str, recipient: str, amount: float) -> None:
        """Add a new transaction to the pending transactions list."""
        self.pending_transactions.append({
            "from": sender,
            "to": recipient,
            "amount": amount
        })

    def get_balance(self, address: str) -> float:
        """Calculate the balance for a given address."""
        balance = 0

        # Check the pending transactions
        for transaction in self.pending_transactions:
            if transaction["from"] == address:
                balance -= transaction["amount"]
            if transaction["to"] == address:
                balance += transaction["amount"]

        # Check the blockchain
        for block in self.chain:
            for transaction in block.transactions:
                if transaction["from"] == address:
                    balance -= transaction["amount"]
                if transaction["to"] == address:
                    balance += transaction["amount"]

        return balance

    def is_chain_valid(self) -> bool:
        """Check if the blockchain is valid."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Verify current block's hash
            if current_block.hash != current_block.calculate_hash():
                return False

            # Verify chain continuity
            if current_block.previous_hash != previous_block.hash:
                return False

            # Verify proof of work
            if current_block.hash[:self.difficulty] != "0" * self.difficulty:
                return False

        return True 