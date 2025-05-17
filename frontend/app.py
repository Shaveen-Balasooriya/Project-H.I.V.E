import os
import requests
import json
from flask import Flask, jsonify, request
from frontend.routes import frontend
from requests.exceptions import RequestException

# --- FORCE BACKEND_URL TO 8081 ---
BACKEND_URL = 'http://localhost:8081'
print(f"[HIVE] Using BACKEND_URL for honeypot manager: {BACKEND_URL}")

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(frontend)
    
    # Configure any app settings
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-project-hive')
    return app

app = create_app()

@app.route('/api/honeypot/port-check/<port>', methods=['GET'])
def proxy_port_check(port):
    """Proxy port check requests to the backend with error handling"""
    try:
        response = requests.get(f"{BACKEND_URL}/honeypot_manager/port-check/{port}", timeout=5)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        app.logger.error(f"Error checking port availability via proxy: {e}")
        # Return a specific error structure the frontend expects
        return jsonify({
            "available": False,
            "message": f"Backend connection error: {str(e)}. Could not verify port {port}."
        }), 503 # Service Unavailable

@app.route('/api/honeypot/types', methods=['GET'])
def proxy_honeypot_types():
    """Proxy honeypot types requests to the backend with error handling"""
    try:
        response = requests.get(f"{BACKEND_URL}/honeypot_manager/types", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        app.logger.error(f"Error getting honeypot types via proxy: {e}")
        # Return a fallback list of types when backend is down
        return jsonify(["ssh", "ftp", "http"]), 503 # Service Unavailable

@app.route('/api/honeypot/types/<honeypot_type>/auth-details', methods=['GET'])
def proxy_honeypot_auth_details(honeypot_type):
    """Proxy honeypot authentication details requests with error handling"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/honeypot_manager/types/{honeypot_type}/auth-details",
            timeout=5
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        app.logger.error(f"Error getting honeypot auth details via proxy: {e}")

        # Return fallback defaults based on type
        if honeypot_type == "ssh":
            banner = "SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3"
        elif honeypot_type == "ftp":
            banner = "220 ProFTPD 1.3.5e Server [ftp.example.com] FTP server ready"
        else:
            banner = f"Welcome to {honeypot_type.upper()} Server"

        return jsonify({
            "authentication": {
                "allowed_users": [
                    {"username": "admin", "password": "admin123"},
                    {"username": "root", "password": "toor"},
                    {"username": "user", "password": "password"}
                ]
            },
            "banner": banner
        }), 503 # Service Unavailable

@app.route('/api/honeypot', methods=['POST'])
def create_honeypot():
    """Create a new honeypot with error handling"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/honeypot_manager/",
            json=request.json,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        app.logger.error(f"Error creating honeypot via proxy: {e}")
        error_detail = f"Backend connection error: {str(e)}"
        try:
            if e.response is not None and e.response.content:
                error_detail = e.response.json().get("detail", error_detail)
        except json.JSONDecodeError:
            if e.response is not None:
                error_detail = e.response.text
        except Exception as parse_exc:
            app.logger.error(f"Error parsing error response: {parse_exc}")

        return jsonify({"detail": error_detail}), 503 # Service Unavailable

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
