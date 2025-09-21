from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import requests
import os
import io, uuid, tempfile
import jwt

app = Flask(__name__)
CORS(app)

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_MIME = {"application/pdf"}

def get_current_user():
    """Extract user UUID from JWT (Kong already validated it)"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get('uuid') or payload.get('sub')
    except:
        return None

def store_document(filename, description, ocr_result):
    """
    Store document in document storage service and return file ID
    """
    try:
        # Get current user for authentication
        auth_header = request.headers.get('Authorization')
        headers = {}
        if auth_header:
            headers['Authorization'] = auth_header
        
        storage_payload = {
            "filename": filename,
            "description": description,
            "content": ocr_result
        }
        
        resp = requests.post(
            "http://document-storage-service:5009/upload_json",
            json=storage_payload,
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        app.logger.error(f"Document storage error: {e}")
        raise

def call_review_service(pages, file_id):
    """
    Sends the OCR pages array and file_id to review-service and returns its JSON.
    """
    try:
        resp = requests.post(
            "http://review-service:5003/review-service",
            json={"pages": pages, "file_id": file_id},

        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        app.logger.error(f"review-service error: {e}")
        raise

@app.route("/upload-service", methods=["POST"])
def upload_and_review():
    # Verify user authentication
    user_uuid = get_current_user()
    if not user_uuid:
        return jsonify(error="Authentication required"), 401

    file = request.files.get("file")
    if not file or file.mimetype not in ALLOWED_MIME:
        return jsonify(error="Please upload a PDF"), 400

    # Get optional metadata from form data
    description = request.form.get("description", "Uploaded document for analysis")
    filename = request.form.get("filename", file.filename or "uploaded_document")
    
    # Remove file extension from filename for storage
    if filename.endswith('.pdf'):
        filename = filename[:-4]

    pdf_bytes = file.read()

    # 1) Call scanner service for OCR
    try:
        scan_resp = requests.post(
            "http://scanner:5004/scan_document",
            files={"file": ("upload.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            
        )
        scan_resp.raise_for_status()
    except requests.RequestException as e:
        return jsonify(error="Scanner service failed", details=str(e)), 502

    ocr_result = scan_resp.json()
    raw_text = ocr_result.get("text", "")
    
    # Parse pages for review service
    pages = [p.strip() for p in raw_text.split("\n--- Page") if p.strip()]
    
    if not pages:
        return jsonify(error="No text content extracted from document"), 400

    # 2) Store document in document storage service
    try:
        storage_result = store_document(filename, description, ocr_result)
        file_id = storage_result.get("id")
        
        if not file_id:
            return jsonify(error="Failed to store document"), 500
            
        app.logger.info(f"Document stored successfully with ID: {file_id}")
        
    except Exception as e:
        return jsonify(error="Document storage failed", details=str(e)), 502

    # 3) Forward pages and file_id to review-service
    try:
        review_result = call_review_service(pages, file_id)
        
        # Enhance response with storage information
        enhanced_result = review_result.copy()
        enhanced_result.update({
            "document_storage": {
                "file_id": file_id,
                "filename": filename,
                "description": description,
                "stored_successfully": True
            }
        })
        
        return jsonify(enhanced_result)
        
    except Exception as e:
        # Even if review fails, document is still stored
        return jsonify({
            "error": "Review service failed", 
            "details": str(e),
            "document_storage": {
                "file_id": file_id,
                "filename": filename,
                "stored_successfully": True,
                "note": "Document was stored successfully despite review failure"
            }
        }), 502

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "upload-service"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)
