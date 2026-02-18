"""Tests for the Mergington High School Activities API endpoints"""
import pytest
from urllib.parse import quote


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        data = response.json()
        
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
        assert len(data) == 9
    
    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_initial_participants(self, client):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to activity"""
        # Sign up new student
        client.post("/activities/Chess%20Club/signup?email=newstudent@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_signup_duplicate_fails(self, client):
        """Test that duplicate signup returns error"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup for non-existent activity fails"""
        response = client.post("/activities/Nonexistent%20Club/signup?email=test@mergington.edu")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        email = "test.student+tag@mergington.edu"
        response = client.post(f"/activities/Drama%20Club/signup?email={quote(email)}")
        
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Drama Club"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_successful(self, client):
        """Test successful removal of participant"""
        email = "michael@mergington.edu"
        response = client.delete(f"/activities/Chess%20Club/participants/{quote(email)}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_remove_participant_actually_removes(self, client):
        """Test that participant is actually removed from activity"""
        email = "michael@mergington.edu"
        
        # Remove participant
        client.delete(f"/activities/Chess%20Club/participants/{quote(email)}")
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_remove_nonexistent_participant_fails(self, client):
        """Test that removing non-existent participant fails"""
        email = "nonexistent@mergington.edu"
        response = client.delete(f"/activities/Chess%20Club/participants/{quote(email)}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_remove_participant_from_nonexistent_activity_fails(self, client):
        """Test that removing participant from non-existent activity fails"""
        email = "test@mergington.edu"
        response = client.delete(f"/activities/Nonexistent%20Club/participants/{quote(email)}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_remove_participant_with_special_characters(self, client):
        """Test removing participant with special characters in email"""
        # First add a participant with special characters
        email = "test.student+tag@mergington.edu"
        client.post(f"/activities/Art%20Studio/signup?email={quote(email)}")
        
        # Now remove them
        response = client.delete(f"/activities/Art%20Studio/participants/{quote(email)}")
        
        assert response.status_code == 200
        
        # Verify removal
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Art Studio"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    def test_signup_and_remove_workflow(self, client):
        """Test complete workflow of signing up and removing a participant"""
        email = "workflow@mergington.edu"
        activity = "Soccer Club"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(f"/activities/{quote(activity)}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify added
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        assert email in response.json()[activity]["participants"]
        
        # Remove
        response = client.delete(f"/activities/{quote(activity)}/participants/{quote(email)}")
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count
        assert email not in response.json()[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test signing up the same student for multiple activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for multiple activities
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        client.post(f"/activities/Science%20Olympiad/signup?email={email}")
        
        # Verify signup in all activities
        response = client.get("/activities")
        data = response.json()
        
        assert email in data["Chess Club"]["participants"]
        assert email in data["Drama Club"]["participants"]
        assert email in data["Science Olympiad"]["participants"]
    
    def test_capacity_tracking(self, client):
        """Test that participant count affects capacity correctly"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club has max 12, starts with 2
        initial_participants = len(data["Chess Club"]["participants"])
        max_participants = data["Chess Club"]["max_participants"]
        
        # Add a participant
        client.post("/activities/Chess%20Club/signup?email=capacity@mergington.edu")
        
        # Verify count increased
        response = client.get("/activities")
        data = response.json()
        new_count = len(data["Chess Club"]["participants"])
        
        assert new_count == initial_participants + 1
        assert new_count <= max_participants
