# Web-Based Blockchain Application

A modern web interface for the blockchain implementation, featuring user authentication, wallet management, and real-time blockchain visualization.

## Features

- User authentication system
- Personal wallet management
- Real-time blockchain visualization
- Block mining interface
- Transaction management
- Responsive web design
- Auto-refreshing blockchain status
- Copy-to-clipboard wallet addresses

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python app.py
```
The database will be automatically created when you first run the application.

3. Run the application:
```bash
python app.py
```

The web interface will be available at `http://localhost:5000`

## Usage

1. Register a new account to get your wallet address
2. Log in to your account
3. Mine blocks to earn coins
4. Send transactions to other users
5. View your transaction history
6. Monitor the blockchain status

## Project Structure

```
web_blockchain/
├── app.py              # Main application file
├── blockchain.py       # Blockchain implementation
├── requirements.txt    # Project dependencies
├── static/
│   ├── css/
│   │   └── style.css  # Custom styles
│   └── js/
│       └── main.js    # Client-side JavaScript
└── templates/
    ├── base.html      # Base template
    ├── index.html     # Home page
    ├── login.html     # Login page
    ├── register.html  # Registration page
    └── dashboard.html # User dashboard
```

## Security Notes

- This is a development version and should not be used in production without proper security measures
- Passwords are stored in plain text (should be hashed in production)
- The secret key should be properly configured in production
- Consider adding rate limiting and other security measures for production use

## Contributing

Feel free to submit issues and enhancement requests! 