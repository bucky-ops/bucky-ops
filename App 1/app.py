from flask import Flask, jsonify, request
from blockchain import Blockchain
import uuid

app = Flask(__name__)
blockchain = Blockchain()

# Generate a unique address for this node
node_address = str(uuid.uuid4()).replace('-', '')

@app.route('/mine', methods=['GET'])
def mine():
    """Mine a new block."""
    last_block = blockchain.get_latest_block()
    blockchain.mine_pending_transactions(node_address)
    
    response = {
        'message': 'New block mined!',
        'index': last_block.index + 1,
        'transactions': last_block.transactions,
        'hash': last_block.hash
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """Create a new transaction."""
    values = request.get_json()
    
    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    # Create a new transaction
    blockchain.add_transaction(values['sender'], values['recipient'], values['amount'])
    
    response = {
        'message': 'Transaction will be added to the next block',
        'transaction': {
            'sender': values['sender'],
            'recipient': values['recipient'],
            'amount': values['amount']
        }
    }
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    """Get the full blockchain."""
    response = {
        'chain': [{
            'index': block.index,
            'transactions': block.transactions,
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'nonce': block.nonce
        } for block in blockchain.chain],
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    """Get the balance for a given address."""
    balance = blockchain.get_balance(address)
    response = {
        'address': address,
        'balance': balance
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 