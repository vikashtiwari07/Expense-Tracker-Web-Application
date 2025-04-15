from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
from fpdf import FPDF
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database setup
def get_db_connection():
    conn = sqlite3.connect('expense_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ExpenseTracker (
            ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
            Date DATETIME, 
            Payee TEXT, 
            Description TEXT, 
            Amount FLOAT, 
            ModeOfPayment TEXT,
            UserID INTEGER
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT, 
            Username TEXT UNIQUE, 
            Password TEXT, 
            Email TEXT, 
            JoinDate DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Authentication routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE Username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['Password'], password):
            session['user_id'] = user['ID']
            session['username'] = user['Username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        join_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO Users (Username, Password, Email, JoinDate) VALUES (?, ?, ?, ?)',
                        (username, hashed_password, email, join_date))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists', 'error')
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Main application routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM ExpenseTracker WHERE UserID = ? ORDER BY Date DESC', 
                          (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', expenses=expenses, datetime=datetime)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    date = request.form['date']
    payee = request.form['payee']
    description = request.form['description']
    amount = float(request.form['amount'])
    mode_of_payment = request.form['mode_of_payment']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO ExpenseTracker (Date, Payee, Description, Amount, ModeOfPayment, UserID) VALUES (?, ?, ?, ?, ?, ?)',
                (date, payee, description, amount, mode_of_payment, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Expense added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM ExpenseTracker WHERE ID = ? AND UserID = ?', 
                (expense_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        date = request.form['date']
        payee = request.form['payee']
        description = request.form['description']
        amount = float(request.form['amount'])
        mode_of_payment = request.form['mode_of_payment']
        
        conn.execute('''UPDATE ExpenseTracker SET 
                      Date = ?, Payee = ?, Description = ?, Amount = ?, ModeOfPayment = ?
                      WHERE ID = ? AND UserID = ?''',
                   (date, payee, description, amount, mode_of_payment, expense_id, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    expense = conn.execute('SELECT * FROM ExpenseTracker WHERE ID = ? AND UserID = ?',
                          (expense_id, session['user_id'])).fetchone()
    conn.close()
    
    if not expense:
        flash('Expense not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_expense.html', expense=expense, datetime=datetime)

# Reporting routes
@app.route('/generate_pdf_report')
def generate_pdf_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM ExpenseTracker WHERE UserID = ?', 
                          (session['user_id'],)).fetchall()
    conn.close()
    
    if not expenses:
        flash('No expenses to generate report', 'error')
        return redirect(url_for('dashboard'))
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.cell(200, 10, txt="Expense Tracker - Monthly Report", ln=1, align='C')
    pdf.ln(10)
    
    # Date
    pdf.cell(200, 10, txt=f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("Arial", 'B', size=10)
    pdf.cell(15, 10, "ID", border=1)
    pdf.cell(25, 10, "Date", border=1)
    pdf.cell(40, 10, "Payee", border=1)
    pdf.cell(80, 10, "Description", border=1)
    pdf.cell(25, 10, "Amount", border=1)
    pdf.cell(25, 10, "Payment Mode", border=1, ln=1)
    
    # Table Data
    pdf.set_font("Arial", size=10)
    total = 0
    for expense in expenses:
        pdf.cell(15, 10, str(expense['ID']), border=1)
        pdf.cell(25, 10, expense['Date'], border=1)
        pdf.cell(40, 10, expense['Payee'], border=1)
        pdf.cell(80, 10, expense['Description'], border=1)
        pdf.cell(25, 10, f"${expense['Amount']:.2f}", border=1)
        pdf.cell(25, 10, expense['ModeOfPayment'], border=1, ln=1)
        total += expense['Amount']
    
    # Total
    pdf.ln(5)
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(180, 10, f"Total Expenses: ${total:.2f}", ln=1, align='R')
    
    # Save PDF to memory
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    
    return send_file(
        pdf_output,
        as_attachment=True,
        download_name=f"expense_report_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

@app.route('/export_to_excel')
def export_to_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM ExpenseTracker WHERE UserID = ?', 
                          (session['user_id'],)).fetchall()
    conn.close()
    
    if not expenses:
        flash('No expenses to export', 'error')
        return redirect(url_for('dashboard'))
    
    # Create DataFrame
    data = []
    for expense in expenses:
        data.append({
            'ID': expense['ID'],
            'Date': expense['Date'],
            'Payee': expense['Payee'],
            'Description': expense['Description'],
            'Amount': expense['Amount'],
            'Mode of Payment': expense['ModeOfPayment']
        })
    
    df = pd.DataFrame(data)
    
    # Save Excel to memory
    excel_output = io.BytesIO()
    with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
    excel_output.seek(0)
    
    return send_file(
        excel_output,
        as_attachment=True,
        download_name=f"expenses_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    app.run(debug=True)