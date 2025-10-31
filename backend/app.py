# backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes.clients import clients_bp
from routes.data import data_bp

# Validate configuration
try:
    Config.validate()
    print("✅ Configuration validated")
except ValueError as e:
    print(f"\n❌ Configuration Error: {e}\n")
    exit(1)

# Create Flask app
app = Flask(__name__)

# IMPORTANT: Disable strict slashes to prevent 308 redirects
app.url_map.strict_slashes = False

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": Config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Register blueprints
app.register_blueprint(clients_bp, url_prefix='/api/clients')
app.register_blueprint(data_bp, url_prefix='/api/data')


# Root routes
@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'success': True,
        'message': 'eGauge Management API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'clients': '/api/clients',
            'extract_data': '/api/data/extract'
        },
        'documentation': f'Frontend available at http://localhost:3000'
    })


@app.route('/api', methods=['GET'])
def api_root():
    """API root endpoint"""
    return jsonify({
        'success': True,
        'message': 'eGauge Management API',
        'version': '1.0.0'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'API is running',
        'supabase_connected': True
    })


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 Starting eGauge Management API")
    print("="*80)
    print(f"Supabase URL: {Config.SUPABASE_URL}")
    print(f"eGauge User: {Config.EGAUGE_USER}")
    print(f"Running on: http://localhost:{Config.PORT}")
    print("="*80 + "\n")
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
