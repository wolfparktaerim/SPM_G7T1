# backend/project-service/models.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Project:
    """Project data model"""
    project_id: str
    title: str
    owner_id: str
    collaborators: List[str]
    description: str
    deadline: int
    creation_date: int
    department: str
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Project from dictionary"""
        return cls(
            project_id=data.get("projectId", ""),
            title=data.get("title", ""),
            owner_id=data.get("ownerId", ""),
            collaborators=data.get("collaborators", []),
            description=data.get("description", ""),
            deadline=data.get("deadline", 0),
            creation_date=data.get("creationDate", 0),
            department=data.get("department", "Unknown")
        )
    
    def to_dict(self):
        """Convert Project to dictionary"""
        return {
            "projectId": self.project_id,
            "title": self.title,
            "ownerId": self.owner_id,
            "collaborators": self.collaborators,
            "description": self.description,
            "deadline": self.deadline,
            "creationDate": self.creation_date,
            "department": self.department
        }

@dataclass
class CreateProjectRequest:
    """Request model for creating a project"""
    userid: str
    role: str
    title: str
    description: str
    deadline: int
    collaborators: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            userid=data.get("userid", ""),
            role=data.get("role", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            deadline=data.get("deadline", 0),
            collaborators=data.get("collaborators", [])
        )
    
    def validate(self):
        """Validate create project request"""
        errors = []
        if not self.userid:
            errors.append("userid is required")
        if not self.role:
            errors.append("role is required")
        if not self.title:
            errors.append("title is required")
        return errors

@dataclass
class UpdateProjectRequest:
    """Request model for updating a project"""
    userid: str
    project_id: str
    title: Optional[str] = None
    deadline: Optional[int] = None
    description: Optional[str] = None
    collaborators: Optional[List[str]] = None
    owner_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            userid=data.get("userid", ""),
            project_id=data.get("projectId", ""),
            title=data.get("title"),
            deadline=data.get("deadline"),
            description=data.get("description"),
            collaborators=data.get("collaborators"),
            owner_id=data.get("ownerId")
        )
    
    def validate(self):
        """Validate update project request"""
        errors = []
        if not self.userid:
            errors.append("userid is required")
        if not self.project_id:
            errors.append("projectId is required")
        return errors