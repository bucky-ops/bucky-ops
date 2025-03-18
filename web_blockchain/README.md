# Web-Based Blockchain Application

A web-based blockchain application that allows users to create accounts, mine blocks, and transfer coins between users. The application includes an admin interface for user management.

## Features

### User Features
- User registration and authentication
- Wallet management with unique addresses
- Block mining with rewards
- User-to-user coin transfers
- Transaction history viewing
- Real-time balance updates

### Admin Features
- User account management
- Password reset functionality
- User balance monitoring
- Admin user creation
- System-wide transaction monitoring

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd web_blockchain
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Access the application at `http://localhost:5000`

## Default Admin Account
- Username: `admin`
- Password: `admin123`

**Important**: Change the admin password immediately after first login for security purposes.

## Usage Guide

### For Regular Users

1. **Registration**
   - Click "Register" on the homepage
   - Enter your desired username and password
   - A unique wallet address will be generated automatically

2. **Mining Coins**
   - Log in to your account
   - Click the "Mine New Block" button
   - Earn mining rewards for each successfully mined block

3. **Sending Coins**
   - Log in to your account
   - Enter the recipient's username
   - Enter the amount to send
   - Click "Send"

4. **Viewing Transactions**
   - All your transactions are visible in the dashboard
   - Transaction history shows sent and received coins
   - Each transaction includes timestamp and amount

### For Administrators

1. **Accessing Admin Dashboard**
   - Log in with admin credentials
   - Click "Admin Dashboard" button
   - Or directly access `/admin` route

2. **User Management**
   - View all users and their balances
   - Create new user accounts
   - Reset user passwords
   - Monitor system transactions

3. **Creating New Users**
   - Click "Create New User" in admin dashboard
   - Enter username and password
   - Optionally set admin privileges
   - Submit to create the account

4. **Resetting Passwords**
   - Find the user in the user management table
   - Click "Reset Password" button
   - Enter new password in the modal
   - Submit to update the password

## Security Notes

1. **Password Security**
   - Change the default admin password immediately
   - Use strong passwords for all accounts
   - Never share your login credentials

2. **Transaction Security**
   - Verify recipient usernames before sending
   - Check transaction amounts carefully
   - Monitor your transaction history regularly

3. **Admin Access**
   - Limit admin account access to trusted personnel
   - Regularly audit admin actions
   - Monitor system for suspicious activities

## Technical Details

### Database
- SQLite database for user and transaction storage
- Automatic database creation on first run
- Transaction history persistence

### Blockchain Features
- Proof of Work mining system
- Transaction verification
- Block chain validation
- Mining rewards system

### Web Interface
- Responsive design
- Real-time updates
- User-friendly forms
- Transaction notifications

## Development

### Project Structure
```
web_blockchain/
├── app.py              # Main application file
├── blockchain.py       # Blockchain implementation
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS)
└── templates/         # HTML templates
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    └── admin.html
```

### Adding New Features
1. Update the blockchain implementation in `blockchain.py`
2. Add new routes in `app.py`
3. Create corresponding templates in `templates/`
4. Update static files as needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
