from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from web3 import Web3
import os
from datetime import datetime, timedelta
import hashlib
from functools import wraps
from flask.cli import FlaskGroup, with_appcontext
import click
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

# Session configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-1234567890abcdefghijklmnopqrstuvwxyz')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Helps prevent CSRF
app.config['SESSION_COOKIE_PATH'] = '/'

# Database configuration
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '7459')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'file_management')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# CSRF protection
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('CSRF_SECRET_KEY', 'csrf-secret-key-1234567890')

# Initialize extensions
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'  # Enables session protection
login_manager.refresh_view = 'login'  # View to redirect to when session needs refresh
login_manager.needs_refresh_message = 'Please log in again to confirm your identity.'
login_manager.needs_refresh_message_category = 'info'

# Create database tables
with app.app_context():
    db.create_all()
    app.logger.info("Database tables created/verified")

# Web3 setup
w3 = Web3(Web3.HTTPProvider(os.environ.get('ETHEREUM_NODE_URL', 'http://localhost:8545')))
contract_address = os.environ.get('CONTRACT_ADDRESS')
contract_abi = []  # Load your contract ABI here

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    ethereum_address = db.Column(db.String(42), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    storage_used = db.Column(db.Integer, default=0)  # Storage used in bytes
    max_storage = db.Column(db.Integer, default=100 * 1024 * 1024)  # Default 100MB
    files = db.relationship('File', backref='owner', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    file_versions = db.relationship('FileVersion', backref='creator', lazy=True)
    file_tags = db.relationship('FileTag', backref='creator', lazy=True)
    access_logs = db.relationship('AccessLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_storage_usage(self):
        """Update user's storage usage based on their files"""
        total_size = db.session.query(db.func.sum(File.file_size)).filter_by(user_id=self.id).scalar() or 0
        self.storage_used = total_size
        db.session.commit()

    def has_storage_space(self, file_size):
        """Check if user has enough storage space for a new file"""
        return (self.storage_used + file_size) <= self.max_storage

    def get_storage_percentage(self):
        """Get storage usage as percentage"""
        return (self.storage_used / self.max_storage) * 100 if self.max_storage > 0 else 0

    def log_activity(self, action, ip_address=None, user_agent=None):
        """Log user activity"""
        log = AccessLog(
            user_id=self.id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        db.session.commit()

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    file_type = db.Column(db.String(50))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    department = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blockchain_id = db.Column(db.Integer)
    version = db.Column(db.Integer, default=1)
    is_latest = db.Column(db.Boolean, default=True)
    file_size = db.Column(db.Integer)  # Size in bytes
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = db.relationship('Comment', backref='file', lazy=True)
    versions = db.relationship('FileVersion', backref='file', lazy=True)
    tags = db.relationship('FileTag', backref='file', lazy=True)
    access_logs = db.relationship('AccessLog', backref='file', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)

class FileVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    change_description = db.Column(db.Text)

class FileTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # view, download, edit, etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(255))

# Role-based access control
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Debug session information
        app.logger.debug(f"Session ID: {request.cookies.get('session')}")
        app.logger.debug(f"User authenticated: {current_user.is_authenticated}")
        if current_user.is_authenticated:
            app.logger.debug(f"User role: {current_user.role}")
            app.logger.debug(f"User ID: {current_user.id}")
        
        if not current_user.is_authenticated:
            app.logger.warning("Unauthorized access attempt: User not authenticated")
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))
            
        if current_user.role != 'admin':
            app.logger.warning(f"Unauthorized access attempt: User {current_user.username} with role {current_user.role}")
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function

def approver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'approver':
            flash('Approver access required')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        app.logger.info(f"User {current_user.username} already authenticated, redirecting to dashboard")
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        app.logger.debug(f"Login attempt for username: {username}")
        
        if not username or not password:
            app.logger.warning("Login attempt with missing credentials")
            flash('Please provide both username and password', 'error')
            return render_template('login.html')
            
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Log successful login attempt
            app.logger.info(f'Successful login for user: {username}')
            
            # Login the user
            login_user(user, remember=True)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Debug session information
            app.logger.debug(f"Session created for user {username}")
            app.logger.debug(f"Session ID: {request.cookies.get('session')}")
            app.logger.debug(f"User authenticated: {current_user.is_authenticated}")
            app.logger.debug(f"User role: {current_user.role}")
            
            # Redirect to the next page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            app.logger.info(f"Redirecting user {username} to: {next_page}")
            return redirect(next_page)
        else:
            # Log failed login attempt
            app.logger.warning(f'Failed login attempt for username: {username}')
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Log all form data
        app.logger.debug("Registration attempt with data:")
        app.logger.debug(f"Username: {request.form.get('username')}")
        app.logger.debug(f"Email: {request.form.get('email')}")
        app.logger.debug(f"Role: {request.form.get('role')}")
        app.logger.debug(f"Department: {request.form.get('department')}")
        app.logger.debug(f"Ethereum Address: {request.form.get('ethereum_address')}")
        
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        department = request.form.get('department')
        ethereum_address = request.form.get('ethereum_address')

        # Validate input
        if not all([username, email, password, confirm_password, role, department, ethereum_address]):
            missing_fields = []
            if not username: missing_fields.append('username')
            if not email: missing_fields.append('email')
            if not password: missing_fields.append('password')
            if not confirm_password: missing_fields.append('confirm_password')
            if not role: missing_fields.append('role')
            if not department: missing_fields.append('department')
            if not ethereum_address: missing_fields.append('ethereum_address')
            
            app.logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            flash(f'Missing required fields: {", ".join(missing_fields)}', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            app.logger.warning("Password mismatch")
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        if len(password) < 8:
            app.logger.warning("Password too short")
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('register'))

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            app.logger.warning(f"Username already exists: {username}")
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            app.logger.warning(f"Email already exists: {email}")
            flash('Email already exists', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(ethereum_address=ethereum_address).first():
            app.logger.warning(f"Ethereum address already registered: {ethereum_address}")
            flash('Ethereum address already registered', 'error')
            return redirect(url_for('register'))

        # Validate Ethereum address format
        if not ethereum_address.startswith('0x') or len(ethereum_address) != 42:
            app.logger.warning(f"Invalid Ethereum address format: {ethereum_address}")
            flash('Invalid Ethereum address format', 'error')
            return redirect(url_for('register'))

        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                role=role,
                department=department,
                ethereum_address=ethereum_address
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            app.logger.info(f"Successfully registered new user: {username}")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        files = File.query.all()
    else:
        files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', files=files)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard'))
    
    if file:
        try:
            # Check storage space
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if not current_user.has_storage_space(file_size):
                flash('Not enough storage space', 'error')
                return redirect(url_for('dashboard'))
            
            # Ensure filename is safe
            filename = os.path.basename(file.filename)
            # Create a unique filename to prevent overwrites
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
            
            # Generate file hash
            file_hash = hashlib.sha256(file.read()).hexdigest()
            file.seek(0)
            
            # Ensure upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save file locally
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Create database record
            new_file = File(
                filename=filename,  # Store original filename
                file_hash=file_hash,
                file_type=file.content_type,
                department=current_user.department,
                user_id=current_user.id,
                file_size=file_size
            )
            db.session.add(new_file)
            db.session.commit()
            
            # Create initial version
            version = FileVersion(
                file_id=new_file.id,
                version_number=1,
                file_hash=file_hash,
                file_path=unique_filename,
                created_by=current_user.id,
                change_description="Initial version"
            )
            db.session.add(version)
            
            # Update user's storage usage
            current_user.update_storage_usage()
            
            # Log activity
            current_user.log_activity(
                'upload',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            # Upload to blockchain
            try:
                contract = w3.eth.contract(address=contract_address, abi=contract_abi)
                tx_hash = contract.functions.uploadFile(
                    file_hash,
                    filename,
                    file.content_type,
                    current_user.department
                ).transact({'from': current_user.ethereum_address})
                new_file.blockchain_id = w3.eth.wait_for_transaction_receipt(tx_hash).blockNumber
                db.session.commit()
            except Exception as e:
                flash(f'Blockchain upload failed: {str(e)}', 'warning')
            
            flash('File uploaded successfully', 'success')
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
            db.session.rollback()
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return redirect(url_for('dashboard'))

@app.route('/file/<int:file_id>/update', methods=['POST'])
@login_required
def update_file(file_id):
    file = File.query.get_or_404(file_id)
    
    if file.user_id != current_user.id and current_user.role != 'admin':
        flash('Permission denied', 'error')
        return redirect(url_for('dashboard'))
    
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('dashboard'))
    
    new_file = request.files['file']
    if new_file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Check storage space
        new_file.seek(0, 2)  # Seek to end
        file_size = new_file.tell()
        new_file.seek(0)  # Reset to beginning
        
        if not current_user.has_storage_space(file_size - file.file_size):
            flash('Not enough storage space', 'error')
            return redirect(url_for('dashboard'))
        
        # Generate new file hash
        new_file_hash = hashlib.sha256(new_file.read()).hexdigest()
        new_file.seek(0)
        
        # Create new version filename
        new_version_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        new_version_path = os.path.join(app.config['UPLOAD_FOLDER'], new_version_filename)
        
        # Save new version
        new_file.save(new_version_path)
        
        # Create new version record
        new_version = FileVersion(
            file_id=file.id,
            version_number=file.version + 1,
            file_hash=new_file_hash,
            file_path=new_version_filename,
            created_by=current_user.id,
            change_description=request.form.get('change_description', 'File updated')
        )
        db.session.add(new_version)
        
        # Update file record
        file.version += 1
        file.file_hash = new_file_hash
        file.file_size = file_size
        file.last_modified = datetime.utcnow()
        
        # Update user's storage usage
        current_user.update_storage_usage()
        
        # Log activity
        current_user.log_activity(
            'update',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        db.session.commit()
        flash('File updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        if os.path.exists(new_version_path):
            os.remove(new_version_path)
        flash(f'Error updating file: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/approve/<int:file_id>', methods=['POST'])
@login_required
@approver_required
def approve_file(file_id):
    file = File.query.get_or_404(file_id)
    comment = request.form.get('comment', '')
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        tx_hash = contract.functions.approveFile(file.blockchain_id).transact(
            {'from': current_user.ethereum_address}
        )
        w3.eth.wait_for_transaction_receipt(tx_hash)
        
        file.status = 'approved'
        new_comment = Comment(
            content=comment,
            user_id=current_user.id,
            file_id=file_id
        )
        db.session.add(new_comment)
        db.session.commit()
        
        flash('File approved successfully')
    except Exception as e:
        flash(f'Approval failed: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/reject/<int:file_id>', methods=['POST'])
@login_required
@approver_required
def reject_file(file_id):
    file = File.query.get_or_404(file_id)
    comment = request.form.get('comment', '')
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        tx_hash = contract.functions.rejectFile(file.blockchain_id, comment).transact(
            {'from': current_user.ethereum_address}
        )
        w3.eth.wait_for_transaction_receipt(tx_hash)
        
        file.status = 'rejected'
        new_comment = Comment(
            content=comment,
            user_id=current_user.id,
            file_id=file_id
        )
        db.session.add(new_comment)
        db.session.commit()
        
        flash('File rejected successfully')
    except Exception as e:
        flash(f'Rejection failed: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get all users and files
    users = User.query.all()
    files = File.query.all()
    
    # Calculate total storage used (handle None values)
    total_storage = sum(file.file_size or 0 for file in files)
    
    # Get recent files and users
    recent_files = File.query.order_by(File.upload_date.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent activity
    recent_activity = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         users=users,
                         files=files,
                         total_storage=total_storage,
                         recent_files=recent_files,
                         recent_users=recent_users,
                         recent_activity=recent_activity)

@app.route('/admin/files')
@login_required
@admin_required
def admin_files():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    department = request.args.get('department')
    search = request.args.get('search')
    
    query = File.query
    
    if status:
        query = query.filter_by(status=status)
    if department:
        query = query.filter_by(department=department)
    if search:
        query = query.filter(File.filename.ilike(f'%{search}%'))
    
    files = query.order_by(File.upload_date.desc()).paginate(page=page, per_page=20)
    return render_template('admin_files.html', files=files)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role')
    department = request.args.get('department')
    status = request.args.get('status')
    search = request.args.get('search')
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    if department:
        query = query.filter_by(department=department)
    if status:
        query = query.filter_by(is_active=(status == 'active'))
    if search:
        query = query.filter(User.username.ilike(f'%{search}%'))
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin_users.html', users=users)

@app.route('/admin/activity')
@login_required
@admin_required
def admin_activity():
    page = request.args.get('page', 1, type=int)
    action = request.args.get('action')
    user_id = request.args.get('user')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = AccessLog.query
    
    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if date_from:
        query = query.filter(AccessLog.timestamp >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(AccessLog.timestamp <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    logs = query.order_by(AccessLog.timestamp.desc()).paginate(page=page, per_page=20)
    users = User.query.all()
    return render_template('admin_activity.html', logs=logs, users=users)

@app.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    # Get basic statistics
    total_users = User.query.count()
    total_files = File.query.count()
    total_storage = db.session.query(func.sum(File.file_size)).scalar() or 0
    
    # Get files by status
    files_by_status = db.session.query(
        File.status,
        func.count(File.id)
    ).group_by(File.status).all()
    files_by_status = dict(files_by_status)
    
    # Get users by role
    users_by_role = db.session.query(
        User.role,
        func.count(User.id)
    ).group_by(User.role).all()
    users_by_role = dict(users_by_role)
    
    # Get recent activity
    recent_activity = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin_stats.html',
                         total_users=total_users,
                         total_files=total_files,
                         total_storage=total_storage,
                         files_by_status=files_by_status,
                         users_by_role=users_by_role,
                         recent_activity=recent_activity)

@app.route('/admin/file/<int:file_id>/versions')
@login_required
@admin_required
def admin_file_versions(file_id):
    file = File.query.get_or_404(file_id)
    return render_template('admin_file_versions.html', file=file)

@app.route('/admin/file/<int:file_id>/access-logs')
@login_required
@admin_required
def admin_file_access_logs(file_id):
    file = File.query.get_or_404(file_id)
    logs = AccessLog.query.filter_by(file_id=file_id).order_by(AccessLog.timestamp.desc()).all()
    return render_template('admin_file_access_logs.html', file=file, logs=logs)

@app.route('/admin/user/<int:user_id>/activity')
@login_required
@admin_required
def admin_user_activity(user_id):
    user = User.query.get_or_404(user_id)
    logs = AccessLog.query.filter_by(user_id=user_id).order_by(AccessLog.timestamp.desc()).all()
    return render_template('admin_user_activity.html', user=user, logs=logs)

@app.route('/admin/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"User {user.username} has been {'activated' if user.is_active else 'deactivated'}.", 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/file/<int:file_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_file(file_id):
    file = File.query.get_or_404(file_id)
    try:
        # Delete file from storage
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        # Delete all versions
        for version in file.versions:
            if os.path.exists(version.file_path):
                os.remove(version.file_path)
            db.session.delete(version)
        
        # Delete file record
        db.session.delete(file)
        db.session.commit()
        
        flash('File deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('admin_files'))

@app.route('/admin/file/<int:file_id>/restore-version/<int:version_id>')
@login_required
@admin_required
def admin_restore_version(file_id, version_id):
    file = File.query.get_or_404(file_id)
    version = FileVersion.query.get_or_404(version_id)
    
    try:
        # Create new version from current file
        current_version = FileVersion(
            file=file,
            version_number=file.version + 1,
            file_hash=file.file_hash,
            file_path=file.file_path,
            created_by=current_user,
            change_description=f"Restored to version {version.version_number}"
        )
        
        # Restore file from version
        file.file_path = version.file_path
        file.file_hash = version.file_hash
        file.version += 1
        
        db.session.add(current_version)
        db.session.commit()
        
        flash('File version restored successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring version: {str(e)}', 'error')
    
    return redirect(url_for('admin_file_versions', file_id=file_id))

@app.route('/admin/file/<int:file_id>/add-tag', methods=['POST'])
@login_required
@admin_required
def admin_add_tag(file_id):
    file = File.query.get_or_404(file_id)
    tag_name = request.form.get('tag_name')
    
    if tag_name:
        tag = FileTag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = FileTag(name=tag_name)
            db.session.add(tag)
        
        if tag not in file.tags:
            file.tags.append(tag)
            db.session.commit()
            flash('Tag added successfully.', 'success')
        else:
            flash('Tag already exists on this file.', 'warning')
    else:
        flash('Tag name is required.', 'error')
    
    return redirect(url_for('admin_file_details', file_id=file_id))

@app.route('/admin/file/<int:file_id>/remove-tag/<int:tag_id>')
@login_required
@admin_required
def admin_remove_tag(file_id, tag_id):
    file = File.query.get_or_404(file_id)
    tag = FileTag.query.get_or_404(tag_id)
    
    if tag in file.tags:
        file.tags.remove(tag)
        db.session.commit()
        flash('Tag removed successfully.', 'success')
    else:
        flash('Tag not found on this file.', 'error')
    
    return redirect(url_for('admin_file_details', file_id=file_id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Create an admin user."""
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        click.echo("Admin user already exists!")
        return

    # Create admin user with a unique Ethereum address
    admin = User(
        username='admin',
        email='admin@example.com',
        role='admin',
        department='management',
        ethereum_address='0x9876543210987654321098765432109876543210'  # Different address
    )
    admin.set_password('admin123')  # Change this password in production!

    try:
        db.session.add(admin)
        db.session.commit()
        click.echo("Admin user created successfully!")
        click.echo("Username: admin")
        click.echo("Password: admin123")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error creating admin user: {str(e)}")

app.cli.add_command(create_admin_command)

from flask.cli import FlaskGroup

cli = FlaskGroup(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 