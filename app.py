import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy # <--- New Import

app = Flask(__name__)

# NEW BLOCK:
# This says: "Use the Render Database if available; otherwise, use my local file."
db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1) # Fix for a Render quirk

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///todo.db'
# 2. Create the Database Object
# This 'db' variable is our connection to the file
db = SQLAlchemy(app)

# This Class represents a single row in our database table
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    # NEW COLUMN: Defaults to False (Not done yet)
    is_completed = db.Column(db.Boolean, default=False) 

    def __repr__(self):
        return f'<Task {self.id}>'
# This is our temporary database (just a list in memory)


@app.route("/")
def home():
    # OLD: tasks = todos
    # NEW: Ask the database for ALL tasks
    tasks = Task.query.all() 
    # We pass the list of database objects to the template
    return render_template("index.html", tasks=tasks)
# ... (Keep the app.run part at the bottom)

@app.route("/add", methods=["POST"])
def add_task():
    content = request.form.get("task")
    if content:
        # 1. Create a new Task Object
        new_task = Task(content=content)
        
        # 2. Add it to the "Staging Area"
        db.session.add(new_task)
        
        # 3. Commit (Save) to the File
        db.session.commit()
        
    return redirect("/")
# The URL will look like: /delete/5
@app.route('/delete/<int:id>')
def delete_task(id):
    # 1. Find the task by its ID
    # .get_or_404() means: "Try to find it, but if it doesn't exist, show a generic Error page."
    task_to_delete = Task.query.get_or_404(id)

    # 2. Delete it from the staging area
    db.session.delete(task_to_delete)
    
    # 3. Commit the change to the file
    db.session.commit()
    
    # 4. Go back home
    return redirect('/')

@app.route('/toggle/<int:id>')
def toggle_task(id):
    task = Task.query.get_or_404(id)
    
    # The Toggle Logic: not True is False, not False is True.
    task.is_completed = not task.is_completed
    
    db.session.commit()
    return redirect('/')

if __name__ == "__main__":
    # This block runs only once when you start the server
    with app.app_context():
        db.create_all() # <--- This magic line creates the DB file!
        print("Included the database!") # Just a sanity check for us
    app.run(debug=True)