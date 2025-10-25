# backend/extension-request-service/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import init_firebase, validate_epoch_timestamp

from extension_request_service import ExtensionRequestService
from models import CreateExtensionRequestRequest, UpdateExtensionRequestRequest

app = Flask(__name__)
CORS(app)

# Initialize Firebase
init_firebase()

# Initialize service
extension_request_service = ExtensionRequestService()

@app.route("/extension-requests", methods=["POST"])
def create_extension_request():
    """Create a new deadline extension request"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = CreateExtensionRequestRequest.from_dict(data)
    errors = req.validate()
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    # Validate proposed deadline timestamp
    if not validate_epoch_timestamp(req.proposed_deadline):
        return jsonify(error="proposedDeadline must be a valid epoch timestamp"), 400
    
    extension_request, error = extension_request_service.create_extension_request(req)
    if error:
        return jsonify(error=error), 400
    
    return jsonify(
        message="Extension request created successfully",
        request=extension_request.to_dict()
    ), 201

@app.route("/extension-requests/<request_id>", methods=["GET"])
def get_extension_request(request_id):
    """Get an extension request by ID"""
    extension_request, error = extension_request_service.get_request_by_id(request_id)
    if error:
        return jsonify(error=error), 404
    
    # ✅ Enhanced response with full extension request data
    return jsonify(extension_request.to_dict()), 200

@app.route("/extension-requests/owner/<owner_id>", methods=["GET"])
def get_requests_by_owner(owner_id):
    """Get all extension requests for an owner"""
    status = request.args.get('status')  # Optional filter
    requests_list = extension_request_service.get_requests_by_owner(owner_id, status)
    
    return jsonify(requests=[r.to_dict() for r in requests_list]), 200

@app.route("/extension-requests/requester/<requester_id>", methods=["GET"])
def get_requests_by_requester(requester_id):
    """Get all extension requests made by a requester"""
    status = request.args.get('status')  # Optional filter
    requests_list = extension_request_service.get_requests_by_requester(requester_id, status)
    
    return jsonify(requests=[r.to_dict() for r in requests_list]), 200

@app.route("/extension-requests/item/<item_id>", methods=["GET"])
def get_requests_by_item(item_id):
    """Get all extension requests for a specific task/subtask"""
    requests_list = extension_request_service.get_requests_by_item(item_id)
    
    return jsonify(requests=[r.to_dict() for r in requests_list]), 200

@app.route("/extension-requests/<request_id>/respond", methods=["PATCH"])
def respond_to_request(request_id):
    """Respond to an extension request (approve or reject)"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = UpdateExtensionRequestRequest.from_dict(data, request_id)
    errors = req.validate()
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    extension_request, error = extension_request_service.respond_to_request(req)
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify(error=error), status_code
    
    return jsonify(
        message=f"Extension request {req.status}",
        request=extension_request.to_dict()
    ), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="extension-request-service"), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 6007))
    app.run(host='0.0.0.0', port=port, debug=True)