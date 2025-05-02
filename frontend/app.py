import os
from flask import Flask
from frontend.routes import frontend

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(frontend)
    
    # Configure any app settings
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-project-hive')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
