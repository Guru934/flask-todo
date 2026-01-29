import os
from datetime import date
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- 1. CONFIGURATION ---
app.secret_key = "change_this_to_something_secret"

# Database Config
db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 2. LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 3. DATABASE MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    
    # NEW COLUMNS
    priority = db.Column(db.String(20), default='Medium')
    deadline = db.Column(db.Date, nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.id}>'

# --- 4. MAIN ROUTES ---

@app.route("/")
def home():
    if not current_user.is_authenticated:
        return render_template("index.html", tasks=[])
    
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", tasks=user_tasks)

@app.route("/add", methods=["POST"])
@login_required 
def add_task():
    content = request.form.get("task")
    priority = request.form.get("priority")
    deadline_str = request.form.get("deadline")
    
    if content:
        # Date Logic
        deadline_obj = None
        if deadline_str:
            try:
                y, m, d = map(int, deadline_str.split('-'))
                deadline_obj = date(y, m, d)
            except ValueError:
                pass # If date format is bad, just ignore it

        new_task = Task(
            content=content, 
            owner=current_user,
            priority=priority,
            deadline=deadline_obj
        )
        
        db.session.add(new_task)
        db.session.commit()
    return redirect("/")

@app.route('/delete/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect('/')

@app.route('/toggle/<int:id>')
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect('/')

# --- 5. AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists!")
            return redirect('/register')
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect('/')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        else:
            flash("Invalid username or password")
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)