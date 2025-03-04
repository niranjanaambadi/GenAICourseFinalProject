from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # For session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite DB for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # 'user' or 'admin'

# Initialize the database
with app.app_context():
    db.create_all()

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route for Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Simple check (in production, hash the password)
            login_user(user)
            session['username'] = username
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        
        # Check if the user already exists
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('User already exists', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, password=password, email=email, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User Dashboard (Accessed by normal users)
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', user=current_user)


# Admin Dashboard (Accessed by admins only)
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    # Fetch all users for the admin to manage
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

# Edit user (Admin functionality)
@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    user = User.query.get(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        db.session.commit()
        flash('User details updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_user.html', user=user)

# Delete user (Admin functionality)
@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('login'))

# Route to handle adding a new project
@app.route('/add_projectgit', methods=['GET', 'POST'])
def add_projectgit():
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))  # Redirect to login if user is not authenticated
    
    if request.method == 'POST':
        title = request.form['title']
        github_url = request.form['github_url']

        # Create a new project and add it to the database
        new_project = Project(title=title, github_url=github_url)
        db.session.add(new_project)
        db.session.commit()
        
        flash('New project added successfully!', 'success')
        return redirect(url_for('user_dashboard'))  # Redirect back to user landing page
    
    return render_template('add_projectgit.html')

import os
import zipfile
from werkzeug.utils import secure_filename

# Define allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'zip'}

# Define the upload folder
UPLOAD_FOLDER = 'uploads'  # You can change this to any path you prefer
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if the uploaded file is a ZIP
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))  # Redirect to login if user is not authenticated
    
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['file']

        # Check if a file is selected
        if file and allowed_file(file.filename):
            # Secure the file name
            filename = secure_filename(file.filename)
            project_folder = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Create the upload folder if it doesn't exist
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            # Save the file
            file.save(project_folder)

            # Extract the ZIP file
            with zipfile.ZipFile(project_folder, 'r') as zip_ref:
                extract_folder = os.path.join(app.config['UPLOAD_FOLDER'], title)  # Folder where contents will be extracted
                if not os.path.exists(extract_folder):
                    os.makedirs(extract_folder)
                zip_ref.extractall(extract_folder)  # Extract all contents

            # List the files in the extracted folder
            project_files = []
            for root, dirs, files in os.walk(extract_folder):
                for file in files:
                    project_files.append(os.path.join(root, file))  # Full path to the file

            # Add the project to the database (with the path to the extracted folder)
            new_project = Project(title=title, folder_path=extract_folder)
            db.session.add(new_project)
            db.session.commit()

            flash('New project added successfully!', 'success')
            return redirect(url_for('user_dashboard'))  # Redirect back to user landing page
    
    return render_template('add_project.html')

@app.route('/view_project/<project_id>', methods=['GET'])
def view_project(project_id):
    project = Project.query.get(project_id)
    if project is None:
        flash("Project not found.", 'danger')
        return redirect(url_for('user_dashboard'))

    # List files in the project folder
    project_files = []
    for root, dirs, files in os.walk(project.folder_path):
        for file in files:
            project_files.append(os.path.join(root, file))

    return render_template('view_project.html', project=project, project_files=project_files)


if __name__ == '__main__':
    app.run(debug=True)
