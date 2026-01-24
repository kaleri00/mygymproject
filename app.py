import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'gym_system.db')

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'engrrabdulkhaliq@gmail.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'oordsaffhezviqsb')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'engrrabdulkhaliq@gmail.com')

ADMIN_USERNAME = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASS', 'admin123'))

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    cleaned = re.sub(r'[^\d+]', '', phone)
    return len(cleaned) >= 10

def sanitize_input(text):
    if not text:
        return ""
    return text.strip()[:500]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash("Please login to access admin panel", "error")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def send_email_notification(name, email, phone, message):
    try:
        subject = f"New Inquiry from {name}"
        
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        NEW CONTACT FORM SUBMISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Full Name:     {name}
Email Address: {email}
Phone Number:  {phone}

Message:
{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Submitted: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification from your Gym Contact System.
        """
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Gym System <{MAIL_USERNAME}>"
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        app.logger.error(f"Email Error: {str(e)}")
        return False

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    conn = get_db_connection()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_contacts_created 
        ON contacts(created_at DESC)
    ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_contacts_status 
        ON contacts(status)
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = sanitize_input(request.form.get('name'))
    email = sanitize_input(request.form.get('email'))
    phone = sanitize_input(request.form.get('phone'))
    message = sanitize_input(request.form.get('message'))
    
    if not all([name, email, phone, message]):
        flash("All fields are required", "error")
        return redirect(url_for('contact'))
    
    if not validate_email(email):
        flash("Please enter a valid email address", "error")
        return redirect(url_for('contact'))
    
    if not validate_phone(phone):
        flash("Please enter a valid phone number", "error")
        return redirect(url_for('contact'))
    
    try:
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')[:200]
        
        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO contacts 
               (name, email, phone, message, ip_address, user_agent) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (name, email, phone, message, ip_address, user_agent)
        )
        conn.commit()
        conn.close()
        
        send_email_notification(name, email, phone, message)
        
        flash("Thank you! Your message has been received.", "success")
        return redirect(url_for('success'))
        
    except Exception as e:
        app.logger.error(f"Submission Error: {str(e)}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for('contact'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            session['username'] = username
            flash("Login successful", "success")
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials", "error")
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    contacts = conn.execute(
        'SELECT * FROM contacts ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    
    return render_template('admin.html', contacts=contacts)

@app.route('/admin/contact/<int:contact_id>/status', methods=['POST'])
@login_required
def update_status(contact_id):
    status = request.form.get('status', 'new')
    
    conn = get_db_connection()
    conn.execute('UPDATE contacts SET status = ? WHERE id = ?', (status, contact_id))
    conn.commit()
    conn.close()
    
    flash("Status updated", "success")
    return redirect(url_for('admin'))

@app.route('/admin/contact/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
    conn.commit()
    conn.close()
    
    flash("Contact deleted", "success")
    return redirect(url_for('admin'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
