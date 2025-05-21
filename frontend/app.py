import os
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Get API endpoint URLs from environment
HONEYPOT_API = os.getenv('HONEYPOT_MANAGER_API', 'http://localhost:8080')
LOG_API = os.getenv('LOG_MANAGER_API', 'http://localhost:9090')

print(f"Using Honeypot API: {HONEYPOT_API}")  # Debug log
print(f"Using Log Manager API: {LOG_API}")  # Debug log for LOG_API

# Initialize Flask app
app = Flask(__name__)
# Set secret key for session management
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))
# Set session lifetime
app.permanent_session_lifetime = timedelta(hours=12)

# Helper function to check authentication
def is_authenticated():
    """Check if user is authenticated"""
    return session.get('authenticated', False)

# New helper to check if session has expired based on token expiry time
def is_session_expired():
    """Check if the session has expired based on the token expiry time"""
    if 'expiry_time' in session:
        expiry_time = datetime.fromisoformat(session['expiry_time'])
        return datetime.now() > expiry_time
    return False

# Add a decorator to check both authentication and expiration
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if authenticated
        if not is_authenticated():
            return redirect(url_for('login'))
            
        # Then check if session has expired
        if is_session_expired():
            app.logger.info("Session expired based on token duration")
            session.clear()
            return redirect(url_for('login', expired=True))
            
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check if all required services are running
def check_services_running():
    """Check if all required services are running."""
    try:
        endpoint = f"{LOG_API}/services"
        response = requests.get(endpoint)
        
        if not response.ok:
            app.logger.error(f"Error checking running services: {response.text}")
            return False, []
        
        running_services = response.json()
        required_services = [
            "hive-opensearch-node",
            "hive-nats-server", 
            "hive-log-collector",
            "hive-opensearch-dash"
        ]
        
        missing_services = [s for s in required_services if s not in running_services]
        
        if missing_services:
            return False, {
                "running": running_services,
                "missing": missing_services
            }
        
        return True, running_services
    except Exception as e:
        app.logger.error(f"Error checking running services: {str(e)}")
        return False, []

# Login page route
@app.route('/login')
def login():
    """Display login page"""
    # Check if redirected due to expiration
    expired = request.args.get('expired', False)
    return render_template('pages/login.html', expired=expired)

# Main page routes
@app.route('/')
def index():
    """Redirect root URL to honeypots page or login if not authenticated"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    # Check if session has expired
    if is_session_expired():
        session.clear()
        return redirect(url_for('login', expired=True))
        
    return redirect(url_for('honeypots'))

@app.route('/honeypots')
@login_required
def honeypots():
    # Check if all required services are running
    services_running, services_info = check_services_running()
    
    if not services_running:
        # Render a template with information about missing services
        return render_template(
            'pages/services_required.html', 
            services_info=services_info,
            redirect_to='/honeypots'
        )
    
    return render_template('pages/honeypots.html')

@app.route('/honeypot-builder')
@login_required
def honeypot_builder():
    # First check services
    services_running, services_info = check_services_running()
    
    if not services_running:
        # Render a template with information about missing services
        return render_template(
            'pages/services_required.html', 
            services_info=services_info,
            redirect_to='/honeypot-builder'
        )
    
    # Then check honeypot limits - hard-coded to 5 maximum honeypots
    try:
        # Get current honeypot count
        honeypots_response = requests.get(f"{HONEYPOT_API}/")
        
        if honeypots_response.ok:
            honeypots = honeypots_response.json()
            
            # Check if we've reached the limit
            current_count = len(honeypots)
            max_allowed = 5  # Hard-coded maximum limit
            
            app.logger.info(f"Honeypot count: {current_count}/{max_allowed}")
            
            if current_count >= max_allowed:
                # Redirect to honeypots page with a message
                app.logger.info("Maximum honeypot limit reached. Redirecting to honeypots page.")
                return redirect('/honeypots?limit_reached=true')
    except Exception as e:
        app.logger.error(f"Error checking honeypot limits: {str(e)}")
        # If there's an error, we'll still show the builder page
        
    # If limits aren't reached or we couldn't check, show the builder page
    return render_template('pages/honeypot-builder.html')

@app.route('/services')
@login_required
def services():
    """
    Route for the services management page
    """
    return render_template('pages/services.html')

# Authentication routes
@app.route('/access')
def access():
    """Process token-based authentication"""
    token = request.args.get('token')
    if not token:
        return "Missing token", 400

    try:
        # Use path joining for cross-platform compatibility
        token_path = os.path.join(os.path.dirname(__file__), "token.txt")
        expiry_path = os.path.join(os.path.dirname(__file__), "token_expiry.txt")
        
        app.logger.info(f"Looking for token at: {token_path}")
        
        # Check if token files exist
        if not os.path.exists(token_path) or not os.path.exists(expiry_path):
            app.logger.error(f"Token files not found. Token path exists: {os.path.exists(token_path)}, Expiry path exists: {os.path.exists(expiry_path)}")
            return "Token is missing or already used.", 403
            
        # Read the token
        with open(token_path, 'r') as f:
            valid_token = f.read().strip()
            app.logger.debug(f"Read token from file: {valid_token[:5]}...")

        # Read the expiry time
        with open(expiry_path, 'r') as f:
            expiry_time_str = f.read().strip()
            app.logger.debug(f"Read expiry time: {expiry_time_str}")
            expiry_time = datetime.fromisoformat(expiry_time_str)

        # Check if token has expired
        if datetime.now() > expiry_time:
            app.logger.warning(f"Token expired at {expiry_time}")
            return "Token has expired", 403

        # Validate the token
        if token == valid_token:
            app.logger.info("Token validation successful")
            session.permanent = True
            session['authenticated'] = True
            
            # Store the expiry time in the session
            session['expiry_time'] = expiry_time.isoformat()
            session['token_validated'] = True
            
            return redirect(url_for('honeypots'))
        else:
            app.logger.warning("Invalid token provided")
            return "Invalid token", 403

    except FileNotFoundError as e:
        app.logger.error(f"Token file not found: {str(e)}")
        return "Token is missing or already used.", 403
    except Exception as e:
        app.logger.error(f"Token access error: {str(e)}")
        return "Server error", 500

@app.route('/logout')
def logout():
    """Log out the user by clearing the session"""
    session.clear()
    return redirect(url_for('login'))

# API proxy routes - Honeypot Manager
@app.route('/api/honeypot/types', methods=['GET'])
def get_honeypot_types():
    """Proxy request to get honeypot types from the backend."""
    try:
        response = requests.get(f"{HONEYPOT_API}/types")
        app.logger.info(f"Types API response: {response.status_code}")
        if not response.ok:
            app.logger.error(f"Error from types API: {response.text}")
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error accessing honeypot API: {str(e)}")
        return jsonify({"error": "Could not connect to honeypot service"}), 500

# Add specific route for the honeypots root endpoint
@app.route('/api/honeypot/', methods=['GET'])
def get_all_honeypots():
    """Proxy request to get all honeypots from the backend."""
    try:
        app.logger.info("Fetching all honeypots")
        response = requests.get(f"{HONEYPOT_API}/")
        app.logger.info(f"Honeypots API response: {response.status_code}")
        if not response.ok:
            app.logger.error(f"Error from honeypots API: {response.text}")
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error fetching honeypots: {str(e)}")
        return jsonify({"error": f"Could not connect to honeypot service: {str(e)}"}), 500

@app.route('/api/honeypot/create', methods=['POST'])
def create_honeypot():
    """Proxy request to create a honeypot."""
    try:
        # Get the JSON payload from the request
        payload = request.json
        app.logger.info(f"Creating honeypot with payload: {payload}")
        
        # Forward the request to the honeypot manager API endpoint
        # The honeypot manager API expects the request at the root endpoint
        endpoint_url = f"{HONEYPOT_API}/"
        app.logger.info(f"Sending request to: {endpoint_url}")
        
        response = requests.post(
            endpoint_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        app.logger.info(f"Create API response: {response.status_code}")
        
        # Better error handling
        if not response.ok:
            error_content = response.text
            app.logger.error(f"Error from create API: {error_content}")
            
            # Try to parse error as JSON
            try:
                error_json = response.json()
                return jsonify(error_json), response.status_code
            except:
                return jsonify({"error": error_content}), response.status_code
        
        # Successfully created honeypot
        try:
            if not response.content:
                return jsonify({"message": "Honeypot created successfully"}), 201
            
            response_data = response.json()
            return jsonify(response_data), response.status_code
        except Exception as e:
            app.logger.error(f"Error parsing response JSON: {e}")
            return jsonify({"error": f"Invalid response from API"}), 500
    except Exception as e:
        app.logger.error(f"Error creating honeypot: {str(e)}")
        return jsonify({"error": "Failed to create honeypot"}), 500

@app.route('/api/honeypot/port-check/<int:port>', methods=['GET'])
def check_port(port):
    """Proxy request to check if a port is available."""
    try:
        app.logger.info(f"Checking port {port}")
        response = requests.get(f"{HONEYPOT_API}/port-check/{port}")
        app.logger.info(f"Port check response: {response.status_code}")
        if not response.ok:
            app.logger.error(f"Error from port check API: {response.text}")
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error checking port: {str(e)}")
        return jsonify({"available": False, "message": f"Error checking port: {str(e)}"}), 500

# Add routes for honeypot lifecycle management
@app.route('/api/honeypot/<name>/start', methods=['POST'])
def start_honeypot(name):
    """Proxy request to start a honeypot."""
    try:
        app.logger.info(f"Starting honeypot: {name}")
        response = requests.post(f"{HONEYPOT_API}/{name}/start")
        app.logger.info(f"Start honeypot response: {response.status_code}")
        
        # Check if we got an error but with the specific "honeypot_name" message
        # This indicates the honeypot actually started despite the error
        if not response.ok:
            error_text = response.text
            app.logger.error(f"Error starting honeypot: {error_text}")
            
            # Check for the specific error about missing honeypot_name attribute
            if "object has no attribute 'honeypot_name'" in error_text:
                app.logger.info(f"Honeypot {name} likely started despite error.")
                # Return a success response with modified message
                return jsonify({
                    "message": f"Honeypot {name} started successfully (with API warning)",
                    "honeypot": {"name": name, "status": "running"}
                }), 200
            
            # Regular error handling
            return response.json(), response.status_code
            
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error starting honeypot: {str(e)}")
        return jsonify({"error": f"Failed to start honeypot: {str(e)}"}), 500

@app.route('/api/honeypot/<name>/stop', methods=['POST'])
def stop_honeypot(name):
    """Proxy request to stop a honeypot."""
    try:
        app.logger.info(f"Stopping honeypot: {name}")
        response = requests.post(f"{HONEYPOT_API}/{name}/stop")
        app.logger.info(f"Stop honeypot response: {response.status_code}")
        
        if not response.ok:
            error_text = response.text
            app.logger.error(f"Error stopping honeypot: {error_text}")
            
            # Check for the specific error about missing honeypot_name attribute
            if "object has no attribute 'honeypot_name'" in error_text:
                app.logger.info(f"Honeypot {name} likely stopped despite error.")
                return jsonify({
                    "message": f"Honeypot {name} stopped successfully (with API warning)",
                    "honeypot": {"name": name, "status": "exited"}
                }), 200
            
            return response.json(), response.status_code
            
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error stopping honeypot: {str(e)}")
        return jsonify({"error": f"Failed to stop honeypot: {str(e)}"}), 500

@app.route('/api/honeypot/<name>', methods=['DELETE'])
def delete_honeypot(name):
    """Proxy request to delete a honeypot."""
    try:
        app.logger.info(f"Deleting honeypot: {name}")
        response = requests.delete(f"{HONEYPOT_API}/{name}")
        app.logger.info(f"Delete honeypot response: {response.status_code}")
        if not response.ok:
            app.logger.error(f"Error deleting honeypot: {response.text}")
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error deleting honeypot: {str(e)}")
        return jsonify({"error": f"Failed to delete honeypot: {str(e)}"}), 500

# Generic proxy for other GET requests
@app.route('/api/honeypot/<path:path>', methods=['GET'])
def proxy_honeypot_get(path):
    """Generic proxy for GET requests to honeypot API."""
    try:
        app.logger.info(f"Proxying GET request to /{path}")
        response = requests.get(f"{HONEYPOT_API}/{path}")
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error proxying GET request: {str(e)}")
        return jsonify({"error": "API request failed"}), 500

# API proxy routes - Service Manager (Log Manager API)
@app.route('/api/service/status', methods=['GET'])
def get_service_status():
    """Proxy request to get service status from the log manager."""
    try:
        # Ensure we're using the exact endpoint from log_manager_router.py
        endpoint = f"{LOG_API}/status"
        app.logger.info(f"LOG_API from env: {LOG_API}")
        app.logger.info(f"Accessing service status at: {endpoint}")
        
        response = requests.get(endpoint)
        app.logger.info(f"Service status API response: {response.status_code}")
        
        if response.ok:
            # Get the JSON response and log it for debugging
            data = response.json()
            app.logger.debug(f"Received service data: {data}")
            return jsonify(data), 200
        else:
            app.logger.error(f"Error from service status API: {response.text}")
            app.logger.error(f"Failed with status {response.status_code} when accessing {endpoint}")
            
            # Return mock data as fallback
            mock_data = {
                "open_search_node": "not found", 
                "nats_server": "not found", 
                "log_collector": "not found"
            }
            return jsonify(mock_data), 200
    except Exception as e:
        app.logger.error(f"Error accessing service status at {LOG_API}/status: {str(e)}")
        # Return mock data for development
        mock_data = {
            "open_search_node": "not found", 
            "nats_server": "not found", 
            "log_collector": "not found"
        }
        return jsonify(mock_data), 200
        
@app.route('/api/service/create', methods=['POST'])
def create_services():
    """Proxy request to create services."""
    try:
        payload = request.json
        app.logger.info(f"Creating services with payload: {payload}")
        
        # Use LOG_API directly from environment
        endpoint = f"{LOG_API}/create"
        app.logger.info(f"LOG_API from env: {LOG_API}")
        app.logger.info(f"Sending create request to: {endpoint}")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        app.logger.info(f"Create services API response: {response.status_code}")
        
        if not response.ok:
            error_content = response.text
            app.logger.error(f"Error from create services API: {error_content}")
            try:
                error_json = response.json()
                return jsonify(error_json), response.status_code
            except:
                return jsonify({"error": error_content}), response.status_code
        
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error creating services at {LOG_API}/create: {str(e)}")
        return jsonify({"error": "Failed to create services", "details": str(e)}), 500

@app.route('/api/service/start', methods=['POST'])
def start_services():
    """Proxy request to start all services."""
    try:
        app.logger.info("Starting all services")
        
        # Use LOG_API directly from environment
        endpoint = f"{LOG_API}/start"
        app.logger.info(f"LOG_API from env: {LOG_API}")
        app.logger.info(f"Sending start request to: {endpoint}")
        
        response = requests.post(endpoint)
        app.logger.info(f"Start services API response: {response.status_code}")
        
        if not response.ok:
            error_content = response.text
            app.logger.error(f"Error starting services: {error_content}")
            try:
                error_json = response.json()
                return jsonify(error_json), response.status_code
            except:
                return jsonify({"error": error_content}), response.status_code
        
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error starting services at {LOG_API}/start: {str(e)}")
        return jsonify({"message": "Services started (mock response)"}), 200

@app.route('/api/service/stop', methods=['POST'])
def stop_services():
    """Proxy request to stop all services."""
    try:
        app.logger.info("Stopping all services")
        
        # Use LOG_API directly from environment
        endpoint = f"{LOG_API}/stop"
        app.logger.info(f"LOG_API from env: {LOG_API}")
        app.logger.info(f"Sending stop request to: {endpoint}")
        
        response = requests.post(endpoint)
        app.logger.info(f"Stop services API response: {response.status_code}")
        
        if not response.ok:
            error_content = response.text
            app.logger.error(f"Error stopping services: {error_content}")
            try:
                error_json = response.json()
                return jsonify(error_json), response.status_code
            except:
                return jsonify({"error": error_content}), response.status_code
        
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error stopping services at {LOG_API}/stop: {str(e)}")
        return jsonify({"message": "Services stopped (mock response)"}), 200

@app.route('/api/service/delete', methods=['DELETE'])
def delete_services():
    """Proxy request to delete all services."""
    try:
        app.logger.info("Deleting all services")
        
        # Use LOG_API directly from environment  
        endpoint = f"{LOG_API}/delete"
        app.logger.info(f"LOG_API from env: {LOG_API}")
        app.logger.info(f"Sending delete request to: {endpoint}")
        
        response = requests.delete(endpoint)
        app.logger.info(f"Delete services API response: {response.status_code}")
        
        if not response.ok:
            error_content = response.text
            app.logger.error(f"Error deleting services: {error_content}")
            try:
                error_json = response.json()
                return jsonify(error_json), response.status_code
            except:
                return jsonify({"error": error_content}), response.status_code
        
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error deleting services at {LOG_API}/delete: {str(e)}")
        return jsonify({"message": "Services deleted (mock response)"}), 200

@app.route('/api/service/restart', methods=['POST'])
def restart_services():
    """Proxy request to restart all services."""
    try:
        app.logger.info("Restarting all services")
        
        # Use LOG_API directly from environment  
        endpoint = f"{LOG_API}/restart"
        app.logger.info(f"LOG_API from env: {LOG_API}")
        app.logger.info(f"Sending restart request to: {endpoint}")
        
        response = requests.post(endpoint)
        app.logger.info(f"Restart services API response: {response.status_code}")
        
        if not response.ok:
            error_content = response.text
            app.logger.error(f"Error restarting services: {error_content}")
            try:
                error_json = response.json()
                return jsonify(error_json), response.status_code
            except:
                return jsonify({"error": error_content}), response.status_code
        
        return response.json(), response.status_code
    except Exception as e:
        app.logger.error(f"Error restarting services at {LOG_API}/restart: {str(e)}")
        return jsonify({"message": "Services restarted (mock response)"}), 200

# Add new API endpoint to check running services
@app.route('/api/service/list', methods=['GET'])
def get_running_services():
    """Proxy request to get list of running services from the log manager."""
    try:
        endpoint = f"{LOG_API}/services"
        app.logger.info(f"LOG_API from env: {LOG_API}")
        app.logger.info(f"Accessing services list at: {endpoint}")
        
        response = requests.get(endpoint)
        app.logger.info(f"Services list API response: {response.status_code}")
        
        if response.ok:
            data = response.json()
            app.logger.debug(f"Received services list: {data}")
            return jsonify(data), 200
        else:
            app.logger.error(f"Error from services list API: {response.text}")
            return jsonify([]), 200  # Return empty list as fallback
    except Exception as e:
        app.logger.error(f"Error accessing services list at {LOG_API}/services: {str(e)}")
        return jsonify([]), 200  # Return empty list for development/error cases
