# backend/project-service/test_project.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Set environment variables before imports
os.environ['JSON_PATH'] = '/tmp/dummy.json'
os.environ['DATABASE_URL'] = 'https://dummy.firebaseio.com'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Firebase BEFORE importing app
with patch('firebase_admin.initialize_app'):
    with patch('firebase_admin.credentials.Certificate'):
        with patch('firebase_admin.db.reference') as mock_db_ref:
            mock_db_ref.return_value = Mock()
            
            from project_service import ProjectService
            from models import Project, CreateProjectRequest, UpdateProjectRequest
            from app import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    """Mock database references"""
    with patch('project_service.get_db_reference') as mock:
        yield mock

@pytest.fixture
def sample_project():
    """Create sample project"""
    return Project(
        project_id="p1",
        title="Test Project",
        owner_id="u1",
        collaborators=["u1", "u2"],
        description="Test Description",
        deadline=1700000000,
        creation_date=1600000000,
        department="Engineering",
        archived=False
    )

class TestProjectModels:
    """Test project models"""
    
    def test_project_from_dict(self):
        """Test creating Project from dictionary"""
        data = {
            "projectId": "p1",
            "title": "Test Project",
            "ownerId": "u1",
            "collaborators": ["u1", "u2"],
            "description": "Test",
            "deadline": 1700000000,
            "creationDate": 1600000000,
            "department": "Engineering",
            "archived": False
        }
        project = Project.from_dict(data)
        
        assert project.project_id == "p1"
        assert project.title == "Test Project"
        assert len(project.collaborators) == 2
        assert project.department == "Engineering"
        assert project.archived == False
    
    def test_project_to_dict(self, sample_project):
        """Test converting Project to dictionary"""
        data = sample_project.to_dict()
        
        assert data["projectId"] == "p1"
        assert data["title"] == "Test Project"
        assert data["ownerId"] == "u1"
        assert len(data["collaborators"]) == 2
        assert data["archived"] == False
    
    def test_create_project_request_validate_success(self):
        """Test validation with valid data"""
        req = CreateProjectRequest(
            userid="u1",
            role="manager",
            title="Test",
            description="Desc",
            deadline=1700000000
        )
        errors = req.validate()
        assert len(errors) == 0
    
    def test_create_project_request_validate_missing_fields(self):
        """Test validation with missing fields"""
        req = CreateProjectRequest(
            userid="",
            role="",
            title="",
            description="",
            deadline=0
        )
        errors = req.validate()
        assert len(errors) > 0
        assert "userid is required" in errors
        assert "role is required" in errors
        assert "title is required" in errors
    
    def test_update_project_request_validate(self):
        """Test update request validation"""
        req = UpdateProjectRequest(
            userid="u1",
            project_id="p1",
            title="Updated"
        )
        errors = req.validate()
        assert len(errors) == 0

class TestProjectService:
    """Test project service class"""
    
    def test_get_user_info(self, mock_db):
        """Test getting user info"""
        mock_projects = Mock()
        mock_users = Mock()
        mock_db.side_effect = lambda x: mock_projects if x == "project" else mock_users
        
        mock_users.child.return_value.get.return_value = {
            "name": "Test User",
            "department": "Engineering",
            "role": "manager"
        }
        
        service = ProjectService()
        user_info = service.get_user_info("u1")
        
        assert user_info["name"] == "Test User"
        assert user_info["department"] == "Engineering"
    
    def test_get_all_users(self, mock_db):
        """Test getting all users"""
        mock_projects = Mock()
        mock_users = Mock()
        mock_db.side_effect = lambda x: mock_projects if x == "project" else mock_users
        
        mock_users.get.return_value = {
            "u1": {"name": "User 1", "email": "user1@test.com"},
            "u2": {"name": "User 2", "email": "user2@test.com"}
        }
        
        service = ProjectService()
        users = service.get_all_users()
        
        assert len(users) == 2
        assert users[0]["uid"] == "u1"
    
    def test_create_project(self, mock_db):
        """Test creating a project"""
        mock_projects = Mock()
        mock_users = Mock()
        mock_db.side_effect = lambda x: mock_projects if x == "project" else mock_users
        
        mock_users.child.return_value.get.return_value = {
            "name": "Test User",
            "department": "Engineering"
        }
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-project-id"
        mock_projects.push.return_value = mock_new_ref
        
        service = ProjectService()
        req = CreateProjectRequest(
            userid="user1",
            role="manager",
            title="Test Project",
            description="Test Description",
            deadline=1700000000,
            collaborators=["user2"]
        )
        
        project, error = service.create_project(req)
        
        assert error is None
        assert project.title == "Test Project"
        assert project.department == "Engineering"
        assert "user1" in project.collaborators
        assert "user2" in project.collaborators
        assert project.archived == False
        mock_new_ref.set.assert_called_once()
    
    def test_create_project_user_not_found(self, mock_db):
        """Test creating project with non-existent user"""
        mock_projects = Mock()
        mock_users = Mock()
        mock_db.side_effect = lambda x: mock_projects if x == "project" else mock_users
        
        mock_users.child.return_value.get.return_value = None
        
        service = ProjectService()
        req = CreateProjectRequest(
            userid="invalid",
            role="manager",
            title="Test",
            description="Test",
            deadline=1700000000
        )
        
        project, error = service.create_project(req)
        
        assert project is None
        assert "not found" in error.lower()
    
    def test_get_all_projects(self, mock_db):
        """Test getting all projects"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_projects.get.return_value = {
            "p1": {
                "projectId": "p1",
                "title": "Project 1",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "description": "Desc",
                "deadline": 1700000000,
                "creationDate": 1600000000,
                "department": "Eng",
                "archived": False
            },
            "p2": {
                "projectId": "p2",
                "title": "Project 2",
                "ownerId": "u2",
                "collaborators": ["u2"],
                "description": "Desc2",
                "deadline": 1700000000,
                "creationDate": 1600000000,
                "department": "HR",
                "archived": False
            }
        }
        
        service = ProjectService()
        projects = service.get_all_projects()
        
        assert len(projects) == 2
        assert projects[0].title == "Project 1"
    
    def test_get_projects_by_department(self, mock_db):
        """Test getting projects by department"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_projects.get.return_value = {
            "p1": {
                "projectId": "p1",
                "title": "Eng Project",
                "ownerId": "u1",
                "collaborators": [],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "Engineering",
                "archived": False
            },
            "p2": {
                "projectId": "p2",
                "title": "HR Project",
                "ownerId": "u2",
                "collaborators": [],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "HR",
                "archived": False
            }
        }
        
        service = ProjectService()
        projects = service.get_projects_by_department("Engineering")
        
        assert len(projects) == 1
        assert projects[0].department == "Engineering"
    
    def test_get_user_projects(self, mock_db):
        """Test getting projects for a specific user"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_projects.get.return_value = {
            "p1": {
                "projectId": "p1",
                "title": "My Project",
                "ownerId": "u1",
                "collaborators": ["u1", "u2"],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "",
                "archived": False
            },
            "p2": {
                "projectId": "p2",
                "title": "Other Project",
                "ownerId": "u3",
                "collaborators": ["u3"],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "",
                "archived": False
            }
        }
        
        service = ProjectService()
        projects = service.get_user_projects("u1")
        
        assert len(projects) == 1
        assert projects[0].project_id == "p1"
    
    def test_update_project(self, mock_db):
        """Test updating a project"""
        mock_projects = Mock()
        mock_users = Mock()
        mock_db.side_effect = lambda x: mock_projects if x == "project" else mock_users
        
        mock_project_ref = Mock()
        mock_project_ref.get.return_value = {
            "projectId": "p1",
            "ownerId": "u1",
            "collaborators": ["u1"],
            "title": "Old Title",
            "description": "Old Desc",
            "deadline": 1600000000,
            "creationDate": 1500000000,
            "department": "Eng",
            "archived": False
        }
        mock_projects.child.return_value = mock_project_ref
        
        service = ProjectService()
        req = UpdateProjectRequest(
            userid="u1",
            project_id="p1",
            title="New Title",
            deadline=1700000000
        )
        
        project, error = service.update_project(req)
        
        assert error is None
        mock_project_ref.update.assert_called_once()
    
    def test_update_project_not_owner(self, mock_db):
        """Test updating project by non-owner"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_project_ref = Mock()
        mock_project_ref.get.return_value = {
            "projectId": "p1",
            "ownerId": "u1",
            "collaborators": ["u1", "u2"]
        }
        mock_projects.child.return_value = mock_project_ref
        
        service = ProjectService()
        req = UpdateProjectRequest(
            userid="u2",  # Not the owner
            project_id="p1",
            title="New Title"
        )
        
        project, error = service.update_project(req)
        
        assert project is None
        assert "owner" in error.lower()
    
    def test_add_collaborators(self, mock_db):
        """Test adding collaborators"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_project_ref = Mock()
        mock_project_ref.get.return_value = {
            "projectId": "p1",
            "ownerId": "u1",
            "collaborators": ["u1"]
        }
        mock_projects.child.return_value = mock_project_ref
        
        service = ProjectService()
        project, error = service.add_collaborators("u1", "p1", ["u2", "u3"])
        
        assert error is None
        mock_project_ref.update.assert_called_once()
    
    def test_change_owner(self, mock_db):
        """Test changing project owner"""
        mock_projects = Mock()
        mock_users = Mock()
        mock_db.side_effect = lambda x: mock_projects if x == "project" else mock_users
        
        mock_project_ref = Mock()
        mock_project_ref.get.return_value = {
            "projectId": "p1",
            "ownerId": "u1",
            "collaborators": ["u1"]
        }
        mock_projects.child.return_value = mock_project_ref
        
        mock_users.get.return_value = {
            "u1": {"role": "director"},
            "u2": {"role": "manager"}
        }
        
        service = ProjectService()
        project, error = service.change_owner("u1", "p1", "u2")
        
        assert error is None
        mock_project_ref.update.assert_called_once()
    
    def test_change_owner_invalid_hierarchy(self, mock_db):
        """Test changing owner with invalid role hierarchy"""
        mock_projects = Mock()
        mock_users = Mock()
        mock_db.side_effect = lambda x: mock_projects if x == "project" else mock_users
        
        mock_project_ref = Mock()
        mock_project_ref.get.return_value = {
            "projectId": "p1",
            "ownerId": "u1",
            "collaborators": ["u1"]
        }
        mock_projects.child.return_value = mock_project_ref
        
        mock_users.get.return_value = {
            "u1": {"role": "director"},
            "u2": {"role": "director"}  # Can't delegate to another director
        }
        
        service = ProjectService()
        project, error = service.change_owner("u1", "p1", "u2")
        
        assert project is None
        assert "manager" in error.lower()

    def test_archive_project(self, mock_db):
        """Test archiving a project"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_project_ref = Mock()
        mock_project_ref.get.side_effect = [
            {  # First call - before archive
                "projectId": "p1",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "title": "Test Project",
                "archived": False
            },
            {  # Second call - after archive
                "projectId": "p1",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "title": "Test Project",
                "archived": True
            }
        ]
        mock_projects.child.return_value = mock_project_ref
        
        service = ProjectService()
        project, error = service.archive_project("u1", "p1")
        
        assert error is None
        assert project.archived == True
        mock_project_ref.update.assert_called_once_with({"archived": True})

    def test_archive_project_not_owner(self, mock_db):
        """Test archiving project by non-owner"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_project_ref = Mock()
        mock_project_ref.get.return_value = {
            "projectId": "p1",
            "ownerId": "u1",
            "collaborators": ["u1", "u2"],
            "archived": False
        }
        mock_projects.child.return_value = mock_project_ref
        
        service = ProjectService()
        project, error = service.archive_project("u2", "p1")  # u2 is not owner
        
        assert project is None
        assert "owner" in error.lower()
        mock_project_ref.update.assert_not_called()

    def test_unarchive_project(self, mock_db):
        """Test unarchiving a project"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_project_ref = Mock()
        mock_project_ref.get.side_effect = [
            {  # First call - before unarchive
                "projectId": "p1",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "title": "Test Project",
                "archived": True
            },
            {  # Second call - after unarchive
                "projectId": "p1",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "title": "Test Project",
                "archived": False
            }
        ]
        mock_projects.child.return_value = mock_project_ref
        
        service = ProjectService()
        project, error = service.unarchive_project("u1", "p1")
        
        assert error is None
        assert project.archived == False
        mock_project_ref.update.assert_called_once_with({"archived": False})

    def test_get_user_projects_excludes_archived(self, mock_db):
        """Test that get_user_projects excludes archived projects"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_projects.get.return_value = {
            "p1": {
                "projectId": "p1",
                "title": "Active Project",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "",
                "archived": False
            },
            "p2": {
                "projectId": "p2",
                "title": "Archived Project",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "",
                "archived": True
            }
        }
        
        service = ProjectService()
        projects = service.get_user_projects("u1")
        
        # Should only return the active project
        assert len(projects) == 1
        assert projects[0].project_id == "p1"
        assert projects[0].archived == False

    def test_get_archived_projects(self, mock_db):
        """Test getting archived projects"""
        mock_projects = Mock()
        mock_db.return_value = mock_projects
        
        mock_projects.get.return_value = {
            "p1": {
                "projectId": "p1",
                "title": "Active Project",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "",
                "archived": False
            },
            "p2": {
                "projectId": "p2",
                "title": "Archived Project",
                "ownerId": "u1",
                "collaborators": ["u1"],
                "description": "",
                "deadline": 0,
                "creationDate": 0,
                "department": "",
                "archived": True
            }
        }
        
        service = ProjectService()
        projects = service.get_archived_projects("u1")
        
        # Should only return archived projects owned by user
        assert len(projects) == 1
        assert projects[0].project_id == "p2"
        assert projects[0].archived == True


class TestProjectEndpoints:
    """Test Flask endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'project-service'
    
    def test_create_project_missing_body(self, client):
        """Test creating project without body"""
        response = client.post('/project/create')
        assert response.status_code in [400, 415]
    
    def test_create_project_invalid_data(self, client):
        """Test creating project with invalid data"""
        response = client.post('/project/create', json={})
        assert response.status_code in [400, 415]
    
    @patch('app.project_service.create_project')
    def test_create_project_success(self, mock_create, client, sample_project):
        """Test successful project creation"""
        mock_create.return_value = (sample_project, None)
        
        response = client.post('/project/create', json={
            "userid": "u1",
            "role": "manager",
            "title": "Test Project",
            "description": "Test",
            "deadline": 1700000000
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'project' in data
    
    @patch('app.project_service.get_all_projects')
    def test_get_all_projects(self, mock_get, client, sample_project):
        """Test getting all projects"""
        mock_get.return_value = [sample_project]
        
        response = client.get('/project/all')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['projects']) == 1
    
    @patch('app.project_service.get_user_projects')
    def test_get_user_projects(self, mock_get, client):
        """Test getting user projects"""
        mock_get.return_value = []
        
        response = client.get('/project/user123')
        assert response.status_code == 200
        data = response.get_json()
        assert 'projects' in data
    
    @patch('app.project_service.update_project')
    def test_update_project(self, mock_update, client, sample_project):
        """Test updating project"""
        mock_update.return_value = (sample_project, None)
        
        response = client.post('/project/update', json={
            "userid": "u1",
            "projectId": "p1",
            "title": "Updated Title"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'updatedProject' in data
    
    @patch('app.project_service.get_all_users')
    def test_get_all_users(self, mock_get, client):
        """Test getting all users"""
        mock_get.return_value = [
            {"uid": "u1", "name": "User 1", "email": "user1@test.com"}
        ]
        
        response = client.get('/project/all-users')
        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
    
    @patch('app.project_service.archive_project')
    def test_archive_project_endpoint(self, mock_archive, client, sample_project):
        """Test archive endpoint"""
        sample_project.archived = True
        mock_archive.return_value = (sample_project, None)
        
        response = client.post('/project/archive', json={
            "userid": "u1",
            "projectId": "p1"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['project']['archived'] == True

    @patch('app.project_service.unarchive_project')
    def test_unarchive_project_endpoint(self, mock_unarchive, client, sample_project):
        """Test unarchive endpoint"""
        mock_unarchive.return_value = (sample_project, None)
        
        response = client.post('/project/unarchive', json={
            "userid": "u1",
            "projectId": "p1"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['project']['archived'] == False

    @patch('app.project_service.get_archived_projects')
    def test_get_archived_projects_endpoint(self, mock_get_archived, client):
        """Test get archived projects endpoint"""
        mock_get_archived.return_value = []
        
        response = client.get('/project/archived/u1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'projects' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])