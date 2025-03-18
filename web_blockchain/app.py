from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from blockchain import Blockchain
import uuid
from datetime import datetime
import os

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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    wallet_address = db.Column(db.String(120), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
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
    return render_template('dashboard.html', user=current_user, blockchain=blockchain)

@app.route('/mine', methods=['GET'])
@login_required
def mine():
    blockchain.mine_pending_transactions(current_user.wallet_address)
    current_user.balance += blockchain.mining_reward
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/transaction/new', methods=['POST'])
@login_required
def new_transaction():
    recipient = request.form.get('recipient')
    amount = float(request.form.get('amount'))
    
    if amount > current_user.balance:
        flash('Insufficient balance')
        return redirect(url_for('dashboard'))
        
    blockchain.add_transaction(current_user.wallet_address, recipient, amount)
    current_user.balance -= amount
    
    transaction = Transaction(
        sender=current_user.wallet_address,
        recipient=recipient,
        amount=amount,
        user_id=current_user.id
    )
    db.session.add(transaction)
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
    app.run(host='0.0.0.0', port=5000, debug=True) 