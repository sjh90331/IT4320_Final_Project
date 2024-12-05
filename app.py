from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  

def get_cost_matrix():
    cost_matrix = [[100, 75, 50, 100] for row in range(12)]
    return cost_matrix

def get_db_connection():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_eticket(first_name):
    template = "IT4320"
    result = ""
    name_index = 0
    template_index = 0
    
    while name_index < len(first_name) or template_index < len(template):
        if name_index < len(first_name):
            result += first_name[name_index]
            name_index += 1
        if template_index < len(template):
            result += template[template_index]
            template_index += 1
    return result

def get_seating_chart():
    conn = get_db_connection()
    reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
    conn.close()
    
    # Initialize seating chart with 'O's
    chart = [['O' for _ in range(4)] for _ in range(12)]
    
    # Mark reserved seats with 'X'
    for res in reservations:
        chart[res['seatRow'] - 1][res['seatColumn'] - 1] = 'X'
    
    return chart

def calculate_total_sales():
    conn = get_db_connection()
    reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
    conn.close()
    
    cost_matrix = get_cost_matrix()
    total = 0
    for res in reservations:
        row = res['seatRow'] - 1
        col = res['seatColumn'] - 1
        total += cost_matrix[row][col]
    
    return total

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/choose_action', methods=['POST'])
def choose_action():
    action = request.form.get('action')
    if not action:
        flash('You must select a valid option')
        return redirect(url_for('index'))
    
    if action == 'admin':
        return redirect(url_for('admin_login'))
    else:
        return redirect(url_for('reserve_seat'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('All fields are required')
            return redirect(url_for('admin_login'))
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
        conn.close()
        
        if admin:
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username/password combination')
            
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    seating_chart = get_seating_chart()
    total_sales = calculate_total_sales()
    return render_template('admin_dashboard.html', 
                         seating_chart=seating_chart, 
                         total_sales=total_sales)

@app.route('/reserve_seat', methods=['GET', 'POST'])
def reserve_seat():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        seat_row = request.form.get('seat_row')
        seat_column = request.form.get('seat_column')
        
        if not all([first_name, last_name, seat_row, seat_column]):
            flash('All fields are required')
            return redirect(url_for('reserve_seat'))
        
        try:
            seat_row = int(seat_row)
            seat_column = int(seat_column)
            if not (1 <= seat_row <= 12 and 1 <= seat_column <= 4):
                raise ValueError
        except ValueError:
            flash('Invalid seat selection')
            return redirect(url_for('reserve_seat'))
        
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM reservations WHERE seatRow = ? AND seatColumn = ?',
                              (seat_row, seat_column)).fetchone()
        
        if existing:
            conn.close()
            flash(f'Row {seat_row} seat {seat_column} is already assigned. Choose again.')
            return redirect(url_for('reserve_seat'))
        
        passenger_name = f"{first_name} {last_name}"
        eticket = generate_eticket(first_name)
        
        conn.execute('INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)',
                    (passenger_name, seat_row, seat_column, eticket))
        conn.commit()
        conn.close()
        
        flash(f'Congratulations {passenger_name}! Row {seat_row} seat {seat_column} is now reserved for you. '
              f'Enjoy your trip! Your E-ticket number is: {eticket}')
        
    seating_chart = get_seating_chart()
    return render_template('reserve_seat.html', seating_chart=seating_chart)

if __name__ == '__main__':
    app.run(debug=True)
