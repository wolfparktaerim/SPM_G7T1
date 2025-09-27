from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Service URLs - these will be your Railway service URLs
SERVICE_URLS = {
    'project': os.getenv('PROJECT_SERVICE_URL', 'https://project-service-production.up.railway.app'),
    'task': os.getenv('TASK_SERVICE_URL', 'https://task-service-production-4a17.up.railway.app'), 
    'subtask': os.getenv('SUBTASK_SERVICE_URL', 'https://subtask-service-production.up.railway.app')
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

# Project service routes
@app.route('/project', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/project/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def project_proxy(path):
    full_path = f"/project{'/' + path if path else ''}"
    return proxy_request('project', full_path)

# Task service routes  
@app.route('/tasks', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/tasks/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def task_proxy(path):
    full_path = f"/tasks{'/' + path if path else ''}"
    return proxy_request('task', full_path)

# Subtask service routes
@app.route('/subtasks', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/subtasks/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def subtask_proxy(path):
    full_path = f"/subtasks{'/' + path if path else ''}"
    return proxy_request('subtask', full_path)

# Health check
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'gateway',
        'services': SERVICE_URLS
    })

# Root route
@app.route('/')
def root():
    return jsonify({
        'message': 'Backend API Gateway',
        'services': ['project', 'tasks', 'subtasks'],
        'endpoints': {
            'project': '/project/*',
            'tasks': '/tasks/*', 
            'subtasks': '/subtasks/*',
            'health': '/health'
        },
        'service_urls': SERVICE_URLS
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)