# backend/extension-request-service/extension_request_service.py
import time
import uuid
from typing import List, Optional, Tuple
from models import ExtensionRequest, CreateExtensionRequestRequest, UpdateExtensionRequestRequest
import requests
import os

def get_db_reference(path: str):
    """Get Firebase Realtime Database reference"""
    from firebase_admin import db
    return db.reference(path)

def current_timestamp():
    """Get current epoch timestamp in seconds"""
    return int(time.time())

class ExtensionRequestService:
    """Service for managing deadline extension requests"""
    
    def __init__(self):
        self.requests_ref = get_db_reference("deadlineExtensionRequests")
        self.tasks_ref = get_db_reference("tasks")
        self.subtasks_ref = get_db_reference("subtasks")
        self.users_ref = get_db_reference("users") 
        
        # Service URLs from environment variables
        self.notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL")
        self.task_service_url = os.getenv("TASK_SERVICE_URL")
        self.subtask_service_url = os.getenv("SUBTASK_SERVICE_URL")
    
    def create_extension_request(self, req: CreateExtensionRequestRequest) -> Tuple[Optional[ExtensionRequest], Optional[str]]:
        """Create a new deadline extension request"""
        # Validate item exists and get current deadline
        item_ref = self.tasks_ref if req.item_type == "task" else self.subtasks_ref
        item_data = item_ref.child(req.item_id).get()
        
        if not item_data:
            return None, f"{req.item_type.capitalize()} not found"
        
        owner_id = item_data.get("ownerId")
        current_deadline = item_data.get("deadline")
        item_title = item_data.get("title", "Untitled")
        
        if not owner_id or not current_deadline:
            return None, "Invalid task/subtask data"
        
        # Verify requester is a collaborator but not the owner
        collaborators = item_data.get("collaborators", [])
        if req.requester_id not in collaborators:
            return None, "Requester must be a collaborator"
        
        if req.requester_id == owner_id:
            return None, "Owner cannot request deadline extension"
        
        # Verify proposed deadline is after current deadline
        if req.proposed_deadline <= current_deadline:
            return None, "Proposed deadline must be after current deadline"
        
        # Check for existing pending request
        all_requests = self.requests_ref.get() or {}
        for request_data in all_requests.values():
            if (request_data.get("itemId") == req.item_id and 
                request_data.get("requesterId") == req.requester_id and
                request_data.get("status") == "pending"):
                return None, "You already have a pending request for this item"
        
        # Create new request
        request_id = str(uuid.uuid4())
        current_time = current_timestamp()
        
        request_data = {
            "requestId": request_id,
            "itemId": req.item_id,
            "itemType": req.item_type,
            "requesterId": req.requester_id,
            "ownerId": owner_id,
            "currentDeadline": current_deadline,
            "proposedDeadline": req.proposed_deadline,
            "reason": req.reason,
            "status": "pending",
            "createdAt": current_time
        }
        
        self.requests_ref.child(request_id).set(request_data)
        
        # Send notification to owner
        self._send_extension_request_notification(
            owner_id=owner_id,
            item_id=req.item_id,
            item_title=item_title,
            requester_id=req.requester_id,
            item_type=req.item_type,
            request_id=request_id,
            current_deadline=current_deadline
        )
        
        return ExtensionRequest.from_dict(request_data), None
    
    def get_request_by_id(self, request_id: str) -> Tuple[Optional[ExtensionRequest], Optional[str]]:
        """Get an extension request by ID"""
        request_data = self.requests_ref.child(request_id).get()
        
        if not request_data:
            return None, "Extension request not found"
        
        return ExtensionRequest.from_dict(request_data), None
    
    def get_requests_by_owner(self, owner_id: str, status: Optional[str] = None) -> List[ExtensionRequest]:
        """Get all extension requests for an owner (optionally filtered by status)"""
        all_requests = self.requests_ref.get() or {}
        owner_requests = []
        
        for request_data in all_requests.values():
            if request_data.get("ownerId") == owner_id:
                if status is None or request_data.get("status") == status:
                    owner_requests.append(ExtensionRequest.from_dict(request_data))
        
        # Sort by created date (newest first)
        owner_requests.sort(key=lambda x: x.created_at, reverse=True)
        return owner_requests
    
    def get_requests_by_requester(self, requester_id: str, status: Optional[str] = None) -> List[ExtensionRequest]:
        """Get all extension requests made by a requester (optionally filtered by status)"""
        all_requests = self.requests_ref.get() or {}
        requester_requests = []
        
        for request_data in all_requests.values():
            if request_data.get("requesterId") == requester_id:
                if status is None or request_data.get("status") == status:
                    requester_requests.append(ExtensionRequest.from_dict(request_data))
        
        # Sort by created date (newest first)
        requester_requests.sort(key=lambda x: x.created_at, reverse=True)
        return requester_requests
    
    def get_requests_by_item(self, item_id: str) -> List[ExtensionRequest]:
        """Get all extension requests for a specific task/subtask"""
        all_requests = self.requests_ref.get() or {}
        item_requests = []
        
        for request_data in all_requests.values():
            if request_data.get("itemId") == item_id:
                item_requests.append(ExtensionRequest.from_dict(request_data))
        
        # Sort by created date (newest first)
        item_requests.sort(key=lambda x: x.created_at, reverse=True)
        return item_requests
    
    def respond_to_request(self, req: UpdateExtensionRequestRequest) -> Tuple[Optional[ExtensionRequest], Optional[str]]:
        """Approve or reject an extension request"""
        request_ref = self.requests_ref.child(req.request_id)
        request_data = request_ref.get()
        
        if not request_data:
            return None, "Extension request not found"
        
        if request_data.get("status") != "pending":
            return None, "Request has already been responded to"
        
        # Verify the responder is the owner
        if request_data.get("ownerId") != req.responder_id:
            return None, "Only the owner can respond to this request"
        
        current_time = current_timestamp()
        update_data = {
            "status": req.status,
            "respondedAt": current_time
        }
        
        if req.status == "rejected" and req.rejection_reason:
            update_data["rejectionReason"] = req.rejection_reason
        
        request_ref.update(update_data)
        
        # Get item details
        item_ref = self.tasks_ref if request_data.get("itemType") == "task" else self.subtasks_ref
        item_data = item_ref.child(request_data.get("itemId")).get()
        
        if not item_data:
            return None, "Item not found"
        
        item_title = item_data.get("title", "Untitled")
        
        # If approved, update the task/subtask deadline
        if req.status == "approved":
            service_url = self.task_service_url if request_data.get("itemType") == "task" else self.subtask_service_url
            
            try:
                # Update deadline via service API
                response = requests.put(
                    f"{service_url}/{request_data.get('itemType')}s/{request_data.get('itemId')}",
                    json={"deadline": request_data.get("proposedDeadline")},
                    timeout=10
                )
                
                if response.status_code != 200:
                    return None, f"Failed to update {request_data.get('itemType')} deadline"
                
            except Exception as e:
                print(f"Error updating deadline: {str(e)}")
                return None, f"Error updating deadline: {str(e)}"
            
            # Notify all collaborators about the deadline change
            collaborators = item_data.get("collaborators", [])
            owner_id = item_data.get("ownerId")
            
            # Get all users who should be notified (owner + collaborators, excluding requester)
            all_users = list(set([owner_id] + collaborators))
            all_users = [uid for uid in all_users if uid and uid != request_data.get("requesterId")]
            
            if all_users:
                self._notify_deadline_change(
                    item_id=request_data.get("itemId"),
                    item_title=item_title,
                    item_type=request_data.get("itemType"),
                    user_ids=all_users,
                    new_deadline=request_data.get("proposedDeadline")
                )
        
        # Send notification to requester about the response
        self._send_response_notification(
            requester_id=request_data.get("requesterId"),
            item_id=request_data.get("itemId"),
            item_title=item_title,
            item_type=request_data.get("itemType"),
            status=req.status,
            rejection_reason=req.rejection_reason,
            new_deadline=request_data.get("proposedDeadline") if req.status == "approved" else None
        )
        
        # Get updated request
        updated_request = request_ref.get()
        return ExtensionRequest.from_dict(updated_request), None
    
    def _get_user_name(self, user_id: str) -> str:
        """Get user's display name from Firebase"""
        try:
            user_data = self.users_ref.child(user_id).get()
            if user_data:
                return user_data.get("name") or user_data.get("displayName") or user_data.get("email") or "User"
            return "User"
        except Exception as e:
            print(f"Error fetching user name: {str(e)}")
            return "User"
    
    def _send_extension_request_notification(self, owner_id: str, item_id: str, 
                                            item_title: str, requester_id: str, 
                                            item_type: str, request_id: str, 
                                            current_deadline: int):
        """Send notification to owner about new extension request"""
        
        if not self.notification_service_url:
            print("⚠️  Skipping notification: NOTIFICATION_SERVICE_URL not configured")
            return
        
        try:
            requester_name = self._get_user_name(requester_id)
            
            notification_data = {
                "ownerId": owner_id,              # ✅ Correct field name
                "itemId": item_id,
                "itemTitle": item_title,
                "requesterId": requester_id,
                "itemType": item_type,
                "extensionRequestId": request_id  # ✅ Correct field name
            }
            
            print(f"🔔 Creating notification for owner: {owner_id}")
            print(f"📍 URL: {self.notification_service_url}/notifications/deadline-extension-request")
            print(f"📦 Data: {notification_data}")
            
            # ✅ CORRECT ENDPOINT
            response = requests.post(
                f"{self.notification_service_url}/notifications/deadline-extension-request",
                json=notification_data,
                timeout=10
            )
            
            print(f"✅ Response status: {response.status_code}")
            print(f"📄 Response body: {response.text}")
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to send notification: {response.text}")
                
        except Exception as e:
            print(f"❌ Error sending notification: {str(e)}")
            import traceback
            traceback.print_exc()


    def _send_response_notification(self, requester_id: str, item_id: str, 
                                    item_title: str, item_type: str, 
                                    status: str, rejection_reason: Optional[str],
                                    new_deadline: Optional[int] = None):
        """Send notification to requester about request response"""
            
        if not self.notification_service_url:
            print("⚠️  Skipping notification: NOTIFICATION_SERVICE_URL not configured")
            return
        
        try:
            notification_data = {
                "requesterId": requester_id,
                "itemId": item_id,
                "itemType": item_type,
                "status": status
            }
            
            if rejection_reason:
                notification_data["rejectionReason"] = rejection_reason
            
            print(f"🔔 Creating response notification for requester: {requester_id}")
            
            # ✅ CORRECT ENDPOINT
            response = requests.post(
                f"{self.notification_service_url}/notifications/deadline-extension-response",
                json=notification_data,
                timeout=10
            )
            
            print(f"✅ Response status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to send notification: {response.text}")
                
        except Exception as e:
            print(f"❌ Error sending notification: {str(e)}")
            import traceback
        traceback.print_exc()

    def _notify_deadline_change(self, item_id: str, item_title: str, item_type: str, 
                           user_ids: List[str], new_deadline: int):
        """Notify all specified users about deadline change"""
        
        if not self.notification_service_url:
            print("⚠️  Skipping notification: NOTIFICATION_SERVICE_URL not configured")
            return
        
        try:
            notification_data = {
                "itemId": item_id,
                "itemTitle": item_title,
                "itemType": item_type,
                "collaboratorIds": user_ids,  # ✅ Correct field name
                "newDeadline": new_deadline
            }
            
            print(f"🔔 Creating deadline change notifications for {len(user_ids)} users")
            
            # ✅ CORRECT ENDPOINT
            response = requests.post(
                f"{self.notification_service_url}/notifications/deadline-changed",
                json=notification_data,
                timeout=10
            )
            
            print(f"✅ Response status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to send notifications: {response.text}")
                        
        except Exception as e:
            print(f"❌ Error sending notifications: {str(e)}")
            import traceback
            traceback.print_exc()