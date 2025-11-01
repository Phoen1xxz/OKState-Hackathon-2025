import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class CarParkingApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Car-Parking System")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        self.root.configure(bg='#0f172a')
        
        # File to store user credentials
        self.users_file = "users.json"
        self.load_users()
        
        # Show login page
        self.show_login_page()
        
    def load_users(self):
        """Loading users from JSON file"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
    
    def save_users(self):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)
    
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login_page(self):
        """Displaying the login page"""
        self.clear_window()
        self.root.configure(bg='#0f172a')  # Deep slate background
        
        # Title
        title_label = tk.Label(self.root, text="Car Parking System", font=("Arial", 28, "bold"), bg='#0f172a', fg='#60a5fa')
        title_label.pack(pady=40)
        
        subtitle_label = tk.Label(self.root, text="Login to Continue", font=("Arial", 14), bg='#0f172a', fg='#94a3b8')
        subtitle_label.pack(pady=10)
        
        # Login Frame
        login_frame = tk.Frame(self.root, bg='#1e293b', relief=tk.RAISED, borderwidth=2)
        login_frame.pack(pady=30, padx=50, fill=tk.BOTH)
        
        # Add padding inside frame
        inner_frame = tk.Frame(login_frame, bg='#1e293b')
        inner_frame.pack(pady=20, padx=20)
        
        # Username
        username_label = tk.Label(inner_frame, text="Username:", font=("Arial", 14, "bold"), bg='#1e293b', fg='#e2e8f0')
        username_label.grid(row=0, column=0, sticky='w', pady=15, padx=10)
        
        self.username_entry = tk.Entry(inner_frame, font=("Arial", 14), bg='#334155', fg='#f1f5f9', width=25, relief=tk.FLAT, borderwidth=2, insertbackground='white')
        self.username_entry.grid(row=0, column=1, pady=15, padx=10, ipady=10)
        
        # Password
        password_label = tk.Label(inner_frame, text="Password:", font=("Arial", 14, "bold"), bg='#1e293b', fg='#e2e8f0')
        password_label.grid(row=1, column=0, sticky='w', pady=15, padx=10)
        
        self.password_entry = tk.Entry(inner_frame, font=("Arial", 14), bg='#334155', fg='#f1f5f9', width=25, show="●", relief=tk.FLAT, borderwidth=2, insertbackground='white')
        self.password_entry.grid(row=1, column=1, pady=15, padx=10, ipady=10)
        
        # Set focus on username entry
        self.username_entry.focus_set()
        
        # Buttons Frame
        buttons_frame = tk.Frame(self.root, bg='#1e293b')
        buttons_frame.pack(pady=30)
        
        # Continue Button
        continue_btn = tk.Button(buttons_frame, text="Continue", font=("Arial", 14, "bold"), bg='#3b82f6', fg='black', width=15, height=2, cursor='hand2', borderwidth=3, relief=tk.RAISED, activebackground='#2563eb', activeforeground='#ffffff', command=self.login)
        continue_btn.grid(row=0, column=0, padx=10, pady=10)
        
        # New User Button
        new_user_btn = tk.Button(buttons_frame, text="Sign Up", font=("Arial", 14, "bold"), bg='#6366f1', fg='black', width=15, height=2, cursor='hand2', borderwidth=3, relief=tk.RAISED, activebackground='#4f46e5', activeforeground='#ffffff', command=self.show_new_user_page)
        new_user_btn.grid(row=0, column=1, padx=10, pady=10)
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.login())
    
    def login(self):
        """Handle login logic"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password!")
            return
        
        if username in self.users and self.users[username] == password:
            self.show_main_page(username)
        else:
            messagebox.showerror("Error", "Invalid username or password!")
    
    def show_new_user_page(self):
        """Display the new user registration page"""
        self.clear_window()
        self.root.configure(bg='#1e1b4b')  # Deep indigo background
        
        # Title
        title_label = tk.Label(self.root, text="✨ New User Registration", font=("Arial", 26, "bold"), bg='#1e1b4b', fg='#a78bfa')
        title_label.pack(pady=35)
        
        subtitle_label = tk.Label(self.root, text="Create Your Account", font=("Arial", 14), bg='#1e1b4b', fg='#c4b5fd')
        subtitle_label.pack(pady=5)
        
        # Registration Frame
        reg_frame = tk.Frame(self.root, bg='#312e81', relief=tk.RAISED, borderwidth=2)
        reg_frame.pack(pady=25, padx=50, fill=tk.BOTH)
        
        # Add padding inside frame
        inner_frame = tk.Frame(reg_frame, bg='#312e81')
        inner_frame.pack(pady=20, padx=20)
        
        # Username
        username_label = tk.Label(inner_frame, text="Username:", font=("Arial", 14, "bold"), bg='#312e81', fg='#e0e7ff')
        username_label.grid(row=0, column=0, sticky='w', pady=12, padx=10)
        
        self.new_username_entry = tk.Entry(inner_frame, font=("Arial", 14), bg='#4c1d95', fg='#faf5ff', width=25, relief=tk.FLAT, borderwidth=2, insertbackground='white')
        self.new_username_entry.grid(row=0, column=1, pady=12, padx=10, ipady=10)
        
        # Password
        password_label = tk.Label(inner_frame, text="Password:", font=("Arial", 14, "bold"), bg='#312e81', fg='#e0e7ff')
        password_label.grid(row=1, column=0, sticky='w', pady=12, padx=10)
        
        self.new_password_entry = tk.Entry(inner_frame, font=("Arial", 14), bg='#4c1d95', fg='#faf5ff', width=25, show="●", relief=tk.FLAT, borderwidth=2, insertbackground='white')
        self.new_password_entry.grid(row=1, column=1, pady=12, padx=10, ipady=10)
        
        # Confirm Password
        confirm_label = tk.Label(inner_frame, text="Confirm Password:", font=("Arial", 14, "bold"), bg='#312e81', fg='#e0e7ff')
        confirm_label.grid(row=2, column=0, sticky='w', pady=12, padx=10)
        
        self.confirm_password_entry = tk.Entry(inner_frame, font=("Arial", 14), bg='#4c1d95', fg='#faf5ff', width=25, show="●", relief=tk.FLAT, borderwidth=2, insertbackground='white')
        self.confirm_password_entry.grid(row=2, column=1, pady=12, padx=10, ipady=10)

        self.new_username_entry.focus_set()  # Set focus on username entry
        
        # Buttons Frame
        buttons_frame = tk.Frame(self.root, bg='#1e1b4b')
        buttons_frame.pack(pady=30)
        
        # Register Button
        register_btn = tk.Button(buttons_frame, text="Register", font=("Arial", 14, "bold"), bg='#10b981', fg='black', width=15, height=2, cursor='hand2', relief=tk.RAISED, borderwidth=3, activebackground='#059669', activeforeground='#ffffff', command=self.register_user)
        register_btn.grid(row=0, column=0, padx=10, pady=10)
        
        # Back to Login Button
        back_btn = tk.Button(buttons_frame, text="Back to Login", font=("Arial", 14, "bold"), bg='#6366f1', fg='black', width=15, height=2, cursor='hand2', relief=tk.RAISED, borderwidth=3, activebackground='#4f46e5', activeforeground='#ffffff', command=self.show_login_page)
        back_btn.grid(row=0, column=1, padx=10, pady=10)
    
    def register_user(self):
        """Handle user registration"""
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get().strip()
        confirm = self.confirm_password_entry.get().strip()
        
        if not username or not password or not confirm:
            messagebox.showerror("Error", "Please fill in all fields!")
            return
        
        if username in self.users:
            messagebox.showerror("Error", "Username already exists!")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return
        
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters!")
            return
        
        # Save new user
        self.users[username] = password
        self.save_users()
        
        messagebox.showinfo("Success", "Registration successful! You can now login.")
        self.show_login_page()
    
    def show_main_page(self, username):
        """Display the main parking system page after login"""
        self.clear_window()
        self.root.configure(bg='#0c4a6e')  # Deep ocean blue background
        
        # Title
        title_label = tk.Label(self.root, text="Car Parking Management", font=("Arial", 26, "bold"), bg='#0c4a6e', fg='#7dd3fc')
        title_label.pack(pady=50)
        
        # Options frame
        options_frame = tk.Frame(self.root, bg='#0c4a6e')
        options_frame.pack(pady=40)
        
        
        # Logout button
        logout_btn = tk.Button(self.root, text="Logout", font=("Arial", 13, "bold"), bg='#ef4444', fg='black', width=18, height=2, cursor='hand2', relief=tk.RAISED, borderwidth=3, activebackground='#dc2626', activeforeground='#ffffff', command=self.show_login_page)
        logout_btn.pack(pady=30)

    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# Run the application
if __name__ == "__main__":
    app = CarParkingApp()
    app.run()