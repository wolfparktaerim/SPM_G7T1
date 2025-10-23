# backend/comment-service/models.py

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CreateCommentRequest:
    """Request model for creating a comment"""
    comment: str
    user_id: str
    creation_date: int
    mention: List[str]
    type: str
    parent_id: str
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            comment=data.get("comment", ""),
            user_id=data.get("userId", ""),
            creation_date=data.get("creationDate", 0),
            mention=data.get("mention", []),
            type=data.get("type", ""),
            parent_id=data.get("parentId", "")
        )
    
    def validate(self):
        """Validate create comment request"""
        errors = []
        if not self.comment or not self.comment.strip():
            errors.append("comment is required and cannot be empty")
        if not self.user_id:
            errors.append("userId is required")
        if not self.creation_date:
            errors.append("creationDate is required")
        if not isinstance(self.mention, list):
            errors.append("mention must be an array")
        if self.type not in ["task", "subtask"]:
            errors.append("type must be either 'task' or 'subtask'")
        if not self.parent_id:
            errors.append("parentId is required")
        return errors
    
    def to_dict(self):
        """Convert to dictionary for service layer"""
        return {
            'comment': self.comment,
            'user_id': self.user_id,
            'creation_date': self.creation_date,
            'mention': self.mention,
            'type': self.type,
            'parent_id': self.parent_id
        }

@dataclass
class UpdateCommentRequest:
    """Request model for adding a reply to a comment thread"""
    type: str
    parent_id: str
    thread_index: int
    comment: str
    user_id: str
    creation_date: int
    mention: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type=data.get("type", ""),
            parent_id=data.get("parentId", ""),
            thread_index=data.get("threadIndex", -1),
            comment=data.get("comment", ""),
            user_id=data.get("userId", ""),
            creation_date=data.get("creationDate", 0),
            mention=data.get("mention")
        )
    
    def validate(self):
        """Validate update comment request"""
        errors = []
        if self.type not in ["task", "subtask"]:
            errors.append("type must be either 'task' or 'subtask'")
        if not self.parent_id:
            errors.append("parentId is required")
        if self.thread_index < 0:
            errors.append("threadIndex is required and must be >= 0")
        if not self.comment or not self.comment.strip():
            errors.append("comment is required and cannot be empty")
        if not self.user_id:
            errors.append("userId is required")
        if not self.creation_date:
            errors.append("creationDate is required")
        return errors
    
    def to_dict(self):
        """Convert to dictionary for service layer"""
        result = {
            'type': self.type,
            'parent_id': self.parent_id,
            'thread_index': self.thread_index,
            'comment': self.comment,
            'user_id': self.user_id,
            'creation_date': self.creation_date
        }
        if self.mention is not None:
            result['mention'] = self.mention
        return result

@dataclass
class ArchiveCommentRequest:
    """Request model for archiving/reopening a comment thread"""
    type: str
    parent_id: str
    thread_index: int
    active: bool = False
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type=data.get("type", ""),
            parent_id=data.get("parentId", ""),
            thread_index=data.get("threadIndex", -1),
            active=data.get("active", False)  
        )
    
    def validate(self):
        """Validate archive comment request"""
        errors = []
        if self.type not in ["task", "subtask"]:
            errors.append("type must be either 'task' or 'subtask'")
        if not self.parent_id:
            errors.append("parentId is required")
        if self.thread_index < 0:
            errors.append("threadIndex is required and must be >= 0")
        if not isinstance(self.active, bool):  
            errors.append("active must be a boolean")
        return errors
    
    def to_dict(self):
        """Convert to dictionary for service layer"""
        return {
            'type': self.type,
            'parent_id': self.parent_id,
            'thread_index': self.thread_index,
            'active': self.active  
        }