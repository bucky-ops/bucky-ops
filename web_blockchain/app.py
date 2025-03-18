from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from blockchain import Blockchain
import uuid
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blockchain.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

blockchain = Blockchain()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    wallet_address = db.Column(db.String(120), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(120), unique=True, nullable=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(120), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html', blockchain=blockchain)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # In production, use proper password hashing
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        wallet_address = str(uuid.uuid4()).replace('-', '')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        user = User(username=username, password=password, wallet_address=wallet_address)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    users = User.query.all() if current_user.is_admin else None
    return render_template('dashboard.html', user=current_user, blockchain=blockchain, users=users)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    if new_password:
        user.password = new_password  # In production, use proper password hashing
        db.session.commit()
        flash(f'Password reset for user {user.username}')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create_user', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('admin_dashboard'))
        
    wallet_address = str(uuid.uuid4()).replace('-', '')
    user = User(username=username, password=password, wallet_address=wallet_address, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()
    flash(f'User {username} created successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/send_coins', methods=['POST'])
@login_required
def send_coins():
    recipient_username = request.form.get('recipient_username')
    amount = float(request.form.get('amount'))
    
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        flash('Recipient user not found')
        return redirect(url_for('dashboard'))
        
    if amount > current_user.balance:
        flash('Insufficient balance')
        return redirect(url_for('dashboard'))
        
    blockchain.add_transaction(current_user.wallet_address, recipient.wallet_address, amount)
    current_user.balance -= amount
    recipient.balance += amount
    
    transaction = Transaction(
        sender=current_user.wallet_address,
        recipient=recipient.wallet_address,
        amount=amount,
        user_id=current_user.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Successfully sent {amount} coins to {recipient_username}')
    return redirect(url_for('dashboard'))

@app.route('/mine', methods=['GET'])
@login_required
def mine():
    blockchain.mine_pending_transactions(current_user.wallet_address)
    current_user.balance += blockchain.mining_reward
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password='admin123',  # Change this in production
                wallet_address=str(uuid.uuid4()).replace('-', ''),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True) 