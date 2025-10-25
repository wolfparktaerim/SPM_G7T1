# backend/extension-request-service/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExtensionRequest:
    """Extension Request data model"""
    request_id: str
    item_id: str
    item_type: str  # "task" or "subtask"
    requester_id: str
    owner_id: str
    current_deadline: int
    proposed_deadline: int
    reason: str
    status: str  # "pending", "approved", "rejected"
    created_at: int
    rejection_reason: Optional[str] = None
    responded_at: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create ExtensionRequest from dictionary"""
        return cls(
            request_id=data.get("requestId", ""),
            item_id=data.get("itemId", ""),
            item_type=data.get("itemType", ""),
            requester_id=data.get("requesterId", ""),
            owner_id=data.get("ownerId", ""),
            current_deadline=data.get("currentDeadline", 0),
            proposed_deadline=data.get("proposedDeadline", 0),
            reason=data.get("reason", ""),
            status=data.get("status", "pending"),
            created_at=data.get("createdAt", 0),
            rejection_reason=data.get("rejectionReason"),
            responded_at=data.get("respondedAt")
        )
    
    def to_dict(self):
        """Convert ExtensionRequest to dictionary"""
        result = {
            "requestId": self.request_id,
            "itemId": self.item_id,
            "itemType": self.item_type,
            "requesterId": self.requester_id,
            "ownerId": self.owner_id,
            "currentDeadline": self.current_deadline,
            "proposedDeadline": self.proposed_deadline,
            "reason": self.reason,
            "status": self.status,
            "createdAt": self.created_at
        }
        
        if self.rejection_reason:
            result["rejectionReason"] = self.rejection_reason
        if self.responded_at:
            result["respondedAt"] = self.responded_at
            
        return result


@dataclass
class CreateExtensionRequestRequest:
    """Request to create an extension request"""
    item_id: str
    item_type: str  # "task" or "subtask"
    requester_id: str
    proposed_deadline: int
    reason: str
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create CreateExtensionRequestRequest from dictionary"""
        return cls(
            item_id=data.get("itemId", ""),
            item_type=data.get("itemType", ""),
            requester_id=data.get("requesterId", ""),
            proposed_deadline=data.get("proposedDeadline", 0),
            reason=data.get("reason", "")
        )
    
    def validate(self):
        """Validate the request"""
        errors = []
        
        if not self.item_id:
            errors.append("itemId is required")
        
        if self.item_type not in ["task", "subtask"]:
            errors.append("itemType must be 'task' or 'subtask'")
        
        if not self.requester_id:
            errors.append("requesterId is required")
        
        if not self.proposed_deadline:
            errors.append("proposedDeadline is required")
        
        if not self.reason or not self.reason.strip():
            errors.append("reason is required")
        
        return errors


@dataclass
class UpdateExtensionRequestRequest:
    """Request to respond to an extension request"""
    request_id: str
    responder_id: str
    status: str  # "approved" or "rejected"
    rejection_reason: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict, request_id: str):
        """Create UpdateExtensionRequestRequest from dictionary"""
        return cls(
            request_id=request_id,
            responder_id=data.get("responderId", ""),
            status=data.get("status", ""),
            rejection_reason=data.get("rejectionReason")
        )
    
    def validate(self):
        """Validate the request"""
        errors = []
        
        if not self.request_id:
            errors.append("requestId is required")
        
        if not self.responder_id:
            errors.append("responderId is required")
        
        if self.status not in ["approved", "rejected"]:
            errors.append("status must be 'approved' or 'rejected'")
        
        return errors