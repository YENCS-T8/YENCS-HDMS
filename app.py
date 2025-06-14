import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
import json

class WenlockHospitalSystem:
    def __init__(self):  # <-- FIXED
        self.root = tk.Tk()
        self.root.title("Wenlock Hospital - Unified Management System")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f8ff")
        
        # Load data from CSVs (simulated with the provided data)
        self.load_data()
        
        # Create main interface
        self.create_main_interface()
        
        # Start real-time updates
        self.start_real_time_updates()
    
    def load_data(self):
        """Load all hospital data"""
        # Blood Bank Data
        self.blood_data = {
            'B001': {'type': 'A+', 'units': 25, 'critical': 10, 'status': 'Sufficient'},
            'B002': {'type': 'A-', 'units': 5, 'critical': 5, 'status': 'Critical'},
            'B003': {'type': 'B+', 'units': 18, 'critical': 10, 'status': 'Sufficient'},
            'B004': {'type': 'B-', 'units': 2, 'critical': 5, 'status': 'Critical'},
            'B005': {'type': 'AB+', 'units': 10, 'critical': 5, 'status': 'Sufficient'},
            'B006': {'type': 'AB-', 'units': 1, 'critical': 3, 'status': 'Critical'},
            'B007': {'type': 'O+', 'units': 30, 'critical': 10, 'status': 'Sufficient'},
            'B008': {'type': 'O-', 'units': 4, 'critical': 5, 'status': 'Critical'}
        }
        
        # Department Data
        self.departments = {
            'D001': {'name': 'Cardiology', 'location': 'Block A, Floor 1'},
            'D002': {'name': 'Orthopedics', 'location': 'Block B, Floor 2'},
            'D003': {'name': 'OT', 'location': 'Block C, Floor G'},
            'D004': {'name': 'General Medicine', 'location': 'Block A, Floor 2'}
        }
        
        # Token Queue Data
        self.token_queue = [
            {'token_id': 101, 'dept_id': 'D001', 'patient': 'A. Kumar', 'status': 'Waiting'},
            {'token_id': 102, 'dept_id': 'D001', 'patient': 'B. Reddy', 'status': 'Called'},
            {'token_id': 205, 'dept_id': 'D002', 'patient': 'C. Fernandes', 'status': 'Waiting'},
            {'token_id': 310, 'dept_id': 'D004', 'patient': 'D. Shetty', 'status': 'In Progress'}
        ]
        
        # Emergency Alerts
        self.emergency_alerts = [
            {'id': 'E001', 'code': 'Code Blue', 'dept': 'OT', 'time': '2025-06-01 09:45 AM', 'status': 'Active'},
            {'id': 'E002', 'code': 'Code Red', 'dept': 'Pharmacy', 'time': '2025-06-01 10:10 AM', 'status': 'Cleared'}
        ]
        
        # Drug Inventory
        self.drug_inventory = {
            'DR001': {'name': 'Paracetamol 500mg', 'stock': 120, 'reorder': 100, 'status': 'Available'},
            'DR002': {'name': 'Amoxicillin 250mg', 'stock': 30, 'reorder': 50, 'status': 'Low Stock'},
            'DR003': {'name': 'Insulin Injection', 'stock': 0, 'reorder': 20, 'status': 'Out of Stock'},
            'DR004': {'name': 'ORS Sachet', 'stock': 300, 'reorder': 150, 'status': 'Available'}
        }
        
        # OT Schedule (additional data)
        self.ot_schedule = [
            {'ot_id': 'OT1', 'surgeon': 'Dr. Sharma', 'procedure': 'Cardiac Surgery', 'time': '10:00 AM', 'status': 'In Progress'},
            {'ot_id': 'OT2', 'surgeon': 'Dr. Patel', 'procedure': 'Orthopedic Surgery', 'time': '2:00 PM', 'status': 'Scheduled'},
            {'ot_id': 'OT3', 'surgeon': 'Dr. Kumar', 'procedure': 'General Surgery', 'time': '4:00 PM', 'status': 'Available'}
        ]
    
    def create_main_interface(self):
        """Create the main dashboard interface"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        # Hospital Logo and Title
        title_label = tk.Label(header_frame, text="🏥 WENLOCK HOSPITAL", 
                              font=("Arial", 24, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(side="left", padx=20, pady=20)
        
        # Current Time Display
        self.time_label = tk.Label(header_frame, text="", font=("Arial", 14), 
                                  fg="white", bg="#2c3e50")
        self.time_label.pack(side="right", padx=20, pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_emergency_tab()
        self.create_ot_management_tab()
        self.create_blood_bank_tab()
        self.create_pharmacy_tab()
        self.create_queue_management_tab()
        self.create_display_broadcast_tab()
    
    def create_dashboard_tab(self):
        """Main dashboard with overview"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="🏠 Dashboard")
        
        # Create dashboard sections
        # Critical Alerts Section
        alerts_frame = tk.LabelFrame(dashboard_frame, text="🚨 Critical Alerts", 
                                   font=("Arial", 14, "bold"), fg="red")
        alerts_frame.pack(fill="x", padx=10, pady=5)
        
        self.alerts_text = tk.Text(alerts_frame, height=4, font=("Arial", 10))
        self.alerts_text.pack(fill="x", padx=5, pady=5)
        
        # Statistics Section
        stats_frame = tk.Frame(dashboard_frame)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Create stats cards
        self.create_stat_card(stats_frame, "Active OTs", "2/3", "#3498db", 0)
        self.create_stat_card(stats_frame, "Critical Blood Types", "4", "#e74c3c", 1)
        self.create_stat_card(stats_frame, "Patients in Queue", "4", "#f39c12", 2)
        self.create_stat_card(stats_frame, "Low Stock Drugs", "2", "#e67e22", 3)
        
        # Recent Activity
        activity_frame = tk.LabelFrame(dashboard_frame, text="📋 Recent Activity", 
                                     font=("Arial", 14, "bold"))
        activity_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.activity_text = tk.Text(activity_frame, font=("Arial", 10))
        activity_scrollbar = ttk.Scrollbar(activity_frame, orient="vertical", command=self.activity_text.yview)
        self.activity_text.configure(yscrollcommand=activity_scrollbar.set)
        self.activity_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        activity_scrollbar.pack(side="right", fill="y")
    
    def create_stat_card(self, parent, title, value, color, column):
        """Create a statistics card"""
        card_frame = tk.Frame(parent, bg=color, relief="raised", bd=2)
        card_frame.grid(row=0, column=column, padx=10, pady=10, sticky="ew")
        parent.grid_columnconfigure(column, weight=1)
        
        title_label = tk.Label(card_frame, text=title, font=("Arial", 12, "bold"), 
                              fg="white", bg=color)
        title_label.pack(pady=(10, 5))
        
        value_label = tk.Label(card_frame, text=value, font=("Arial", 20, "bold"), 
                              fg="white", bg=color)
        value_label.pack(pady=(0, 10))
    
    def create_emergency_tab(self):
        """Emergency alerts and codes management"""
        emergency_frame = ttk.Frame(self.notebook)
        self.notebook.add(emergency_frame, text="🚨 Emergency")
        
        # Emergency Code Buttons
        codes_frame = tk.LabelFrame(emergency_frame, text="Emergency Codes", 
                                  font=("Arial", 14, "bold"))
        codes_frame.pack(fill="x", padx=10, pady=5)
        
        button_frame = tk.Frame(codes_frame)
        button_frame.pack(pady=10)
        
        codes = [
            ("Code Blue - Cardiac Arrest", "#3498db"),
            ("Code Red - Fire", "#e74c3c"),
            ("Code Yellow - Bomb Threat", "#f1c40f"),
            ("Code Black - Security", "#2c3e50")
        ]
        
        for i, (code, color) in enumerate(codes):
            btn = tk.Button(button_frame, text=code, bg=color, fg="white", 
                           font=("Arial", 12, "bold"), width=20, height=2,
                           command=lambda c=code: self.trigger_emergency(c))
            btn.grid(row=i//2, column=i%2, padx=10, pady=5)
        
        # Active Alerts
        alerts_frame = tk.LabelFrame(emergency_frame, text="Active Alerts", 
                                   font=("Arial", 14, "bold"))
        alerts_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for alerts
        columns = ("ID", "Code", "Department", "Time", "Status")
        self.emergency_tree = ttk.Treeview(alerts_frame, columns=columns, show="headings")
        
        for col in columns:
            self.emergency_tree.heading(col, text=col)
            self.emergency_tree.column(col, width=120)
        
        self.emergency_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = tk.Frame(emergency_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(control_frame, text="Clear Alert", command=self.clear_alert,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(control_frame, text="Broadcast to All Screens", command=self.broadcast_emergency,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    
    def create_ot_management_tab(self):
        """OT scheduling and management"""
        ot_frame = ttk.Frame(self.notebook)
        self.notebook.add(ot_frame, text="🏥 OT Management")
        
        # OT Schedule
        schedule_frame = tk.LabelFrame(ot_frame, text="OT Schedule", 
                                     font=("Arial", 14, "bold"))
        schedule_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for OT schedule
        ot_columns = ("OT ID", "Surgeon", "Procedure", "Time", "Status")
        self.ot_tree = ttk.Treeview(schedule_frame, columns=ot_columns, show="headings")
        
        for col in ot_columns:
            self.ot_tree.heading(col, text=col)
            self.ot_tree.column(col, width=150)
        
        self.ot_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # OT Control Panel
        control_frame = tk.LabelFrame(ot_frame, text="OT Controls", 
                                    font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Control buttons
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Add Surgery", command=self.add_surgery,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Update Status", command=self.update_ot_status,
                 bg="#f39c12", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Emergency Block", command=self.emergency_block_ot,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    
    def create_blood_bank_tab(self):
        """Blood bank inventory management"""
        blood_frame = ttk.Frame(self.notebook)
        self.notebook.add(blood_frame, text="🩸 Blood Bank")
        
        # Blood inventory
        inventory_frame = tk.LabelFrame(blood_frame, text="Blood Inventory", 
                                      font=("Arial", 14, "bold"))
        inventory_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for blood inventory
        blood_columns = ("Blood ID", "Type", "Units Available", "Critical Level", "Status")
        self.blood_tree = ttk.Treeview(inventory_frame, columns=blood_columns, show="headings")
        
        for col in blood_columns:
            self.blood_tree.heading(col, text=col)
            self.blood_tree.column(col, width=120)
        
        self.blood_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Blood bank controls
        control_frame = tk.LabelFrame(blood_frame, text="Blood Bank Controls", 
                                    font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)
        
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Add Stock", command=self.add_blood_stock,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Issue Blood", command=self.issue_blood,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Critical Alert", command=self.blood_critical_alert,
                 bg="#f39c12", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    
    def create_pharmacy_tab(self):
        """Pharmacy inventory management"""
        pharmacy_frame = ttk.Frame(self.notebook)
        self.notebook.add(pharmacy_frame, text="💊 Pharmacy")
        
        # Drug inventory
        inventory_frame = tk.LabelFrame(pharmacy_frame, text="Drug Inventory", 
                                      font=("Arial", 14, "bold"))
        inventory_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for drug inventory
        drug_columns = ("Drug ID", "Drug Name", "Stock Qty", "Reorder Level", "Status")
        self.drug_tree = ttk.Treeview(inventory_frame, columns=drug_columns, show="headings")
        
        for col in drug_columns:
            self.drug_tree.heading(col, text=col)
            self.drug_tree.column(col, width=130)
        
        self.drug_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Pharmacy controls
        control_frame = tk.LabelFrame(pharmacy_frame, text="Pharmacy Controls", 
                                    font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)
        
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Update Stock", command=self.update_drug_stock,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Generate Order", command=self.generate_drug_order,
                 bg="#e67e22", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Low Stock Alert", command=self.drug_low_stock_alert,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    
    def create_queue_management_tab(self):
        """Patient queue management"""
        queue_frame = ttk.Frame(self.notebook)
        self.notebook.add(queue_frame, text="👥 Queue Management")
        
        # Token queue
        queue_list_frame = tk.LabelFrame(queue_frame, text="Patient Queue", 
                                       font=("Arial", 14, "bold"))
        queue_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for queue
        queue_columns = ("Token ID", "Department", "Patient Name", "Status")
        self.queue_tree = ttk.Treeview(queue_list_frame, columns=queue_columns, show="headings")
        
        for col in queue_columns:
            self.queue_tree.heading(col, text=col)
            self.queue_tree.column(col, width=150)
        
        self.queue_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Queue controls
        control_frame = tk.LabelFrame(queue_frame, text="Queue Controls", 
                                    font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)
        
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Call Next", command=self.call_next_patient,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Add Patient", command=self.add_patient_queue,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Update Status", command=self.update_queue_status,
                 bg="#f39c12", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    
    def create_display_broadcast_tab(self):
        """Display and broadcast management"""
        display_frame = ttk.Frame(self.notebook)
        self.notebook.add(display_frame, text="📺 Display Management")
        
        # Display status
        status_frame = tk.LabelFrame(display_frame, text="Display Screen Status (73 Screens)", 
                                   font=("Arial", 14, "bold"))
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # Simulated display grid
        display_grid = tk.Frame(status_frame)
        display_grid.pack(pady=10)
        
        self.display_buttons = []
        for i in range(8):  # Show 8 representative screens
            for j in range(9):
                screen_id = i * 9 + j + 1
                if screen_id <= 73:
                    btn = tk.Button(display_grid, text=f"S{screen_id}", 
                                   bg="#27ae60", fg="white", width=4, height=2,
                                   command=lambda sid=screen_id: self.toggle_screen(sid))
                    btn.grid(row=i, column=j, padx=1, pady=1)
                    self.display_buttons.append(btn)
        
        # Broadcast controls
        broadcast_frame = tk.LabelFrame(display_frame, text="Broadcast Controls", 
                                      font=("Arial", 14, "bold"))
        broadcast_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Message input
        msg_frame = tk.Frame(broadcast_frame)
        msg_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(msg_frame, text="Broadcast Message:", font=("Arial", 12)).pack(anchor="w")
        self.broadcast_text = tk.Text(msg_frame, height=3, font=("Arial", 11))
        self.broadcast_text.pack(fill="x", pady=5)
        
        # Broadcast buttons
        btn_frame = tk.Frame(broadcast_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Broadcast All", command=self.broadcast_all,
                 bg="#e74c3c", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Emergency Broadcast", command=self.emergency_broadcast,
                 bg="#c0392b", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Department Specific", command=self.dept_broadcast,
                 bg="#8e44ad", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=5)
    
    def start_real_time_updates(self):
        """Start real-time updates"""
        self.update_display()
        self.root.after(1000, self.start_real_time_updates)  # Update every second
    
    def update_display(self):
        """Update all displays with current data"""
        # Update time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        
        # Update emergency alerts tree
        self.update_emergency_tree()
        
        # Update OT schedule tree
        self.update_ot_tree()
        
        # Update blood bank tree
        self.update_blood_tree()
        
        # Update pharmacy tree
        self.update_drug_tree()
        
        # Update queue tree
        self.update_queue_tree()
        
        # Update dashboard alerts
        self.update_dashboard_alerts()
        
        # Update activity log
        self.update_activity_log()
    
    def update_emergency_tree(self):
        """Update emergency alerts treeview"""
        # Clear existing data
        for item in self.emergency_tree.get_children():
            self.emergency_tree.delete(item)
        
        # Insert current alerts
        for alert in self.emergency_alerts:
            self.emergency_tree.insert("", "end", values=(
                alert['id'], alert['code'], alert['dept'], 
                alert['time'], alert['status']
            ))
    
    def update_ot_tree(self):
        """Update OT schedule treeview"""
        for item in self.ot_tree.get_children():
            self.ot_tree.delete(item)
        
        for ot in self.ot_schedule:
            self.ot_tree.insert("", "end", values=(
                ot['ot_id'], ot['surgeon'], ot['procedure'], 
                ot['time'], ot['status']
            ))
    
    def update_blood_tree(self):
        """Update blood bank treeview"""
        for item in self.blood_tree.get_children():
            self.blood_tree.delete(item)
        
        for blood_id, data in self.blood_data.items():
            self.blood_tree.insert("", "end", values=(
                blood_id, data['type'], data['units'], 
                data['critical'], data['status']
            ))
    
    def update_drug_tree(self):
        """Update drug inventory treeview"""
        for item in self.drug_tree.get_children():
            self.drug_tree.delete(item)
        
        for drug_id, data in self.drug_inventory.items():
            self.drug_tree.insert("", "end", values=(
                drug_id, data['name'], data['stock'], 
                data['reorder'], data['status']
            ))
    
    def update_queue_tree(self):
        """Update queue treeview"""
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        
        for queue_item in self.token_queue:
            dept_name = self.departments[queue_item['dept_id']]['name']
            self.queue_tree.insert("", "end", values=(
                queue_item['token_id'], dept_name, 
                queue_item['patient'], queue_item['status']
            ))
    
    def update_dashboard_alerts(self):
        """Update dashboard critical alerts"""
        self.alerts_text.delete(1.0, tk.END)
        
        # Check for critical conditions
        alerts = []
        
        # Critical blood types
        for blood_id, data in self.blood_data.items():
            if data['status'] == 'Critical':
                alerts.append(f"🩸 CRITICAL: {data['type']} blood - Only {data['units']} units left")
        
        # Out of stock drugs
        for drug_id, data in self.drug_inventory.items():
            if data['status'] == 'Out of Stock':
                alerts.append(f"💊 OUT OF STOCK: {data['name']}")
        
        # Active emergencies
        for alert in self.emergency_alerts:
            if alert['status'] == 'Active':
                alerts.append(f"🚨 ACTIVE: {alert['code']} in {alert['dept']}")
        
        # Display alerts
        if alerts:
            self.alerts_text.insert(tk.END, "\n".join(alerts))
        else:
            self.alerts_text.insert(tk.END, "✅ No critical alerts at this time")
    
    def update_activity_log(self):
        """Update activity log"""
        if not hasattr(self, 'activity_log'):
            self.activity_log = []
        
        # Add timestamp to recent activities (simplified)
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if len(self.activity_log) == 0:  # Initialize with some sample activities
            self.activity_log = [
                f"{current_time} - System initialized",
                f"{current_time} - Blood bank data loaded",
                f"{current_time} - OT schedules updated",
                f"{current_time} - Patient queues synchronized"
            ]
        
        # Update activity display
        self.activity_text.delete(1.0, tk.END)
        for activity in self.activity_log[-20:]:  # Show last 20 activities
            self.activity_text.insert(tk.END, activity + "\n")
        self.activity_text.see(tk.END)
    
    # Event handlers (simplified implementations)
    def trigger_emergency(self, code_type):
        """Trigger emergency alert"""
        alert_id = f"E{len(self.emergency_alerts) + 1:03d}"
        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        new_alert = {
            'id': alert_id,
            'code': code_type,
            'dept': 'Central Command',
            'time': timestamp,
            'status': 'Active'
        }
        
        self.emergency_alerts.append(new_alert)
        self.add_activity(f"EMERGENCY: {code_type} triggered")
        messagebox.showwarning("Emergency Alert", f"{code_type} has been triggered and broadcast to all screens!")
    
    def clear_alert(self):
        """Clear selected alert"""
        selection = self.emergency_tree.selection()
        if selection:
            item = self.emergency_tree.item(selection[0])
            alert_id = item['values'][0]
            
            for alert in self.emergency_alerts:
                if alert['id'] == alert_id:
                    alert['status'] = 'Cleared'
                    break
            
            self.add_activity(f"Emergency alert {alert_id} cleared")
            messagebox.showinfo("Alert", "Emergency alert has been cleared")
    
    def broadcast_emergency(self):
        """Broadcast emergency to all screens"""
        self.add_activity("Emergency broadcast sent to all 73 screens")
        messagebox.showinfo("Broadcast", "Emergency alert broadcast to all 73 display screens!")
    
    def add_surgery(self):
        """Add new surgery to OT schedule"""
        # Simplified - in real implementation, would open a dialog
        new_surgery = {
            'ot_id': f'OT{len(self.ot_schedule) + 1}',
            'surgeon': 'Dr. New Surgeon',
            'procedure': 'Emergency Surgery',
            'time': '6:00 PM',
            'status': 'Scheduled'
        }
        self.ot_schedule.append(new_surgery)
        self.add_activity("New surgery scheduled in OT")
        messagebox.showinfo("Success", "New surgery added to OT schedule")
    
    def update_ot_status(self):
        """Update OT status"""
        selection = self.ot_tree.selection()
        if selection:
            item = self.ot_tree.item(selection[0])
            ot_id = item['values'][0]
            
            for ot in self.ot_schedule:
                if ot['ot_id'] == ot_id:
                    if ot['status'] == 'Scheduled':
                        ot['status'] = 'In Progress'
                    elif ot['status'] == 'In Progress':
                        ot['status'] = 'Completed'
                    else:
                        ot['status'] = 'Available'
                    break
            
            self.add_activity(f"OT {ot_id} status updated")
            messagebox.showinfo("Success", f"OT {ot_id} status updated")
    
    def emergency_block_ot(self):
        """Block OT for emergency"""
        for ot in self.ot_schedule:
            if ot['status'] == 'Available':
                ot['status'] = 'Emergency Block'
                ot['surgeon'] = 'Emergency Team'
                ot['procedure'] = 'Emergency Surgery'
                ot['time'] = 'ASAP'
                self.add_activity(f"OT {ot['ot_id']} blocked for emergency")
                messagebox.showinfo("Emergency", f"OT {ot['ot_id']} blocked for emergency use")
                return
        
        messagebox.showwarning("Warning", "No available OT for emergency block")
    
    def add_blood_stock(self):
        """Add blood stock"""
        # Simplified implementation
        for blood_id, data in self.blood_data.items():
            if data['status'] == 'Critical':
                data['units'] += 10
                if data['units'] > data['critical']:
                    data['status'] = 'Sufficient'
                self.add_activity(f"Blood stock added: {data['type']} - {data['units']} units")
                messagebox.showinfo("Success", f"Added 10 units of {data['type']} blood")
                return
    
    def issue_blood(self):
        """Issue blood units"""
        # Simplified implementation
        for blood_id, data in self.blood_data.items():
            if data['units'] > 0:
                data['units'] -= 1
                if data['units'] <= data['critical']:
                    data['status'] = 'Critical'
                self.add_activity(f"Blood issued: {data['type']} - {data['units']} units remaining")
                messagebox.showinfo("Success", f"1 unit of {data['type']} blood issued")
                return
    
    def blood_critical_alert(self):
        """Send blood critical alert"""
        critical_types = [data['type'] for data in self.blood_data.values() if data['status'] == 'Critical']
        if critical_types:
            alert_msg = f"Critical blood shortage: {', '.join(critical_types)}"
            self.add_activity(alert_msg)
            messagebox.showwarning("Critical Alert", alert_msg)
        else:
            messagebox.showinfo("Info", "No critical blood shortages at this time")
    
    def update_drug_stock(self):
        """Update drug stock"""
        for drug_id, data in self.drug_inventory.items():
            if data['status'] == 'Out of Stock':
                data['stock'] = data['reorder'] + 50
                data['status'] = 'Available'
                self.add_activity(f"Drug restocked: {data['name']} - {data['stock']} units")
                messagebox.showinfo("Success", f"{data['name']} restocked")
                return
    
    def generate_drug_order(self):
        """Generate drug purchase order"""
        low_stock_drugs = [data['name'] for data in self.drug_inventory.values() 
                          if data['status'] in ['Low Stock', 'Out of Stock']]
        
        if low_stock_drugs:
            order_msg = f"Purchase order generated for: {', '.join(low_stock_drugs)}"
            self.add_activity(order_msg)
            messagebox.showinfo("Order Generated", order_msg)
        else:
            messagebox.showinfo("Info", "No drugs need reordering at this time")
    
    def drug_low_stock_alert(self):
        """Send low stock alert"""
        low_stock_drugs = [data['name'] for data in self.drug_inventory.values() 
                          if data['status'] in ['Low Stock', 'Out of Stock']]
        
        if low_stock_drugs:
            alert_msg = f"Low stock alert: {', '.join(low_stock_drugs)}"
            self.add_activity(alert_msg)
            messagebox.showwarning("Low Stock Alert", alert_msg)
        else:
            messagebox.showinfo("Info", "All drugs sufficiently stocked")
    
    def call_next_patient(self):
        """Call next patient in queue"""
        for queue_item in self.token_queue:
            if queue_item['status'] == 'Waiting':
                queue_item['status'] = 'Called'
                self.add_activity(f"Patient called: {queue_item['patient']} - Token {queue_item['token_id']}")
                messagebox.showinfo("Patient Called", f"Token {queue_item['token_id']} - {queue_item['patient']} called")
                return
        
        messagebox.showinfo("Info", "No patients waiting in queue")
    
    def add_patient_queue(self):
        """Add patient to queue"""
        new_token = {
            'token_id': max([q['token_id'] for q in self.token_queue]) + 1,
            'dept_id': 'D001',  # Default to Cardiology
            'patient': 'New Patient',
            'status': 'Waiting'
        }
        self.token_queue.append(new_token)
        self.add_activity(f"New patient added to queue: Token {new_token['token_id']}")
        messagebox.showinfo("Success", f"New patient added with Token {new_token['token_id']}")
    
    def update_queue_status(self):
        """Update patient queue status"""
        for queue_item in self.token_queue:
            if queue_item['status'] == 'Called':
                queue_item['status'] = 'In Progress'
                self.add_activity(f"Patient status updated: {queue_item['patient']} - In Progress")
                messagebox.showinfo("Success", f"Token {queue_item['token_id']} status updated to In Progress")
                return
            elif queue_item['status'] == 'In Progress':
                queue_item['status'] = 'Completed'
                self.add_activity(f"Patient completed: {queue_item['patient']}")
                messagebox.showinfo("Success", f"Token {queue_item['token_id']} marked as completed")
                return
    
    def toggle_screen(self, screen_id):
        """Toggle display screen status"""
        btn = self.display_buttons[screen_id - 1]
        current_color = btn.cget('bg')
        
        if current_color == '#27ae60':  # Green (Online)
            btn.config(bg='#e74c3c')  # Red (Offline)
            status = 'OFFLINE'
        else:
            btn.config(bg='#27ae60')  # Green (Online)
            status = 'ONLINE'
        
        self.add_activity(f"Screen {screen_id} status: {status}")
        messagebox.showinfo("Screen Status", f"Screen {screen_id} is now {status}")
    
    def broadcast_all(self):
        """Broadcast message to all screens"""
        message = self.broadcast_text.get(1.0, tk.END).strip()
        if message:
            self.add_activity(f"Message broadcast to all screens: {message[:50]}...")
            messagebox.showinfo("Broadcast Complete", "Message sent to all 73 display screens!")
        else:
            messagebox.showwarning("Warning", "Please enter a message to broadcast")
    
    def emergency_broadcast(self):
        """Emergency broadcast with priority"""
        message = self.broadcast_text.get(1.0, tk.END).strip()
        if message:
            self.add_activity(f"EMERGENCY BROADCAST: {message[:50]}...")
            messagebox.showwarning("Emergency Broadcast", "EMERGENCY MESSAGE sent to all screens with highest priority!")
        else:
            messagebox.showwarning("Warning", "Please enter an emergency message to broadcast")
    
    def dept_broadcast(self):
        """Department specific broadcast"""
        message = self.broadcast_text.get(1.0, tk.END).strip()
        if message:
            # Simplified - would normally show department selection dialog
            self.add_activity(f"Department broadcast sent: {message[:50]}...")
            messagebox.showinfo("Department Broadcast", "Message sent to selected department screens!")
        else:
            messagebox.showwarning("Warning", "Please enter a message to broadcast")
    
    def add_activity(self, activity):
        """Add activity to log"""
        if not hasattr(self, 'activity_log'):
            self.activity_log = []
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"{timestamp} - {activity}")
        
        # Keep only last 50 activities
        if len(self.activity_log) > 50:
            self.activity_log = self.activity_log[-50:]
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# Additional utility classes for extended functionality
class ReportGenerator:
    """Generate various hospital reports"""
    
    def __init__(self, hospital_system):  # <-- FIXED
        self.hospital_system = hospital_system
    
    def generate_daily_report(self):
        """Generate daily hospital report"""
        report = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'ot_utilization': self.calculate_ot_utilization(),
            'blood_status': self.get_blood_status_summary(),
            'drug_status': self.get_drug_status_summary(),
            'patient_flow': self.get_patient_flow_summary(),
            'emergency_alerts': len([a for a in self.hospital_system.emergency_alerts if a['status'] == 'Active'])
        }
        return report
    
    def calculate_ot_utilization(self):
        """Calculate OT utilization percentage"""
        total_ots = len(self.hospital_system.ot_schedule)
        active_ots = len([ot for ot in self.hospital_system.ot_schedule if ot['status'] == 'In Progress'])
        return (active_ots / total_ots) * 100 if total_ots > 0 else 0
    
    def get_blood_status_summary(self):
        """Get blood bank status summary"""
        total_units = sum(data['units'] for data in self.hospital_system.blood_data.values())
        critical_types = len([data for data in self.hospital_system.blood_data.values() if data['status'] == 'Critical'])
        return {'total_units': total_units, 'critical_types': critical_types}
    
    def get_drug_status_summary(self):
        """Get drug inventory summary"""
        total_drugs = len(self.hospital_system.drug_inventory)
        low_stock = len([data for data in self.hospital_system.drug_inventory.values() if data['status'] in ['Low Stock', 'Out of Stock']])
        return {'total_drugs': total_drugs, 'low_stock': low_stock}
    
    def get_patient_flow_summary(self):
        """Get patient flow summary"""
        total_patients = len(self.hospital_system.token_queue)
        waiting = len([p for p in self.hospital_system.token_queue if p['status'] == 'Waiting'])
        in_progress = len([p for p in self.hospital_system.token_queue if p['status'] == 'In Progress'])
        return {'total': total_patients, 'waiting': waiting, 'in_progress': in_progress}

class NotificationSystem:
    """Handle all hospital notifications"""
    
    def __init__(self, hospital_system):  # <-- FIXED
        self.hospital_system = hospital_system
        self.notification_queue = []
    
    def add_notification(self, message, priority='normal', department=None):
        """Add notification to queue"""
        notification = {
            'id': len(self.notification_queue) + 1,
            'message': message,
            'priority': priority,
            'department': department,
            'timestamp': datetime.now(),
            'status': 'pending'
        }
        self.notification_queue.append(notification)
    
    def send_notification(self, notification_id):
        """Send notification to appropriate channels"""
        for notification in self.notification_queue:
            if notification['id'] == notification_id:
                notification['status'] = 'sent'
                # In real implementation, would integrate with SMS, email, PA system
                print(f"Notification sent: {notification['message']}")
                break
    
    def get_pending_notifications(self):
        """Get all pending notifications"""
        return [n for n in self.notification_queue if n['status'] == 'pending']

# Main execution
if __name__ == "__main__":
    try:
        # Create and run the hospital management system
        hospital_system = WenlockHospitalSystem()
        
        # Initialize additional components
        report_generator = ReportGenerator(hospital_system)
        notification_system = NotificationSystem(hospital_system)
        
        # Add some initial notifications
        notification_system.add_notification("System initialized successfully", priority='info')
        notification_system.add_notification("Daily backup completed", priority='normal')
        
        # Run the main application
        hospital_system.run()
        
    except Exception as e:
        print(f"Error starting Wenlock Hospital System: {e}")
        messagebox.showerror("System Error", f"Failed to start hospital system: {e}")