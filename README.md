# Blockchain-Based File Management System

A decentralized file management system built with Flask and Ethereum blockchain integration. This system provides secure file storage, version control, and access management with blockchain-based verification.

## Features

- User authentication and role-based access control
- Secure file upload and storage
- File versioning and history tracking
- Blockchain-based file verification
- Department-based file organization
- Admin dashboard for system management
- Activity logging and audit trails
- File tagging and categorization

## Prerequisites

- Python 3.8+
- PostgreSQL
- Ethereum node (local or remote)
- Web3.py
- Flask and related dependencies

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/file-management-dapp.git
cd file-management-dapp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python create_db.py
```

5. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the variables in `.env` with your configuration

6. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

7. Create an admin user:
```bash
flask create-admin
```

## Current Known Issues

1. **Password Hash Length**
   - Issue: Password hash length exceeds database column size
   - Status: Fixed in code but requires database migration
   - Solution: Will be addressed in next update

2. **CSRF Token Validation**
   - Issue: Some forms may experience CSRF validation errors
   - Status: Under investigation
   - Solution: Will be fixed in next update

3. **Blockchain Integration**
   - Issue: Contract ABI not fully implemented
   - Status: In progress
   - Solution: Will be completed in next update

4. **File Upload Size**
   - Issue: Large file uploads may timeout
   - Status: Known limitation
   - Solution: Will implement chunked upload in next update

## Usage

1. Start the application:
```bash
python app.py
```

2. Access the application at `http://localhost:5000`

3. Default admin credentials:
   - Username: admin
   - Password: admin123 (change in production!)

## Security Considerations

- Change default admin password immediately
- Use HTTPS in production
- Configure proper session security
- Implement rate limiting
- Use secure file storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask framework
- Web3.py library
- PostgreSQL database
- Ethereum blockchain

## Roadmap

1. Implement chunked file uploads
2. Add file encryption
3. Enhance blockchain integration
4. Implement file sharing
5. Add API endpoints
6. Improve error handling
7. Add comprehensive testing

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 