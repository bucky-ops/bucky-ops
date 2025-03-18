# Simple Blockchain Implementation

This is a simple blockchain implementation in Python that includes basic blockchain functionality with proof-of-work mining and transaction management.

## Features

- Create and manage blocks
- Mine new blocks with proof-of-work
- Create and process transactions
- Check balances for addresses
- View the entire blockchain

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Mine a new block
```
GET /mine
```
Mines a new block and adds it to the blockchain.

### Create a new transaction
```
POST /transactions/new
```
Creates a new transaction to be added to the next block.

Example request body:
```json
{
    "sender": "address1",
    "recipient": "address2",
    "amount": 5
}
```

### Get the full blockchain
```
GET /chain
```
Returns the complete blockchain.

### Get balance for an address
```
GET /balance/<address>
```
Returns the balance for the specified address.

## Example Usage

1. Start the server:
```bash
python app.py
```

2. Mine a block:
```bash
curl http://localhost:5000/mine
```

3. Create a transaction:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"sender": "address1", "recipient": "address2", "amount": 5}' http://localhost:5000/transactions/new
```

4. View the blockchain:
```bash
curl http://localhost:5000/chain
```

5. Check a balance:
```bash
curl http://localhost:5000/balance/address1
``` 