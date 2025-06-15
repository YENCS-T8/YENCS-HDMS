from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,session,url_for
from datetime import datetime
import mysql.connector
import config
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

def get_db_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )


activity_log = [
    f"{datetime.now().strftime('%H:%M:%S')} - System initialized",
    f"{datetime.now().strftime('%H:%M:%S')} - Blood bank data loaded",
    f"{datetime.now().strftime('%H:%M:%S')} - OT schedules updated",
    f"{datetime.now().strftime('%H:%M:%S')} - Patient queues synchronized"
]

notifications = []

def role_required(allowed_roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"User role: {session.get('role')}, allowed: {allowed_roles}")
            if 'role' not in session or session['role'] not in allowed_roles:
                return redirect(url_for('unauthorized'))  # Or return render_template('unauthorized.html')
            return f(*args, **kwargs)
        return decorated_function
    return wrapper


conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

users = [
    ('admin', 'admin123', 'admin'),
    ('bloodstaff', 'blood123', 'blood_bank'),
    ('receptionist1', 'recep123', 'receptionist'),
    ('pharmacystaff', 'pharma123', 'pharmacy')
]


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pword = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (uname,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and user['password'] == pword:
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))



# --- Dashboard ---
@app.route('/')
@role_required(['admin', 'receptionist', 'blood_bank', 'pharmacy'])
def dashboard():
    user_role = session.get('role')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    alerts = []
    stats = {}
    notifications_data = []
    activity_log_data = []

    try:
        # --- Critical Alerts (Admin & Relevant Roles) ---
        if user_role in ['admin', 'blood_bank']:
            cursor.execute("SELECT type, units, critical_level FROM blood_bank WHERE units < critical_level")
            for b in cursor.fetchall():
                status = "out of stock" if b['units'] == 0 else "critical"
                alerts.append(f"🩸 Blood Alert: {b['type']} is {status} ({b['units']} / {b['critical_level']})")

        if user_role in ['admin', 'pharmacy']:
            cursor.execute("SELECT name, stock, reorder_level FROM pharmacy WHERE stock <= reorder_level")
            for d in cursor.fetchall():
                status = "out of stock" if d['stock'] == 0 else "low stock"
                alerts.append(f"💊 Drug Alert: {d['name']} is {status} (Stock: {d['stock']} / Reorder: {d['reorder_level']})")

        if user_role in ['admin', 'receptionist']:
            cursor.execute("SELECT code, dept FROM emergency_alert WHERE status='Active'")
            for e in cursor.fetchall():
                alerts.append(f"🚨 EMERGENCY: {e['code']} in {e['dept']}")

        if not alerts:
            alerts.append("✅ No critical alerts at this time")

        # --- Stats (Role-based) ---
        if user_role in ['admin', 'receptionist']:
            cursor.execute("SELECT COUNT(*) AS cnt FROM ot_schedule WHERE status='In Progress'")
            active_ots = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) AS cnt FROM ot_schedule")
            total_ots = cursor.fetchone()['cnt']
            stats['active_ots'] = f"{active_ots}/{total_ots}"

            cursor.execute("SELECT COUNT(*) AS cnt FROM patient_queue WHERE status='Waiting'")
            stats['patients_in_queue'] = cursor.fetchone()['cnt']

        if user_role in ['admin', 'blood_bank']:
            cursor.execute("SELECT COUNT(*) AS cnt FROM blood_bank WHERE units < critical_level")
            stats['critical_blood'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT SUM(units) AS total_units FROM blood_bank")
            stats['total_units'] = cursor.fetchone()['total_units'] or 0

        if user_role in ['admin', 'pharmacy']:
            cursor.execute("SELECT COUNT(*) AS cnt FROM pharmacy WHERE stock <= reorder_level")
            stats['low_stock_drugs'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) AS cnt FROM pharmacy")
            stats['total_medicines'] = cursor.fetchone()['cnt']

        # --- Notifications (Admin only) ---
        if user_role == 'admin':
            cursor.execute("SELECT message, status FROM notification ORDER BY id DESC LIMIT 10")
            notifications_data = cursor.fetchall()

        # --- Activity Log (Admin only) ---
        if user_role == 'admin':
            cursor.execute("SELECT message, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT 20")
            rows = cursor.fetchall()
            activity_log_data = [
                f"[{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] {row['message']}" 
                for row in rows
            ]

    except Exception as e:
        print(f"Dashboard error: {e}")
        alerts = ["❌ Error loading dashboard data."]
        stats = {
            "active_ots": "N/A", "critical_blood": "N/A",
            "patients_in_queue": "N/A", "low_stock_drugs": "N/A"
        }
        notifications_data = [{"message": "Error loading notifications.", "status": ""}]
        activity_log_data = ["Error loading activity log."]
    finally:
        cursor.close()
        conn.close()

    return render_template('dashboard.html',
        alerts=alerts,
        stats=stats,
        notifications=notifications_data,
        activity_log=activity_log_data,
        user_role=user_role
    )

# --- Activity Log ---
@app.route('/add_activity', methods=['POST'])
@role_required(['admin', 'receptionist'])
def add_activity():
    activity = request.form.get('activity')
    if activity:
        timestamp = datetime.now().strftime("%H:%M:%S")
        activity_log.append(f"{timestamp} - {activity}")
        if len(activity_log) > 50:
            activity_log[:] = activity_log[-50:]
    return redirect(url_for('dashboard'))



# --- Emergency Management ---
@app.route('/emergency', methods=['GET', 'POST'])
@role_required(['admin', 'receptionist'])
def emergency():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        code = request.form['code']
        color = request.form['color']
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dept = "General"
        status = "Active"

        cursor.execute(
            "INSERT INTO emergency_alert (code, color, dept, time, status) VALUES (%s, %s, %s, %s, %s)",
            (code, color, dept, time, status)
        )
        conn.commit()

    cursor.execute("SELECT * FROM emergency_alert ORDER BY time DESC")
    emergency_alerts = cursor.fetchall()

    cursor.execute("SELECT * FROM code_definitions")
    code_definitions = cursor.fetchall()

    conn.close()

    return render_template("emergency.html", emergency_alerts=emergency_alerts, code_definitions=code_definitions)



@app.route('/clear_emergency/<int:alert_id>')
@role_required(['admin', 'receptionist'])
def clear_emergency(alert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE emergency_alert SET status = 'Resolved' WHERE id = %s", (alert_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('emergency'))

@app.route('/emergency_block_ot')
@role_required(['admin', 'receptionist'])
def emergency_block_ot():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE ot SET status = 'Blocked' WHERE status != 'Completed'")
    conn.commit()
    conn.close()
    return redirect(url_for('ot'))


@app.route('/add_code', methods=['POST'])
@role_required(['admin', 'receptionist'])
def add_code():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    code_name = request.form['code_name']
    description = request.form['description']
    color = request.form['color']

    cursor.execute("INSERT INTO code_definitions (code_name, description, color) VALUES (%s, %s, %s)",
                   (code_name, description, color))
    conn.commit()
    conn.close()
    
    return redirect(url_for('emergency'))



# -------------------- OT Dashboard --------------------
@app.route('/ot')
@role_required(['admin', 'receptionist'])
def ot():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get OT department ID
    cursor.execute("SELECT id FROM departments WHERE name = 'Orthopedics'")
    dept_row = cursor.fetchone()
    ot_dept_id = dept_row['id'] if dept_row else None

    if not ot_dept_id:
        cursor.close()
        conn.close()
        return "OT department not found", 500

    # Get token list for OT
    cursor.execute("""
        SELECT pq.*, d.name AS department_name 
        FROM patient_queue pq
        JOIN departments d ON pq.department_id = d.id
        WHERE pq.department_id = %s
        ORDER BY pq.token_number ASC
    """, (ot_dept_id,))
    ot_tokens = cursor.fetchall()

    # Current Token
    current_token = next((t for t in ot_tokens if t['status'] == 'In Progress'), None)

    # OT Schedule
    cursor.execute("SELECT * FROM ot_schedule ORDER BY scheduled_time ASC")
    ot_schedule = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("ot.html", 
        ot_tokens=ot_tokens, 
        ot_schedule=ot_schedule, 
        current_token=current_token
    )




# -------------------- Add Patient to OT Queue --------------------
@app.route('/add_ot_patient', methods=['POST'])
@role_required(['admin', 'receptionist'])
def add_ot_patient():
    conn = get_db_connection()
    cursor = conn.cursor()

    name = request.form['patient_name']
    surgeon = request.form['surgeon']
    time = request.form['scheduled_time']

    # Get OT department ID
    cursor.execute("SELECT id FROM departments WHERE name = 'Orthopedics'")
    dept_row = cursor.fetchone()
    ot_dept_id = dept_row[0] if dept_row else None

    if not ot_dept_id:
        cursor.close()
        conn.close()
        return "OT department not found", 400

    # Get next token number
    cursor.execute("SELECT MAX(token_number) FROM patient_queue WHERE department_id = %s", (ot_dept_id,))
    last_token = cursor.fetchone()[0]
    next_token = (last_token or 0) + 1

    cursor.execute("""
        INSERT INTO patient_queue 
        (patient_name, department_id, doctor_or_surgeon, token_number, scheduled_time, status) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, ot_dept_id, surgeon, next_token, time, 'Waiting'))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Patient added to OT queue.")
    return redirect(url_for('ot'))


# -------------------- Update OT Schedule Status --------------------
@app.route('/update_ot_status/<int:schedule_id>', methods=['POST'])
@role_required(['admin', 'receptionist'])
def update_ot_status(schedule_id):
    new_status = request.form.get('new_status')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE ot_schedule SET status = %s WHERE id = %s", (new_status, schedule_id))
    conn.commit()
    conn.close()
    flash("OT Schedule status updated.", "success")
    return redirect(url_for('ot'))  # Replace with your actual OT dashboard route



# -------------------- Update Token Status --------------------
@app.route('/update_token_status/<int:token_number>', methods=['POST'])
@role_required(['admin', 'receptionist'])
def update_token_status(token_number):
    new_status = request.form.get('new_status')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get OT department ID
    cursor.execute("SELECT id FROM departments WHERE name = 'Orthopedics'")
    dept_row = cursor.fetchone()
    ot_dept_id = dept_row[0] if dept_row else None

    if not ot_dept_id:
        cursor.close()
        conn.close()
        return "OT department not found", 400

    # Update selected token
    cursor.execute("""
        UPDATE patient_queue 
        SET status = %s 
        WHERE token_number = %s AND department_id = %s
    """, (new_status, token_number, ot_dept_id))
    conn.commit()

    # If completed, move next waiting token to "In Progress"
    if new_status == 'Completed':
        # Ensure no other token is in progress
        cursor.execute("""
            UPDATE patient_queue 
            SET status = 'Waiting' 
            WHERE status = 'In Progress' AND department_id = %s
        """, (ot_dept_id,))
        conn.commit()

        # Promote next waiting token
        cursor.execute("""
            SELECT token_number FROM patient_queue 
            WHERE status = 'Waiting' AND department_id = %s 
            ORDER BY token_number ASC LIMIT 1
        """, (ot_dept_id,))
        next_token = cursor.fetchone()

        if next_token:
            cursor.execute("""
                UPDATE patient_queue 
                SET status = 'In Progress' 
                WHERE token_number = %s AND department_id = %s
            """, (next_token[0], ot_dept_id))
            conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('ot'))


@app.route('/schedule_ot', methods=['POST'])
@role_required(['admin', 'receptionist'])
def schedule_ot():
    patient_name = request.form['patient_name']
    surgeon_name = request.form['surgeon_name']
    description = request.form['description']
    scheduled_date = request.form['scheduled_date']
    scheduled_time = request.form['scheduled_time']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ot_schedule 
        (patient_name, surgeon_name, description, scheduled_date, scheduled_time)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_name, surgeon_name, description, scheduled_date, scheduled_time))

    conn.commit()
    cursor.close()
    conn.close()

    flash("OT scheduled successfully.")
    return redirect(url_for('ot'))





# -------------------- AJAX Refresh for Token Queue --------------------
@app.route('/get_ot_tokens')
@role_required(['admin', 'receptionist'])
def get_ot_tokens():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM departments WHERE name = 'OT'")
    dept_row = cursor.fetchone()
    ot_dept_id = dept_row['id'] if dept_row else None

    if not ot_dept_id:
        cursor.close()
        conn.close()
        return "Department not found", 400

    cursor.execute("""
        SELECT pq.*, d.name AS department_name 
        FROM patient_queue pq
        JOIN departments d ON pq.department_id = d.id
        WHERE pq.department_id = %s
        ORDER BY pq.token_number
    """, (ot_dept_id,))
    ot_tokens = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('partials/ot_tokens_fragment.html', ot_tokens=ot_tokens)




# ---------------------- Consultation Schedule ----------------------
@app.route('/consultation_schedule', methods=['GET', 'POST'])
@role_required(['admin', 'receptionist'])
def consultation_schedule():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        doctor = request.form['doctor']
        specialization = request.form['specialization']
        date = request.form['date']
        start = request.form['start_time']
        end = request.form['end_time']
        room = request.form['room_no']

        cursor.execute('''INSERT INTO consultation_schedule
            (doctor_name, specialization, date, start_time, end_time, room_no)
            VALUES (%s, %s, %s, %s, %s, %s)''',
            (doctor, specialization, date, start, end, room))
        conn.commit()

    cursor.execute("SELECT * FROM consultation_schedule ORDER BY date, start_time")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("consultation_schedule.html", schedule=data)


# --- Blood Bank ---
# Route for blood bank
@app.route('/blood', methods=['GET', 'POST'])
@role_required(['admin', 'blood_bank', 'receptionist'])
def blood():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch blood bank records
    cursor.execute("SELECT * FROM blood_bank")
    rows = cursor.fetchall()

    blood_data = {}
    for row in rows:
        status = "Sufficient"
        if row['units'] < row['critical_level']: # <-- This is where the threshold is checked
            status = "Critical"
        blood_data[row['blood_id']] = {
            'type': row['type'],
            'units': row['units'],
            'critical': row['critical_level'],
            'status': status
        }

    # Handle stock addition for critical blood types
    if request.method == 'POST':
        for blood_id, data in blood_data.items():
            if data['status'] == 'Critical':
                cursor.execute("UPDATE blood_bank SET units = units + 1 WHERE blood_id = %s", (blood_id,))
        conn.commit()
        flash("1 unit added to each critical blood type.")
        return redirect(url_for('blood'))

    conn.close()
    return render_template("blood.html", blood_data=blood_data)

# Route to issue blood
@app.route('/issue_blood/<int:blood_id>')
@role_required(['admin', 'blood_bank', 'receptionist'])
def issue_blood(blood_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE blood_bank SET units = units - 1 WHERE blood_id = %s AND units > 0", (blood_id,))
    conn.commit()
    conn.close()
    flash("1 unit issued.")
    return redirect(url_for('blood'))

# Route to send critical alert (placeholder)
# --- Blood Bank ---
# (Keep your existing /blood, /issue_blood, /add_specific_blood_stock routes as they are)

# Route to send critical alert (already exists, but enhance its message)
@app.route('/blood_critical_alert')
@role_required(['admin', 'blood_bank', 'receptionist'])
def blood_critical_alert():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    critical_blood_types = []
    try:
        # Select blood types where current units are less than the critical_level
        cursor.execute("SELECT type, units, critical_level FROM blood_bank WHERE units < critical_level")
        critical_blood_types = cursor.fetchall()
        
        if critical_blood_types:
            alert_messages = []
            for item in critical_blood_types:
                # Determine status more precisely if needed, though 'Critical' is implied here
                status_description = "Critical" 
                if item['units'] == 0:
                    status_description = "Extremely Critical (Out of Stock!)"

                alert_messages.append(
                    f"{status_description}: {item['type']} blood (Current: {item['units']} units, Critical Level: {item['critical_level']} units)"
                )
            
            full_alert_message = f"🚨 URGENT BLOOD ALERT: {len(critical_blood_types)} blood type(s) are in critical stock! " \
                                 f"Details: {'; '.join(alert_messages)}"
            flash(full_alert_message, "danger") # Use "danger" for critical alerts
            log_activity(f"Sent critical blood stock alert for {len(critical_blood_types)} type(s).")
        else:
            flash("All blood types are sufficiently stocked. No critical alerts.", "success")
            log_activity("Checked blood stock; all types are sufficient.")

    except Exception as e:
        flash(f"Error checking critical blood levels: {e}", "danger")
        log_activity(f"Error checking critical blood levels: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('blood')) # Redirect back to the blood bank main page



# In your app.py
# Add this new route for adding specific blood stock
@app.route('/add_specific_blood_stock', methods=['POST'])
@role_required(['admin', 'blood_bank','receptionist'])
def add_specific_blood_stock():
    blood_id = request.form.get('blood_id')
    units_to_add = request.form.get('units_to_add', type=int) # Note: changed name to match new form field

    if not blood_id or units_to_add is None or units_to_add <= 0:
        flash("Invalid blood type or units to add. Please select a blood type and enter a positive number.", "danger")
        return redirect(url_for('blood'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE blood_bank SET units = units + %s WHERE blood_id = %s", (units_to_add, blood_id))
        if cursor.rowcount == 0:
            flash(f"Blood type ID '{blood_id}' not found. No stock added.", "warning")
        else:
            conn.commit()
            # Log the activity (assuming log_activity is defined as discussed)
            log_activity(f"Added {units_to_add} units to blood type {blood_id}.")
            flash(f"{units_to_add} units added to blood type {blood_id}.", "success")
    except Exception as e:
        conn.rollback() # Rollback changes if an error occurs
        flash(f"Error adding blood stock: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('blood'))

# Remember to also include the `log_activity` helper function if you haven't already:
def log_activity(message):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO activity_log (message, timestamp) VALUES (%s, NOW())", (message,))
        conn.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




# Add this new route for adding specific drug stock
@app.route('/add_specific_drug_stock', methods=['POST'])
@role_required(['admin', 'pharmacy'])
def add_specific_drug_stock():
    drug_id = request.form.get('drug_id')
    units_to_add = request.form.get('units_to_add', type=int)

    if not drug_id or units_to_add is None or units_to_add <= 0:
        flash("Invalid drug selection or units to add. Please select a drug and enter a positive number.", "danger")
        return redirect(url_for('pharmacy'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update the stock for the specified drug
        cursor.execute("UPDATE pharmacy SET stock = stock + %s WHERE id = %s", (units_to_add, drug_id))
        if cursor.rowcount == 0:
            flash(f"Drug ID '{drug_id}' not found. No stock added.", "warning")
        else:
            conn.commit()
            # Log the activity
            log_activity(f"Added {units_to_add} units to drug ID: {drug_id}.")
            flash(f"{units_to_add} units added to drug ID: {drug_id}.", "success")
    except Exception as e:
        conn.rollback() # Rollback changes if an error occurs
        flash(f"Error adding drug stock: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('pharmacy'))

# Modify the existing '/pharmacy' route to differentiate POST requests
@app.route('/pharmacy', methods=['GET', 'POST'])
@role_required(['admin', 'pharmacy'])
def pharmacy():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Handle POST request for "Restock Out of Stock Drugs" button
        if request.method == 'POST' and 'restock_out_of_stock' in request.form:
            cursor.execute("SELECT id, name FROM pharmacy WHERE stock = 0") # Also fetch name for activity log
            out_of_stock_drugs = cursor.fetchall()

            if not out_of_stock_drugs:
                flash("No drugs are currently out of stock to restock.", "info")
            else:
                restocked_count = 0
                restocked_names = []
                for drug_row in out_of_stock_drugs:
                    drug_id_to_restock = drug_row['id']
                    drug_name = drug_row['name']
                    # Restock to reorder_level + 10 as per your existing logic
                    cursor.execute("UPDATE pharmacy SET stock = reorder_level + 10 WHERE id = %s", (drug_id_to_restock,))
                    restocked_count += 1
                    restocked_names.append(drug_name)

                conn.commit()
                log_activity(f"Restocked {restocked_count} out of stock drug(s): {', '.join(restocked_names)}.")
                flash(f"Successfully restocked {restocked_count} out of stock drug(s).", "success")
            
            # Close connection and redirect regardless of whether drugs were restocked
            cursor.close()
            conn.close()
            return redirect(url_for('pharmacy'))

        # --- Handle GET request (and fall-through from non-restock POSTs) ---
        # Get search query from URL parameters
        search_query = request.args.get('search_query', '').strip()

        # Build the base SQL query
        sql_query = "SELECT * FROM pharmacy"
        query_params = []

        if search_query:
            sql_query += " WHERE name LIKE %s"
            query_params.append('%' + search_query + '%')
        
        sql_query += " ORDER BY name ASC" # Always order for consistency

        cursor.execute(sql_query, tuple(query_params))
        rows = cursor.fetchall()

        drug_inventory_for_template = {}
        for row in rows:
            status = "Sufficient"
            if row['stock'] == 0:
                status = "Out of Stock"
            elif row['stock'] <= row['reorder_level']:
                status = "Low Stock"

            drug_inventory_for_template[row['id']] = {
                'name': row['name'],
                'stock': row['stock'],
                'reorder': row['reorder_level'],
                'status': status
            }
        
        return render_template("pharmacy.html", 
                               drug_inventory=drug_inventory_for_template,
                               search_query=search_query) # Pass search_query back to template

    except Exception as e:
        flash(f"A system error occurred on the pharmacy page: {e}", "danger")
        log_activity(f"System error in pharmacy route: {e}")
        # Always attempt to close connections in case of error
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return redirect(url_for('dashboard')) # Redirect to a safe page if critical error
    finally:
        # This finally block ensures connections are closed if not handled by the POST redirect
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Make sure your log_activity function is present in app.py if it's not already
# (from previous responses):
def log_activity(message):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO activity_log (message, timestamp) VALUES (%s, NOW())", (message,))
        conn.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Add this new route to your app.py, for example, below the add_specific_drug_stock route
@app.route('/add_medicine', methods=['POST'])
@role_required(['admin', 'pharmacy'])
def add_medicine():
    # Retrieve data from the form
    name = request.form.get('name').strip()
    stock = request.form.get('stock', type=int)
    reorder_level = request.form.get('reorder_level', type=int)

    # Basic validation
    if not name:
        flash("Medicine name cannot be empty.", "danger")
        return redirect(url_for('pharmacy'))
    if stock is None or stock < 0:
        flash("Stock must be a non-negative number.", "danger")
        return redirect(url_for('pharmacy'))
    if reorder_level is None or reorder_level < 0:
        flash("Reorder level must be a non-negative number.", "danger")
        return redirect(url_for('pharmacy'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert the new medicine into the pharmacy table
        cursor.execute(
            "INSERT INTO pharmacy (name, stock, reorder_level) VALUES (%s, %s, %s)",
            (name, stock, reorder_level)
        )
        conn.commit()
        log_activity(f"New medicine '{name}' added to inventory with stock {stock}.")
        flash(f"Medicine '{name}' added successfully!", "success")
    except mysql.connector.Error as err:
        conn.rollback() # Rollback in case of database error
        flash(f"Database error: {err.msg}", "danger")
    except Exception as e:
        conn.rollback() # Catch any other unexpected errors
        flash(f"An unexpected error occurred: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('pharmacy'))



# Route to generate drug order (placeholder)
# --- Pharmacy ---
# (Keep your existing /pharmacy, /add_specific_drug_stock, /add_medicine routes as they are)

# Route to generate drug order
@app.route('/generate_drug_order', methods=['GET']) # Changed to GET, as it's typically just viewing a report
@role_required(['admin', 'pharmacy'])
def generate_drug_order():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    order_list = []
    try:
        # Select drugs where current stock is less than or equal to the reorder level
        cursor.execute("SELECT id, name, stock, reorder_level FROM pharmacy WHERE stock <= reorder_level ORDER BY name ASC")
        low_stock_drugs = cursor.fetchall()

        if low_stock_drugs:
            for drug in low_stock_drugs:
                # Calculate suggested order quantity (e.g., bring stock up to reorder_level + a buffer)
                # You can customize this logic, e.g., reorder_level * 2, or fixed quantity
                suggested_quantity = drug['reorder_level'] + 50 - drug['stock'] # Example: reorder to (reorder_level + 50)
                if suggested_quantity < 10: # Ensure a reasonable minimum order
                    suggested_quantity = 10 
                
                order_list.append({
                    'id': drug['id'],
                    'name': drug['name'],
                    'current_stock': drug['stock'],
                    'reorder_level': drug['reorder_level'],
                    'suggested_quantity': suggested_quantity
                })
            flash("Order list generated based on low stock levels.", "info")
            log_activity(f"Generated drug order for {len(order_list)} low-stock items.")
        else:
            flash("No drugs are currently low or out of stock. No order needed at this time.", "success")
            log_activity("Attempted to generate drug order, but no low-stock items found.")

    except Exception as e:
        flash(f"Error generating drug order: {e}", "danger")
        log_activity(f"Error generating drug order: {e}")
    finally:
        cursor.close()
        conn.close()

    # Pass the order list to a new template or display it on the pharmacy page
    # For simplicity, let's render a new template for the order list.
    return render_template("pharmacy_order_list.html", order_list=order_list)


# Route to send alert for low stock drugs (already exists, but can be enhanced)
@app.route('/drug_low_stock_alert')
@role_required(['admin', 'pharmacy'])
def drug_low_stock_alert():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    low_stock_drugs = []
    try:
        cursor.execute("SELECT name, stock, reorder_level FROM pharmacy WHERE stock <= reorder_level")
        low_stock_drugs = cursor.fetchall()
        
        if low_stock_drugs:
            alert_messages = []
            for drug in low_stock_drugs:
                status = "Out of Stock" if drug['stock'] == 0 else "Low Stock"
                alert_messages.append(
                    f"{status}: {drug['name']} (Current: {drug['stock']}, Reorder: {drug['reorder_level']})"
                )
            full_alert_message = f"🚨 ALERT: {len(low_stock_drugs)} drugs are low or out of stock! " \
                                 f"Details: {'; '.join(alert_messages)}"
            flash(full_alert_message, "danger")
            log_activity(f"Sent low stock alert for {len(low_stock_drugs)} drug(s).")
        else:
            flash("All drugs are sufficiently stocked.", "success")
            log_activity("Checked drug stock; all items are sufficient.")

    except Exception as e:
        flash(f"Error checking drug stock: {e}", "danger")
        log_activity(f"Error checking drug stock: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('pharmacy')) # Redirect back to the pharmacy main page


# --- New Route: Search Drugs (for AJAX) ---
@app.route('/search_drugs')
@role_required(['admin', 'pharmacy'])
def search_drugs():
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    results = []
    try:
        if query:
            # Search for drugs where name contains the query (case-insensitive)
            cursor.execute("SELECT id, name, stock FROM pharmacy WHERE name LIKE %s LIMIT 10", ('%' + query + '%',))
            results = cursor.fetchall()
    except Exception as e:
        print(f"Error searching drugs: {e}") # Log error for debugging
    finally:
        cursor.close()
        conn.close()
    
    # Return results as JSON
    return jsonify(results)



# --- Modified Route: Issue Drug ---
@app.route('/issue_drug', methods=['GET', 'POST'])
@role_required([ 'pharmacy'])
def issue_drug():
    print("DEBUG: Entered issue_drug function.") # Debug print
    conn = None   # Initialize connection to None
    cursor = None # Initialize cursor to None

    try:
        conn = get_db_connection() # Attempt to get database connection
        cursor = conn.cursor(dictionary=True)
        print("DEBUG: Database connection established in issue_drug.") # Debug print

        if request.method == 'POST':
            print("DEBUG: Handling POST request in issue_drug.") # Debug print
            drug_id = request.form.get('drug_id_hidden')
            quantity_to_issue = request.form.get('quantity', type=int)

            if not drug_id or quantity_to_issue is None or quantity_to_issue <= 0:
                flash("Invalid drug selection or quantity. Please select a drug and enter a positive number.", "danger")
                # Important: If validation fails early, ensure connection is closed before returning
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                print("DEBUG: Invalid input. Redirecting (early exit POST).") # Debug print
                return redirect(url_for('issue_drug'))

            try:
                print(f"DEBUG: Processing issue for drug_id={drug_id}, quantity={quantity_to_issue}.") # Debug print
                # Check current stock before issuing
                cursor.execute("SELECT name, stock, reorder_level FROM pharmacy WHERE id = %s", (drug_id,))
                drug_info = cursor.fetchone()

                if not drug_info:
                    flash(f"Selected Medicine ID '{drug_id}' not found. Please select from the suggestions.", "danger")
                    print(f"DEBUG: Drug ID {drug_id} not found in DB.") # Debug print
                elif drug_info['stock'] < quantity_to_issue:
                    flash(f"Insufficient stock for {drug_info['name']}. Available: {drug_info['stock']} units.", "danger")
                    print(f"DEBUG: Insufficient stock for {drug_info['name']}.") # Debug print
                else:
                    # Stock is sufficient, proceed with update
                    cursor.execute("UPDATE pharmacy SET stock = stock - %s WHERE id = %s", (quantity_to_issue, drug_id))
                    conn.commit()
                    log_activity(f"Issued {quantity_to_issue} units of {drug_info['name']} (ID: {drug_id}).")
                    flash(f"Successfully issued {quantity_to_issue} units of {drug_info['name']}.", "success")
                    print(f"DEBUG: Successfully issued {quantity_to_issue} units of {drug_info['name']}.") # Debug print

                    # Recheck stock immediately after successful issue for an alert
                    cursor.execute("SELECT name, stock, reorder_level FROM pharmacy WHERE id = %s", (drug_id,))
                    updated_drug_info = cursor.fetchone()
                    if updated_drug_info and updated_drug_info['stock'] <= updated_drug_info['reorder_level']:
                        status = "Out of Stock" if updated_drug_info['stock'] == 0 else "Low Stock"
                        flash(f"🚨 ALERT: {updated_drug_info['name']} is now {status}! Current: {updated_drug_info['stock']}, Reorder: {updated_drug_info['reorder_level']}", "warning")
                        print(f"DEBUG: Low stock alert for {updated_drug_info['name']}.") # Debug print

            except mysql.connector.Error as db_err: # Catch specific database errors
                print(f"DEBUG: Database error in inner try-except: {db_err}") # Debug print
                if conn:
                    conn.rollback() # Rollback changes if a database error occurs
                flash(f"Database error issuing drug: {db_err.msg}", "danger")
                log_activity(f"Database error issuing drug ID {drug_id}: {db_err.msg}")
            except Exception as e: # Catch any other unexpected errors
                print(f"DEBUG: General error in inner try-except: {e}") # Debug print
                if conn:
                    conn.rollback() # Rollback changes if an error occurs
                flash(f"An unexpected error occurred while issuing drug: {e}", "danger")
                log_activity(f"Unexpected error issuing drug ID {drug_id}: {e}")
            finally:
                print("DEBUG: Inner finally block reached. Closing connections.") # Debug print
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                print("DEBUG: Connections closed (inner finally). Redirecting.") # Debug print
                return redirect(url_for('issue_drug')) # GUARANTEED RETURN FOR POST

        # If it's a GET request
        print("DEBUG: Handling GET request in issue_drug. Closing connections and rendering template.") # Debug print
        return render_template('issue_drug.html') # GUARANTEED RETURN FOR GET

    except mysql.connector.Error as db_conn_err: # Catch database connection errors
        print(f"DEBUG: Database connection error (outer try-except): {db_conn_err}") # Debug print
        flash(f"Could not connect to the database. Please try again later. ({db_conn_err.msg})", "danger")
        log_activity(f"DB connection error in issue_drug route: {db_conn_err.msg}")
        if cursor: # Attempt to close if opened before error
            cursor.close()
        if conn: # Attempt to close if opened before error
            conn.close()
        print("DEBUG: Redirecting to dashboard due to DB connection error.") # Debug print
        return redirect(url_for('dashboard')) # Redirect to a safe page

    except Exception as e:
        # This catches any other unforeseen errors that might occur
        # (e.g., if `get_db_connection` itself throws something other than mysql.connector.Error)
        print(f"DEBUG: Critical system error (outer try-except): {e}") # Debug print
        flash(f"A critical system error occurred: {e}", "danger")
        log_activity(f"Critical system error in issue_drug route: {e}")
        if cursor: # Attempt to close if opened before error
            cursor.close()
        if conn: # Attempt to close if opened before error
            conn.close()
        print("DEBUG: Redirecting to dashboard due to critical error.") # Debug print
        return redirect(url_for('dashboard'))

# Route for Queue Management
@app.route('/queue', methods=['GET', 'POST'])
@role_required(['admin'])
def queue():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch departments for dropdown
    cursor.execute("SELECT * FROM departments")
    departments = {dept['id']: dept for dept in cursor.fetchall()}

    # Handle new patient submission
    if request.method == 'POST':
        patient = request.form['patient']
        dept_id = request.form['dept_id']
        token_id = request.form.get('token_id') or None
        status = request.form.get('status') or 'Waiting'

        if token_id:
            cursor.execute("INSERT INTO patient_queue (token_id, dept_id, patient, status) VALUES (%s, %s, %s, %s)",
                           (token_id, dept_id, patient, status))
        else:
            cursor.execute("INSERT INTO patient_queue (dept_id, patient, status) VALUES (%s, %s, %s)",
                           (dept_id, patient, status))
        conn.commit()
        flash("Patient added to the queue.", "success")
        return redirect(url_for('queue'))

    # Fetch the current queue
    cursor.execute("SELECT * FROM patient_queue ORDER BY created_at ASC")
    token_queue = cursor.fetchall()
    conn.close()

    return render_template("queue.html", token_queue=token_queue, departments=departments)

# Route to call next patient
@app.route('/call_next_patient')
@role_required(['admin'])
def call_next_patient():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patient_queue WHERE status='Waiting' ORDER BY created_at ASC LIMIT 1")
    patient = cursor.fetchone()

    if patient:
        cursor.execute("UPDATE patient_queue SET status='In Consultation' WHERE token_id = %s", (patient['token_id'],))
        conn.commit()
        flash(f"Now calling: {patient['patient']} (Token #{patient['token_id']})", "info")
    else:
        flash("No waiting patients in the queue.", "warning")
    conn.close()
    return redirect(url_for('queue'))

# Route to bulk update statuses (example: mark all as completed)
@app.route('/update_queue_status')
@role_required(['admin'])
def update_queue_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE patient_queue SET status='Completed' WHERE status='In Consultation'")
    conn.commit()
    conn.close()
    flash("Queue statuses updated.", "success")
    return redirect(url_for('queue'))


# Define a standard 'idle' state for displays when content is cleared
DEFAULT_IDLE_DISPLAY_CONTENT = {
    'type': 'idle',
    'content': 'Hospital Management System: Ready',
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

# NEW: Refactor display_screen_details to hold more details per screen
# Key: screen_id, Value: {'status': 'ONLINE'|'OFFLINE', 'last_seen': datetime_object, 'ip': 'string'}
# Initialize with a set of default screens, all starting OFFLINE and N/A IP
display_screen_details = {
    1: {'status': 'OFFLINE', 'last_seen': None, 'ip': 'N/A'},
    2: {'status': 'OFFLINE', 'last_seen': None, 'ip': 'N/A'},
    3: {'status': 'OFFLINE', 'last_seen': None, 'ip': 'N/A'}
}

# Stores what each display should currently show
display_content_state = {
    1: DEFAULT_IDLE_DISPLAY_CONTENT.copy(),
    2: DEFAULT_IDLE_DISPLAY_CONTENT.copy(),
    3: DEFAULT_IDLE_DISPLAY_CONTENT.copy()
}

# Stores history of all broadcast messages (optional, mainly for admin view)
broadcast_messages_history = []


# --- Flask Routes for Display Management ---

@app.route('/display', methods=['GET', 'POST'])
@role_required(['admin'])
def display():
    current_time = datetime.now() # Still need current_time for last_seen formatting

    if request.method == 'POST':
        action = request.form.get('action')
        screen_id = request.form.get('screen_id', type=int)
        message_content = request.form.get('message_content')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if screen_id is valid for actions targeting specific screens
        if screen_id is not None and screen_id not in display_screen_details:
             flash(f'Screen {screen_id} not found in configured displays.', 'danger')
             return redirect(url_for('display'))

        if action == 'broadcast_all':
            if not message_content:
                flash('Broadcast message cannot be empty.', 'danger')
            else:
                for sid in display_content_state:
                    display_content_state[sid] = {'type': 'broadcast', 'content': message_content, 'timestamp': timestamp}
                broadcast_messages_history.append({'timestamp': timestamp, 'message': message_content, 'type': 'broadcast', 'target': 'All'})
                flash('Message broadcasted to all screens successfully!', 'success')
                log_activity(f"Broadcasted to all displays: '{message_content}'")

        elif action == 'send_token':
            if not message_content or not screen_id:
                flash('Token number and screen must be provided.', 'danger')
            else:
                display_content_state[screen_id] = {'type': 'token', 'content': message_content, 'timestamp': timestamp}
                broadcast_messages_history.append({'timestamp': timestamp, 'message': f"Token: {message_content}", 'type': 'token', 'target': screen_id})
                flash(f'Token {message_content} sent to Screen {screen_id}.', 'success')
                log_activity(f"Sent Token {message_content} to Screen {screen_id}")

        elif action == 'display_doctor_info':
            if not message_content or not screen_id:
                flash('Doctor info and screen must be provided.', 'danger')
            else:
                display_content_state[screen_id] = {'type': 'doctor', 'content': message_content, 'timestamp': timestamp}
                broadcast_messages_history.append({'timestamp': timestamp, 'message': f"Doctor Info: {message_content}", 'type': 'doctor', 'target': screen_id})
                flash(f'Doctor info sent to Screen {screen_id}.', 'success')
                log_activity(f"Sent Doctor Info '{message_content}' to Screen {screen_id}")

        elif action == 'emergency_alert':
            if not message_content:
                flash('Emergency alert message cannot be empty.', 'danger')
            else:
                for sid in display_content_state:
                    display_content_state[sid] = {'type': 'emergency', 'content': message_content, 'timestamp': timestamp}
                broadcast_messages_history.append({'timestamp': timestamp, 'message': f"EMERGENCY: {message_content}", 'type': 'emergency', 'target': 'All'})
                flash('Emergency alert broadcasted to all screens!', 'danger')
                log_activity(f"Broadcasted Emergency Alert: '{message_content}'")

        elif action == 'clear_specific_display':
            if not screen_id:
                flash('Screen must be selected to clear content.', 'danger')
            else:
                display_content_state[screen_id] = DEFAULT_IDLE_DISPLAY_CONTENT.copy()
                flash(f'Content on Screen {screen_id} cleared.', 'info')
                log_activity(f"Cleared content on Screen {screen_id}")
        
        elif action == 'clear_all_displays':
            for sid in display_content_state:
                display_content_state[sid] = DEFAULT_IDLE_DISPLAY_CONTENT.copy()
            flash('Content on all displays cleared.', 'info')
            log_activity("Cleared content on all displays")

        elif action == 'clear_broadcast_history':
            broadcast_messages_history.clear()
            flash('Broadcast message history cleared.', 'info')
            log_activity("Cleared broadcast message history")
        
        elif action == 'toggle_screen_status': # This now toggles 'status' in display_screen_details
            if screen_id is None: # Ensure screen_id is provided
                 flash('Screen must be selected to toggle status.', 'danger')
            else:
                current_logical_status = display_screen_details[screen_id]['status']
                if current_logical_status == 'ONLINE':
                    display_screen_details[screen_id]['status'] = 'OFFLINE'
                    display_screen_details[screen_id]['last_seen'] = None # Clear last_seen for manual OFFLINE
                    flash(f'Screen {screen_id} is now manually set to OFFLINE.', 'warning')
                    log_activity(f"Manually set Screen {screen_id} to OFFLINE")
                else:
                    # When manually setting to ONLINE, reset last_seen to now to reflect activity
                    display_screen_details[screen_id]['status'] = 'ONLINE'
                    display_screen_details[screen_id]['last_seen'] = current_time # Assume it's now online
                    flash(f'Screen {screen_id} is now manually set to ONLINE.', 'success')
                    log_activity(f"Manually set Screen {screen_id} to ONLINE")
        
        return redirect(url_for('display'))

    # For GET requests: Render the control panel
    return render_template(
        'display.html',
        display_screen_details=display_screen_details, # Pass this for status and IP
        display_content_state=display_content_state,
        broadcast_messages=broadcast_messages_history,
        screen_ids=sorted(display_screen_details.keys()), # For dropdowns
        current_time=current_time # Pass current time for potential debugging in template
    )

# --- Route for Display Clients to Retrieve Their Content ---
@app.route('/display_client/<int:display_id>')
@role_required(['admin'])
def display_client(display_id):
    # ... (error checking) ...
    display_screen_details[display_id]['status'] = 'ONLINE'
    display_screen_details[display_id]['last_seen'] = datetime.now()
    display_screen_details[display_id]['ip'] = request.remote_addr # <-- THIS IS WHERE IP IS CAPTURED
    log_activity(f"Display {display_id} connected/reconnected from IP: {request.remote_addr}")
    return render_template('display_client.html', display_id=display_id)

@app.route('/get_display_data/<int:display_id>')
def get_display_data(display_id):
    # ... (error checking) ...
    display_screen_details[display_id]['status'] = 'ONLINE'
    display_screen_details[display_id]['last_seen'] = datetime.now()
    display_screen_details[display_id]['ip'] = request.remote_addr # <-- IP IS REFRESHED HERE TOO
    return jsonify(display_content_state.get(display_id, DEFAULT_IDLE_DISPLAY_CONTENT.copy()))

# --- Toggle Screen Endpoint (for manual toggle link) ---
# This endpoint specifically handles the manual toggle from the screen card itself.
@app.route('/toggle_screen/<int:screen_id>')
def toggle_screen(screen_id):
    if screen_id not in display_screen_details:
        flash(f'Screen {screen_id} not found.', 'danger')
    else:
        current_logical_status = display_screen_details[screen_id]['status']
        if current_logical_status == 'ONLINE':
            display_screen_details[screen_id]['status'] = 'OFFLINE'
            display_screen_details[screen_id]['last_seen'] = None # Clear last_seen for manual OFFLINE
            flash(f'Screen {screen_id} is now manually set to OFFLINE.', 'warning')
            log_activity(f"Manually set Screen {screen_id} to OFFLINE (via direct link)")
        else:
            display_screen_details[screen_id]['status'] = 'ONLINE'
            display_screen_details[screen_id]['last_seen'] = datetime.now() # Assume it's now online
            flash(f'Screen {screen_id} is now manually set to ONLINE.', 'success')
            log_activity(f"Manually set Screen {screen_id} to ONLINE (via direct link)")
    
    return redirect(url_for('display'))

# --- Notifications ---
@app.route('/notifications', methods=['GET', 'POST'])
@role_required(['admin'])
def notification_center():
    if request.method == 'POST':
        message = request.form.get('message')
        priority = request.form.get('priority', 'normal')
        department = request.form.get('department')
        notification = {
            'id': len(notifications) + 1,
            'message': message,
            'priority': priority,
            'department': department,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'pending'
        }
        notifications.append(notification)
        flash("Notification added.", "success")
        return redirect(url_for('notification_center'))
    return render_template('notifications.html', notifications=notifications)

# ... other imports and app setup ...



@app.route('/notifications/send/<int:notification_id>')
@role_required(['admin'])
def send_notification(notification_id):
    for notification in notifications:
        if notification['id'] == notification_id:
            notification['status'] = 'sent'
            activity_log.append(f"{datetime.now().strftime('%H:%M:%S')} - Notification sent: {notification['message']}")
            flash(f"Notification sent: {notification['message']}", "success")
            break
    return redirect(url_for('notification_center'))

# --- Reports ---
@app.route('/reports')
@role_required(['admin'])
def reports():
    ot_utilization = (sum(1 for ot in ot_schedule if ot['status'] == 'In Progress') / len(ot_schedule)) * 100 if ot_schedule else 0
    ot_utilization = round(ot_utilization, 2)  # Show only 2 decimal places
    blood_status = {
        'total_units': sum(data['units'] for data in blood_data.values()),
        'critical_types': sum(1 for data in blood_data.values() if data['status'] == 'Critical')
    }
    drug_status = {
        'total_drugs': len(drug_inventory),
        'low_stock': sum(1 for data in drug_inventory.values() if data['status'] in ['Low Stock', 'Out of Stock'])
    }
    patient_flow = {
        'total': len(token_queue),
        'waiting': sum(1 for p in token_queue if p['status'] == 'Waiting'),
        'in_progress': sum(1 for p in token_queue if p['status'] == 'In Progress')
    }
    emergency_count = sum(1 for a in emergency_alerts if a['status'] == 'Active')
    report = {
        'date': datetime.now().strftime("%Y-%m-%d"),
        'ot_utilization': ot_utilization,
        'blood_status': blood_status,
        'drug_status': drug_status,
        'patient_flow': patient_flow,
        'emergency_alerts': emergency_count
    }
    return render_template('reports.html', report=report)


@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html'), 403




if __name__ == '__main__':
    app.run(debug=True)