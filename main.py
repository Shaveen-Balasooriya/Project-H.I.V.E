import platform
import subprocess
import secrets
import time
import sys
import os
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

# Get the absolute path to the project directory and token files
PROJECT_DIR = Path(__file__).parent.absolute()
TOKEN_FILE = PROJECT_DIR / "frontend" / "token.txt"
TOKEN_EXPIRY_FILE = PROJECT_DIR / "frontend" / "token_expiry.txt"


def is_admin():
    """Check if the current user has administrator/root privileges."""
    system = platform.system()
    if system == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            print(f"[!] Error checking admin status: {e}")
            return False
    else:  # Linux/Unix systems
        try:
            return os.geteuid() == 0
        except AttributeError:
            print("[!] Could not determine admin status on this platform.")
            return False


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def write_token_to_file(token, expiry_minutes):
    """Write the access token and its expiry time to files."""
    # Ensure we're using absolute paths
    token_file = PROJECT_DIR / "frontend" / "token.txt" 
    expiry_file = PROJECT_DIR / "frontend" / "token_expiry.txt"
    
    print(f"[*] Writing token to: {token_file}")
    
    # Create the frontend directory if it doesn't exist
    os.makedirs(os.path.dirname(token_file), exist_ok=True)
    
    try:
        # Remove existing token files if they exist
        if os.path.exists(token_file):
            os.remove(token_file)
        if os.path.exists(expiry_file):
            os.remove(expiry_file)
            
        # Write new token files
        with open(token_file, "w") as f:
            f.write(token)
        
        expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
        with open(expiry_file, "w") as f:
            f.write(expiry_time.isoformat())
        
        # Verify the files were created
        if os.path.exists(token_file) and os.path.exists(expiry_file):
            print(f"[+] Token files created successfully")
            return True
        else:
            print(f"[!] Token files were not created properly")
            return False
    except Exception as e:
        print(f"[!] Error writing token files: {e}")
        return False


def start_services(duration_minutes, token):
    """Start the Flask frontend and optionally other services."""
    print(f"\n[+] Starting services for {duration_minutes} minutes...")

    # Get proper Python executable
    python_cmd = "python" if platform.system() == "Windows" else "python3"
    
    # Get absolute paths
    flask_app_path = PROJECT_DIR / "frontend" / "app.py"
    frontend_dir = PROJECT_DIR / "frontend"
    
    # Set the Flask environment variables
    env = os.environ.copy()
    env["FLASK_APP"] = str(flask_app_path)
    env["FLASK_ENV"] = "development"  # Use development mode for better error reporting
    
    # Also make sure PYTHONPATH includes our project directory
    env["PYTHONPATH"] = str(PROJECT_DIR)
    
    # Start Flask frontend using flask run, which is more reliable than directly executing the script
    try:
        # Method 1: Try running with 'flask run'
        try:
            cmd = [python_cmd, "-m", "flask", "run", "--no-reload"]
            print(f"[+] Starting Flask with command: {' '.join(cmd)}")
            
            # Create a log file for stdout/stderr
            log_path = PROJECT_DIR / "flask_output.log"
            with open(log_path, 'w') as log_file:
                frontend_proc = subprocess.Popen(
                    cmd,
                    env=env,
                    cwd=str(frontend_dir),
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
                print(f"[+] Flask process started (PID: {frontend_proc.pid})")
                print(f"[+] Log file: {log_path}")
        except Exception as e:
            # Method 2: Fall back to direct Python execution if flask run fails
            print(f"[!] Failed to start Flask with module approach: {e}")
            print("[*] Falling back to direct Python execution...")
            
            cmd = [python_cmd, str(flask_app_path)]
            print(f"[+] Starting Flask with command: {' '.join(cmd)}")
            
            # Create a log file for stdout/stderr
            log_path = PROJECT_DIR / "flask_output.log"
            with open(log_path, 'w') as log_file:
                frontend_proc = subprocess.Popen(
                    cmd,
                    env=env,
                    cwd=str(frontend_dir),
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
                print(f"[+] Flask process started (PID: {frontend_proc.pid})")
                print(f"[+] Log file: {log_path}")
        
        # Give Flask a moment to start up - longer this time
        time.sleep(5)
        
        # Try to verify Flask is running by making a request
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:5000/")
            print("[+] Flask application is running successfully")
        except Exception as e:
            print(f"[!] Warning: Could not verify Flask is running: {e}")
            print("[!] The application may still be starting up...")
            print("[!] If browser doesn't connect, please open Flask logs or manually run flask app.py")
        
        # Generate the access URL with token
        access_url = f"http://localhost:5000/access?token={token}"
        print(f"[+] Access URL: {access_url}")
        
        # Try to open the browser automatically
        try:
            webbrowser.open(access_url)
            print("[+] Opening browser automatically...")
        except Exception as e:
            print(f"[!] Could not open browser: {e}")
            print("[+] Please copy and paste the URL into your browser manually.")
        
        print(f"[+] Session will expire in {duration_minutes} minutes.")
        print("[+] Press Ctrl+C to terminate services early.")
        
        try:
            # Keep the script running until duration expires or user interrupts
            time.sleep(duration_minutes * 60)
        except KeyboardInterrupt:
            print("\n[+] User interrupted. Shutting down services...")
        
        # Clean up
        print("[+] Terminating Flask server...")
        frontend_proc.terminate()
        try:
            # Wait up to 5 seconds for graceful shutdown
            frontend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            print("[!] Flask server didn't terminate gracefully, forcing...")
            frontend_proc.kill()
        
        clean_up_token_files()
        print("[+] Dashboard session ended. Services terminated.")
        
    except Exception as e:
        print(f"[!] Error starting Flask: {e}")
        clean_up_token_files()
        sys.exit(1)


def clean_up_token_files():
    """Remove token files after session ends."""
    try:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        if os.path.exists(TOKEN_EXPIRY_FILE):
            os.remove(TOKEN_EXPIRY_FILE)
        print("[+] Token files cleaned up.")
    except Exception as e:
        print(f"[!] Error removing token files: {e}")


if __name__ == "__main__":
    print("\n== Project H.I.V.E Secure Launcher ==")
    print("(Services will only start with admin privileges)\n")

    # Check for admin privileges first
    if not is_admin():
        print("[!] You must run this as an administrator/root.")
        print("    On Windows: Right-click and select 'Run as administrator'")
        print("    On Linux: Run with 'sudo'")
        sys.exit(1)
    
    print("[+] Admin privileges confirmed!")

    # Session duration selection
    print("\nSelect session duration:")
    print("1. 15 minutes")
    print("2. 30 minutes")
    print("3. 45 minutes")
    print("4. 60 minutes")

    choice = input("Enter choice (1-4) [default=2]: ").strip() or "2"
    durations = {"1": 15, "2": 30, "3": 45, "4": 60}
    duration = durations.get(choice, 30)  # Default to 30 minutes

    # Generate access token
    token = generate_token()
    if not write_token_to_file(token, duration):
        print("[!] Failed to create token files. Exiting.")
        sys.exit(1)

    print(f"\n[+] Access Token: {token}")
    print("[!] This token will be used to authenticate your browser session.")

    # Start services with the generated token
    start_services(duration, token)
