import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
# Use top-level imports so the script can be run directly (python UI.py)
try:
    # Prefer direct imports when running as a standalone script
    from create_user import create_user, Auth0Error
    from auth_password import perform_password_grant
except Exception:
    # Fallback to relative imports when executed as a package
    from .create_user import create_user, Auth0Error
    from .auth_password import perform_password_grant


def _format_auth0_error(info) -> str:
    """Convert various Auth0 error shapes into a readable string."""
    if info is None:
        return ""
    if isinstance(info, str):
        return info
    if isinstance(info, (int, float)):
        return str(info)
    if isinstance(info, list):
        parts = [_format_auth0_error(i) for i in info]
        return "; ".join(p for p in parts if p)
    if isinstance(info, dict):
        # Prefer common message keys
        for key in ("description", "error_description", "message", "error", "msg"):
            v = info.get(key)
            if v:
                return _format_auth0_error(v)
        # Otherwise flatten dict into key: value pieces
        parts = []
        for k, v in info.items():
            parts.append(f"{k}: {_format_auth0_error(v)}")
        return "; ".join(parts)
    # Fallback
    try:
        return str(info)
    except Exception:
        return repr(info)


def _error_has_keywords(info, keywords):
    s = _format_auth0_error(info).lower()
    return any(kw in s for kw in keywords)

class CarParkingApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Car-Parking System")
        self.root.geometry("800x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#0f172a')
        # Local users file (store credentials + selected passes)
        self.users_file = "users.json"
        self.load_users()

        # Show login page
        self.show_login_page()

    def load_users(self):
        """Load users from local JSON file. Stored format:
        { username: {"password": ..., "form": ...}, ... }
        """
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}
        # Normalize old-format where value might be a plain password string
        # New canonical structure: { username: {"password": ..., "passes": ["form 1", ...] } }
        normalized = {}
        for k, v in data.items():
            if isinstance(v, dict):
                # If old dict used 'form' key, convert to 'passes' list
                if 'passes' in v:
                    normalized[k] = v
                elif 'form' in v:
                    normalized[k] = {"password": v.get('password', ''), "passes": [v.get('form')]}
                else:
                    # keep existing dict but ensure passes key exists
                    vv = dict(v)
                    if 'passes' not in vv:
                        vv['passes'] = []
                    normalized[k] = vv
            else:
                normalized[k] = {"password": v, "passes": []}
        self.users = normalized

    def save_users(self):
        """Save current self.users dict to users_file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            # Non-fatal; show a message in console
            print(f"Failed to save users to {self.users_file}: {e}")
    
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
        
        tokens = perform_password_grant(username, password)
        if tokens:
            id_token = tokens.get("id_token")
            self.show_main_page(id_token)
        else:
            messagebox.showerror("Error", "Invalid username or password!")
    
    def show_new_user_page(self):
        """Display the new user registration page"""
        self.clear_window()
        self.root.configure(bg='#1e1b4b')  # Deep indigo background
        
        # Title
        title_label = tk.Label(self.root, text="New User Registration", font=("Arial", 26, "bold"), bg='#1e1b4b', fg='#a78bfa')
        title_label.pack(pady=35)
        
        subtitle_label = tk.Label(self.root, text="Create Your Account", font=("Arial", 14), bg='#1e1b4b', fg='#c4b5fd')
        subtitle_label.pack(pady=5)
        
        # Registration Frame
        reg_frame = tk.Frame(self.root, bg='#312e81', relief=tk.RAISED, borderwidth=2)
        reg_frame.pack(pady=25, padx=25, fill=tk.BOTH)
        
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

        # Passes selection - allow multiple passes via checkboxes
        pass_label = tk.Label(inner_frame, text="Passes:", font=("Arial", 14, "bold"), bg='#312e81', fg='#e0e7ff')
        pass_label.grid(row=4, column=0, sticky='nw', pady=12, padx=10)

        # Create a small frame to hold checkboxes
        passes_frame = tk.Frame(inner_frame, bg='#312e81')
        passes_frame.grid(row=4, column=1, pady=12, padx=10, sticky='w')

        self.pass_options = ["staff", "Green Commuter", "Silver Commuter", "Residence hall maroon", "ADA"]
        self.new_pass_vars = {}
        for i, opt in enumerate(self.pass_options):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(passes_frame, text=opt, variable=var, bg='#312e81', fg='#e0e7ff', selectcolor='#4c1d95', activebackground='#312e81')
            cb.grid(row=i//2, column=i%2, sticky='w', padx=6, pady=2)
            self.new_pass_vars[opt] = var
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
        # Collect selected passes (from checkboxes). If none selected, fall back to single 'form' choice
        selected_passes = []
        try:
            for opt, var in getattr(self, 'new_pass_vars', {}).items():
                if var.get():
                    selected_passes.append(opt)
        except Exception:
            selected_passes = []

        
        if not username or not password or not confirm:
            messagebox.showerror("Error", "Please fill in all fields!")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return
        
        try:
            create_user(username, password, os.getenv("AUTH0_REALM", "Username-Password-Authentication"))
        except Auth0Error as e:
            info = e.info if hasattr(e, 'info') else {}
            # Format error into readable text
            formatted = _format_auth0_error(info)
            # Detect common cases
            if _error_has_keywords(formatted, ["invalid"]):
                user_msg = "Username already exists!"
            elif _error_has_keywords(formatted, ["length"]):
                user_msg = "Weak password: must have: 8 characters, a number, a capital letter, and a symbol."
            elif _error_has_keywords(formatted, ["email"]):
                user_msg = "Username must be an email!"
            else:
                # Generic fallback shows the formatted message
                user_msg = formatted or "Failed to create user"

            try:
                self.users[username] = {"password": password, "passes": selected_passes}
                self.save_users()
            except Exception as e:
                print("Warning: failed to save local user info:", e)

            messagebox.showerror("Error", f"Failed to create user: {user_msg}")
            return

        # Persist locally as well
        try:
            self.users[username] = {"password": password, "passes": selected_passes}
            self.save_users()
        except Exception as e:
            print("Warning: failed to save local user info:", e)

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
