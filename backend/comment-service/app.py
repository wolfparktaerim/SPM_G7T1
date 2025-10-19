# backend/comment-service/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import init_firebase, validate_epoch_timestamp
from comment_service import CommentService
from models import CreateCommentRequest, UpdateCommentRequest, ArchiveCommentRequest

app = Flask(__name__)
CORS(app)

# Initialize Firebase
init_firebase()

# Initialize service
comment_service = CommentService()

@app.route("/comments", methods=["POST"])
def create_comment():
    """Create a new comment or comment thread"""
    data = request.get_json()
    
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = CreateCommentRequest.from_dict(data)
    errors = req.validate()
    
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    # Additional validations
    if not validate_epoch_timestamp(req.creation_date):
        return jsonify(error="creationDate must be a valid epoch timestamp"), 400
    
    if not isinstance(req.mention, list) or not all(isinstance(m, str) for m in req.mention):
        return jsonify(error="mention must be an array of strings"), 400
    
    comment_thread, error = comment_service.create_comment(req.to_dict())
    
    if error:
        return jsonify(error=error), 400
    
    return jsonify(
        message="Comment created successfully",
        commentThread=comment_thread
    ), 201

@app.route("/comments", methods=["PUT"])
def update_comment():
    """Add a reply to an existing comment thread"""
    data = request.get_json()
    
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = UpdateCommentRequest.from_dict(data)
    errors = req.validate()
    
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    # Additional validations
    if not validate_epoch_timestamp(req.creation_date):
        return jsonify(error="creationDate must be a valid epoch timestamp"), 400
    
    if req.mention is not None:
        if not isinstance(req.mention, list) or not all(isinstance(m, str) for m in req.mention):
            return jsonify(error="mention must be an array of strings"), 400
    
    comment_thread, error = comment_service.update_comment_thread(req.to_dict())
    
    if error:
        return jsonify(error=error), 400
    
    return jsonify(
        message="Reply added successfully",
        commentThread=comment_thread
    ), 200

@app.route("/comments/archive", methods=["PUT"])
def archive_comment():
    """Archive a comment thread by setting active to False"""
    data = request.get_json()
    
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = ArchiveCommentRequest.from_dict(data)
    errors = req.validate()
    
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    comment_thread, error = comment_service.archive_comment_thread(req.to_dict())
    
    if error:
        return jsonify(error=error), 400
    
    return jsonify(
        message="Comment thread archived successfully",
        commentThread=comment_thread
    ), 200

@app.route("/comments/<parent_id>", methods=["GET"])
def get_comments(parent_id):
    """Get all comment threads for a task or subtask"""
    comment_type = request.args.get('type', 'task')
    
    if comment_type not in ['task', 'subtask']:
        return jsonify(error="type parameter must be either 'task' or 'subtask'"), 400
    
    comment_threads, error = comment_service.get_comment_threads(parent_id, comment_type)
    
    if error:
        return jsonify(error=error), 404
    
    return jsonify(commentThreads=comment_threads), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="comment-service"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6006, debug=True)
