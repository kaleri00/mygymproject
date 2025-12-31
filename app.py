import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'database.db')

# --- EMAIL CONFIGURATION ---
# IMPORTANT: For Gmail, you MUST use an "App Password" (16-character code)
# if you have 2-Step Verification enabled. 
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "engrrabdulkhaliq@gmail.com" 
MAIL_PASSWORD = "oordsaffhezviqsb"  # User's provided password/placeholder
RECIPIENT_EMAIL = "engrrabdulkhaliq@gmail.com"

def send_email_notification(name, email, phone, message):
    try:
        subject = f"New Contact Form: {name}"
        
        # Professional Email Body
        body = f"""
New Form Submission Received

Details:
-------------------------
Name:    {name}
Email:   {email}
Phone:   {phone}
Message: {message}

-------------------------
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        msg = MIMEMultipart()
        msg['From'] = MAIL_USERNAME
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and Send
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        server.set_debuglevel(0)
        server.starttls() # Secure the connection
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
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
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    message = request.form.get('message')

    # Basic server-side validation
    if not name or not email or not phone or not message:
        flash("All fields are required!", "error")
        return redirect(url_for('contact'))

    try:
        # DB save
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO contacts (name, email, phone, message) VALUES (?, ?, ?, ?)',
            (name, email, phone, message)
        )
        conn.commit()
        conn.close()

        # Send Email
        print("Attempting to send email...")
        email_sent = send_email_notification(name, email, phone, message)
        print("Email sent?", email_sent)

        # Redirect
        return redirect(url_for('success'))

    except Exception as e:
        print("=== ERROR DETAIL ===")
        import traceback
        traceback.print_exc()  # full traceback
        flash(f"An unexpected error occurred: {e}", "error")
        return redirect(url_for('contact'))

@app.route('/admin')
def admin():
    conn = get_db_connection()
    contacts = conn.execute('SELECT * FROM contacts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin.html', contacts=contacts)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
    
