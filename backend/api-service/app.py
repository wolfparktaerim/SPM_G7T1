# backend/api-gateway/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)

# Configure CORS for frontend
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://spm-g7-t1-td8d.vercel.app",
            "http://localhost:3000", 
            "http://localhost:3001" 
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Service URLs - Set these in Render environment variables
SERVICE_URLS = {
    'project': os.getenv('PROJECT_SERVICE_URL', 'http://project-service:6001'),
    'task': os.getenv('TASK_SERVICE_URL', 'http://task-service:6002'), 
    'subtask': os.getenv('SUBTASK_SERVICE_URL', 'http://sub-task-service:6003'),
    'notification': os.getenv('NOTIFICATION_SERVICE_URL', 'http://notification-service:6004'),
    'email': os.getenv('EMAIL_SERVICE_URL', 'http://email-service:6005')
}

def proxy_request(service_name, path=''):
    """Proxy requests to the appropriate microservice"""
    if service_name not in SERVICE_URLS:
        return jsonify({'error': 'Service not found'}), 404
    
    target_url = f"{SERVICE_URLS[service_name]}{path}"
    
    print(f"Proxying {request.method} {request.url} -> {target_url}")
    
    try:
        # Forward the request with the same method, headers, and data
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args, timeout=30)
        elif request.method == 'POST':
            response = requests.post(target_url, json=request.get_json(), params=request.args, timeout=30)
        elif request.method == 'PUT':
            response = requests.put(target_url, json=request.get_json(), params=request.args, timeout=30)
        elif request.method == 'PATCH':
            response = requests.patch(target_url, json=request.get_json(), params=request.args, timeout=30)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, params=request.args, timeout=30)
        else:
            return jsonify({'error': 'Method not allowed'}), 405
            
        # Return the response from the microservice
        return response.content, response.status_code, {
            'Content-Type': response.headers.get('Content-Type', 'application/json')
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error proxying request: {e}")
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503

# ==============================================
# PROJECT SERVICE ROUTES
# ==============================================
@app.route('/project', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/project/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def project_proxy(path):
    full_path = f"/project{'/' + path if path else ''}"
    return proxy_request('project', full_path)

# ==============================================
# TASK SERVICE ROUTES
# ==============================================
@app.route('/tasks', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/tasks/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def task_proxy(path):
    full_path = f"/tasks{'/' + path if path else ''}"
    return proxy_request('task', full_path)

# ==============================================
# SUBTASK SERVICE ROUTES
# ==============================================
@app.route('/subtasks', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/subtasks/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def subtask_proxy(path):
    full_path = f"/subtasks{'/' + path if path else ''}"
    return proxy_request('subtask', full_path)

# ==============================================
# NOTIFICATION SERVICE ROUTES
# ==============================================
@app.route('/notifications', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@app.route('/notifications/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def notification_proxy(path):
    full_path = f"/notifications{'/' + path if path else ''}"
    return proxy_request('notification', full_path)

# ==============================================
# EMAIL SERVICE ROUTES
# ==============================================
@app.route('/email', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/email/<path:path>', methods=['GET', 'POST'])
def email_proxy(path):
    full_path = f"/email{'/' + path if path else ''}"
    return proxy_request('email', full_path)

# ==============================================
# SCHEDULER SERVICE ROUTES (part of notification)
# ==============================================
@app.route('/scheduler', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/scheduler/<path:path>', methods=['GET', 'POST'])
def scheduler_proxy(path):
    full_path = f"/scheduler{'/' + path if path else ''}"
    return proxy_request('notification', full_path)

# ==============================================
# HEALTH CHECK
# ==============================================
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'api-gateway',
        'services': SERVICE_URLS
    })

# ==============================================
# ROOT ROUTE
# ==============================================
@app.route('/')
def root():
    return jsonify({
        'message': 'Backend API Gateway',
        'services': ['project', 'tasks', 'subtasks', 'notifications', 'email'],
        'endpoints': {
            'project': '/project/*',
            'tasks': '/tasks/*', 
            'subtasks': '/subtasks/*',
            'notifications': '/notifications/*',
            'email': '/email/*',
            'scheduler': '/scheduler/*',
            'health': '/health'
        },
        'service_urls': SERVICE_URLS
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6000))
    app.run(host='0.0.0.0', port=port, debug=False)