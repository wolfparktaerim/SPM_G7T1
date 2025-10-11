# backend/project-service/project_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, current_timestamp
from models import Project, CreateProjectRequest, UpdateProjectRequest

class ProjectService:
    """Service for managing projects"""
    
    def __init__(self):
        self.projects_ref = get_db_reference("project")
        self.users_ref = get_db_reference("users")
    
    def get_user_info(self, user_id):
        """Get user information"""
        return self.users_ref.child(user_id).get()
    
    def get_all_users(self):
        """Get all users"""
        all_users = self.users_ref.get() or {}
        return [
            {"uid": uid, "name": info.get("name"), "email": info.get("email")}
            for uid, info in all_users.items()
        ]
    
    def create_project(self, req: CreateProjectRequest):
        """Create a new project"""
        # Get creator info
        user_info = self.get_user_info(req.userid)
        if not user_info:
            return None, "User not found"
        
        department = user_info.get("department", "Unknown")
        
        # Create project
        new_proj_ref = self.projects_ref.push()
        project_id = new_proj_ref.key
        
        # Ensure creator is in collaborators
        collaborators = list(set(req.collaborators + [req.userid]))
        
        project = Project(
            project_id=project_id,
            title=req.title,
            owner_id=req.userid,
            collaborators=collaborators,
            description=req.description,
            deadline=req.deadline,
            creation_date=current_timestamp(),
            department=department
        )
        
        new_proj_ref.set(project.to_dict())
        return project, None
    
    def get_all_projects(self):
        """Get all projects"""
        all_projects = self.projects_ref.get() or {}
        return [Project.from_dict(p) for p in all_projects.values()]
    
    def get_projects_by_department(self, department):
        """Get projects by department"""
        all_projects = self.projects_ref.get() or {}
        dept_lower = (department or "unknown").lower()
        
        filtered = [
            Project.from_dict(p) for p in all_projects.values()
            if (p.get("department") or "unknown").lower() == dept_lower
        ]
        return filtered
    
    def get_user_projects(self, user_id):
        """Get projects for a user (owner or collaborator)"""
        all_projects = self.projects_ref.get() or {}
        
        filtered = [
            Project.from_dict(p) for p in all_projects.values()
            if user_id == p.get("ownerId") or user_id in p.get("collaborators", [])
        ]
        return filtered
    
    def get_available_users_for_collaboration(self, project_id):
        """Get users available for collaboration (not already collaborating)"""
        project_ref = self.projects_ref.child(project_id)
        project_data = project_ref.get()
        
        if not project_data:
            return None, "Project not found"
        
        all_users = self.users_ref.get() or {}
        owner_id = project_data.get("ownerId")
        current_collaborators = set(project_data.get("collaborators", []))
        
        available = [
            {"uid": uid, "name": info.get("name"), "email": info.get("email")}
            for uid, info in all_users.items()
            if uid != owner_id and uid not in current_collaborators
        ]
        
        return available, None
    
    def update_project(self, req: UpdateProjectRequest):
        """Update a project"""
        project_ref = self.projects_ref.child(req.project_id)
        project_data = project_ref.get()
        
        if not project_data:
            return None, "Project not found"
        
        if project_data.get('ownerId') != req.userid:
            return None, "Only project owner can update the project"
        
        # Build update data
        update_data = {}
        
        if req.title is not None:
            update_data['title'] = req.title
        
        if req.deadline is not None:
            update_data['deadline'] = req.deadline
        
        if req.description is not None:
            update_data['description'] = req.description
        
        if req.collaborators is not None:
            current_collabs = set(project_data.get('collaborators', []))
            new_collabs = [c for c in req.collaborators if c not in current_collabs]
            update_data['collaborators'] = list(current_collabs) + new_collabs
        
        if req.owner_id and req.owner_id != project_data.get('ownerId'):
            # Validate role hierarchy
            users = self.users_ref.get() or {}
            current_role = users.get(req.userid, {}).get("role")
            new_role = users.get(req.owner_id, {}).get("role")
            
            roles_order = {'director': 3, 'manager': 2, 'staff': 1}
            if roles_order.get(current_role, 0) < roles_order.get(new_role, 0):
                return None, "Cannot assign project ownership to a higher role"
            
            update_data['ownerId'] = req.owner_id
            if 'collaborators' in update_data and req.owner_id not in update_data['collaborators']:
                update_data['collaborators'].append(req.owner_id)
        
        if update_data:
            project_ref.update(update_data)
        
        return Project.from_dict(project_ref.get()), None
    
    def add_collaborators(self, user_id, project_id, new_collaborators):
        """Add collaborators to project"""
        project_ref = self.projects_ref.child(project_id)
        project_data = project_ref.get()
        
        if not project_data:
            return None, "Project not found"
        
        if project_data.get("ownerId") != user_id:
            return None, "Unauthorized: only owner can add collaborators"
        
        collaborators = set(project_data.get("collaborators", []))
        for collab in new_collaborators:
            collaborators.add(collab)
        
        project_ref.update({"collaborators": list(collaborators)})
        return Project.from_dict(project_ref.get()), None
    
    def change_owner(self, current_owner_id, project_id, new_owner_id):
        """Change project owner"""
        project_ref = self.projects_ref.child(project_id)
        project_data = project_ref.get()
        
        if not project_data:
            return None, "Project not found"
        
        if project_data.get("ownerId") != current_owner_id:
            return None, "Unauthorized: only current owner can change owner"
        
        users = self.users_ref.get() or {}
        current_role = users.get(current_owner_id, {}).get("role")
        new_role = users.get(new_owner_id, {}).get("role")
        
        if not current_role or not new_role:
            return None, "User roles not found in /users database"
        
        # Role delegation rules
        if current_role == "director":
            if new_role != "manager":
                return None, "Director can only delegate ownership to a manager"
        elif current_role == "manager":
            if new_role in ("manager", "director"):
                return None, "Manager cannot delegate ownership to manager or director"
        else:
            return None, "Only director or manager can delegate ownership"
        
        # Add new owner to collaborators
        collaborators = set(project_data.get("collaborators", []))
        collaborators.add(new_owner_id)
        
        project_ref.update({
            "ownerId": new_owner_id,
            "collaborators": list(collaborators)
        })
        
        return Project.from_dict(project_ref.get()), None