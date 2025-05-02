from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_from_directory, abort, current_app
import requests
from requests.exceptions import RequestException
import os
import traceback

frontend = Blueprint('frontend', __name__, template_folder='templates')

# Base URL of the FastAPI honeypot-manager service with environment variable support
API_BASE = os.getenv('HONEYPOT_MANAGER_API', 'http://localhost:8081/honeypot_manager')

# Status mapping for consistent display
STATUS_MAPPING = {
    'running': 'started',  # Map 'running' to 'started' for consistency
    'created': 'created',
    'exited': 'exited',
    'stopped': 'stopped'   # Adding for completeness
}

# Favicon route
@frontend.route('/favicon.ico')
def favicon():
    """Serve favicon directly"""
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return send_from_directory(os.path.join(static_path, 'images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@frontend.route('/')
def index():
    """Main dashboard page."""
    return redirect(url_for('frontend.honeypot_manager'))

@frontend.route('/honeypot_manager')
def honeypot_manager():
    """Honeypot manager page with filtering options."""
    # Fetch honeypot types for filter dropdown
    honeypot_types = []
    try:
        types_resp = requests.get(f"{API_BASE}/types", timeout=5)
        if types_resp.ok:
            honeypot_types = types_resp.json()
    except RequestException as e:
        print(f"API Error fetching honeypot types: {e}")
    
    # Get filter parameters from query string
    selected_type = request.args.get('type', '')
    selected_status = request.args.get('status', '')

    # Query honeypots from backend with filters applied
    honeypots = []
    try:
        # Handle different filter combinations
        if selected_type and selected_status:
            # First get by type, then filter by status in-memory
            resp = requests.get(f"{API_BASE}/type/{selected_type}", timeout=5)
            if resp.ok:
                all_hp = resp.json()
                honeypots = [hp for hp in all_hp if STATUS_MAPPING.get(hp.get('status')) == selected_status]
        elif selected_type:
            resp = requests.get(f"{API_BASE}/type/{selected_type}", timeout=5)
            if resp.ok:
                honeypots = resp.json()
        elif selected_status:
            resp = requests.get(f"{API_BASE}/status/{selected_status}", timeout=5)
            if resp.ok:
                honeypots = resp.json()
        else:
            # No filters: get all honeypots
            resp = requests.get(f"{API_BASE}", timeout=5)
            if resp.ok:
                honeypots = resp.json()
    except RequestException as e:
        print(f"API Error fetching honeypots: {e}")
        traceback.print_exc()

    return render_template(
        'pages/honeypot_manager.html',
        honeypot_types=honeypot_types,
        honeypots=honeypots,
        selected_type=selected_type,
        selected_status=selected_status
    )

@frontend.route('/create-honeypot')
def create_honeypot():
    """Dedicated page for creating a honeypot."""
    # Fetch honeypot types for dropdown
    honeypot_types = []
    error = None
    
    try:
        types_resp = requests.get(f"{API_BASE}/types", timeout=5)
        if types_resp.ok:
            honeypot_types = types_resp.json()
        else:
            error = f"Failed to fetch honeypot types: API returned status {types_resp.status_code}"
    except RequestException as e:
        error = f"API Error fetching honeypot types: {e}"
        print(error)
        traceback.print_exc()
    
    # If we couldn't fetch honeypot types, show an error message
    if error:
        return render_template('error.html', 
                              error_code=500, 
                              error_message="Failed to load honeypot creation page. Please try again later.")
    
    return render_template('pages/create_honeypot.html', honeypot_types=honeypot_types)

@frontend.route('/honeypot_cards')
def honeypot_cards():
    """Return only the honeypot cards HTML for AJAX refresh."""
    # Get filter parameters from query string
    selected_type = request.args.get('type', '')
    selected_status = request.args.get('status', '')

    # Query honeypots from backend with filters applied
    honeypots = []
    try:
        # Handle different filter combinations
        if selected_type and selected_status:
            # First get by type, then filter by status in-memory
            resp = requests.get(f"{API_BASE}/type/{selected_type}", timeout=5)
            if resp.ok:
                all_hp = resp.json()
                honeypots = [hp for hp in all_hp if STATUS_MAPPING.get(hp.get('status')) == selected_status]
        elif selected_type:
            resp = requests.get(f"{API_BASE}/type/{selected_type}", timeout=5)
            if resp.ok:
                honeypots = resp.json()
        elif selected_status:
            resp = requests.get(f"{API_BASE}/status/{selected_status}", timeout=5)
            if resp.ok:
                honeypots = resp.json()
        else:
            # No filters: get all honeypots
            resp = requests.get(f"{API_BASE}", timeout=5)
            if resp.ok:
                honeypots = resp.json()
    except RequestException as e:
        print(f"API Error fetching honeypots: {e}")
        traceback.print_exc()

    # Render just the honeypot cards partial template
    return render_template(
        'partials/honeypot_cards.html',
        honeypots=honeypots
    )

# Placeholder pages
@frontend.route('/settings')
def settings():
    """Settings page placeholder."""
    environment = os.environ.get('FLASK_ENV', 'development')
    return render_template('pages/settings.html', environment=environment)

# API Proxy Routes
@frontend.route('/api/honeypot', methods=['POST'])
def create_honeypot_api():
    """Proxy POST requests to create a honeypot to the backend API."""
    try:
        print("Received honeypot creation request:", request.json)
        response = requests.post(
            f"{API_BASE}/",
            json=request.json,
            headers={'Content-Type': 'application/json'},
            timeout=10  # Increased timeout for creation operations
        )
        print(f"API response status: {response.status_code}")
        print(f"API response body: {response.text}")
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        print(f"Error creating honeypot: {e}")
        traceback.print_exc()
        return jsonify({"detail": str(e)}), 500

@frontend.route('/api/honeypot/<honeypot_name>', methods=['DELETE'])
def delete_honeypot(honeypot_name):
    """Proxy DELETE requests to delete a honeypot to the backend API."""
    try:
        print(f"Deleting honeypot: {honeypot_name}")
        response = requests.delete(f"{API_BASE}/{honeypot_name}", timeout=10)
        print(f"API response status: {response.status_code}")
        print(f"API response body: {response.text}")
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        print(f"Error deleting honeypot: {e}")
        traceback.print_exc()
        return jsonify({"detail": str(e)}), 500

@frontend.route('/api/honeypot/<honeypot_name>/<honeypot_action>', methods=['POST'])
def manage_honeypot(honeypot_name, honeypot_action):
    """Proxy lifecycle management operations (start/stop/restart) to the backend API."""
    if honeypot_action not in ['start', 'stop', 'restart']:
        return jsonify({"detail": "Invalid action"}), 400
    
    try:
        print(f"Performing action {honeypot_action} on honeypot: {honeypot_name}")
        response = requests.post(f"{API_BASE}/{honeypot_name}/{honeypot_action}", timeout=10)
        print(f"API response status: {response.status_code}")
        print(f"API response body: {response.text}")
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        print(f"Error performing {honeypot_action} on honeypot: {e}")
        traceback.print_exc()
        return jsonify({"detail": str(e)}), 500

# Authentication details endpoints
@frontend.route('/api/honeypot/type/<honeypot_type>/auth-details', methods=['GET'])
def get_honeypot_auth_details(honeypot_type):
    """Proxy requests to get authentication details for a specific honeypot type."""
    try:
        response = requests.get(f"{API_BASE}/types/{honeypot_type}/auth-details", timeout=5)
        if response.status_code == 404:
            # Return default empty structure if endpoint doesn't exist
            return jsonify({
                "banner": f"Welcome to {honeypot_type.upper()} server",
                "authentication": {
                    "allowed_users": [
                        {"username": "admin", "password": "admin123"},
                        {"username": "root", "password": "toor"},
                        {"username": "user", "password": "password"}
                    ]
                }
            }), 200
        return jsonify(response.json()), response.status_code
    except Exception as e:
        # Return default structure on error
        return jsonify({
            "banner": f"Welcome to {honeypot_type.upper()} server",
            "authentication": {
                "allowed_users": [
                    {"username": "admin", "password": "admin123"},
                    {"username": "root", "password": "toor"},
                    {"username": "user", "password": "password"}
                ]
            }
        }), 200

@frontend.route('/api/honeypot/types', methods=['GET'])
def get_honeypot_types():
    """Proxy requests to get all available honeypot types."""
    try:
        response = requests.get(f"{API_BASE}/types", timeout=5)
        return jsonify(response.json()), response.status_code
    except RequestException as e:
        print(f"Error fetching honeypot types: {e}")
        return jsonify({"detail": str(e)}), 500

@frontend.route('/honeypot/<n>')
def honeypot_details(n):
    """Render the honeypot details page."""
    try:
        # Get honeypot details
        response = requests.get(f"{API_BASE}/name/{n}")
        
        if response.status_code == 200:
            honeypot = response.json()
            return render_template('pages/honeypot_details.html', honeypot=honeypot)
        else:
            # Honeypot not found
            return render_template('error.html', 
                                 error_code=404, 
                                 error_message=f"Honeypot '{n}' not found")
    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error loading honeypot details: {str(e)}")
        return render_template('error.html', 
                              error_code=500, 
                              error_message="Could not load honeypot details")
