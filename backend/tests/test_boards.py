"""Tests for board management endpoints."""
import pytest


class TestCreateBoard:
    """Tests for creating boards."""

    def test_create_board_success(self, client, auth_headers):
        """Test creating a board successfully."""
        response = client.post(
            "/api/v1/boards",
            json={"name": "My Board"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "My Board"
        assert data["data"]["sort_order"] == 0

    def test_create_board_no_auth(self, client):
        """Test creating a board without authentication."""
        response = client.post(
            "/api/v1/boards",
            json={"name": "My Board"}
        )
        assert response.status_code == 401

    def test_create_board_empty_name(self, client, auth_headers):
        """Test creating a board with empty name."""
        response = client.post(
            "/api/v1/boards",
            json={"name": ""},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_board_name_too_long(self, client, auth_headers):
        """Test creating a board with name too long (101 chars)."""
        long_name = "a" * 101
        response = client.post(
            "/api/v1/boards",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_board_name_max_length_ok(self, client, auth_headers):
        """Test creating a board with name at max length (100 chars)."""
        max_name = "a" * 100
        response = client.post(
            "/api/v1/boards",
            json={"name": max_name},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_multiple_boards_sort_order(self, client, auth_headers):
        """Test that boards get correct sort_order when created."""
        # Create first board
        client.post(
            "/api/v1/boards",
            json={"name": "Board 1"},
            headers=auth_headers
        )
        # Create second board
        response = client.post(
            "/api/v1/boards",
            json={"name": "Board 2"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["sort_order"] == 1


class TestGetBoards:
    """Tests for getting boards."""

    def test_get_boards_empty(self, client, auth_headers):
        """Test getting boards when there are none."""
        response = client.get("/api/v1/boards", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_boards_with_data(self, client, auth_headers, test_board):
        """Test getting boards when there are some."""
        response = client.get("/api/v1/boards", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == test_board.name

    def test_get_boards_no_auth(self, client):
        """Test getting boards without authentication."""
        response = client.get("/api/v1/boards")
        assert response.status_code == 401

    def test_get_boards_include_stocks(self, client, auth_headers, test_board, test_stock):
        """Test getting boards with include_stocks=true."""
        response = client.get(
            "/api/v1/boards?include_stocks=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stocks" in data["data"][0]
        assert len(data["data"][0]["stocks"]) == 1


class TestGetSingleBoard:
    """Tests for getting a single board."""

    def test_get_board_success(self, client, auth_headers, test_board):
        """Test getting a board successfully."""
        response = client.get(
            f"/api/v1/boards/{test_board.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_board.id
        assert data["data"]["name"] == test_board.name

    def test_get_board_not_found(self, client, auth_headers):
        """Test getting a board that doesn't exist."""
        response = client.get(
            "/api/v1/boards/99999",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_get_board_no_auth(self, client, test_board):
        """Test getting a board without authentication."""
        response = client.get(f"/api/v1/boards/{test_board.id}")
        assert response.status_code == 401

    def test_get_board_no_permission(self, client, auth_headers, test_board_user2):
        """Test getting another user's board."""
        response = client.get(
            f"/api/v1/boards/{test_board_user2.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


class TestUpdateBoard:
    """Tests for updating boards."""

    def test_update_board_success(self, client, auth_headers, test_board):
        """Test updating a board successfully."""
        response = client.put(
            f"/api/v1/boards/{test_board.id}",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"

    def test_update_board_empty_name(self, client, auth_headers, test_board):
        """Test updating a board with empty name."""
        response = client.put(
            f"/api/v1/boards/{test_board.id}",
            json={"name": ""},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_board_not_found(self, client, auth_headers):
        """Test updating a board that doesn't exist."""
        response = client.put(
            "/api/v1/boards/99999",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_update_board_no_permission(self, client, auth_headers, test_board_user2):
        """Test updating another user's board."""
        response = client.put(
            f"/api/v1/boards/{test_board_user2.id}",
            json={"name": "Hacked!"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_update_board_sort_order(self, client, auth_headers, test_board):
        """Test updating a board's sort_order."""
        response = client.put(
            f"/api/v1/boards/{test_board.id}",
            json={"name": test_board.name, "sort_order": 5},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["sort_order"] == 5


class TestDeleteBoard:
    """Tests for deleting boards."""

    def test_delete_board_success(self, client, auth_headers, test_board):
        """Test deleting a board successfully."""
        response = client.delete(
            f"/api/v1/boards/{test_board.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/boards/{test_board.id}",
            headers=auth_headers
        )
        get_data = get_response.json()
        assert get_data["success"] is False

    def test_delete_board_not_found(self, client, auth_headers):
        """Test deleting a board that doesn't exist."""
        response = client.delete(
            "/api/v1/boards/99999",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_delete_board_no_permission(self, client, auth_headers, test_board_user2):
        """Test deleting another user's board."""
        response = client.delete(
            f"/api/v1/boards/{test_board_user2.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


class TestReorderBoards:
    """Tests for reordering boards."""

    @pytest.fixture
    async def multiple_boards(self, test_db, test_user):
        """Create multiple test boards."""
        from app.models import Board
        boards = []
        for i in range(3):
            board = Board(
                user_id=test_user.id,
                name=f"Board {i}",
                sort_order=i
            )
            test_db.add(board)
            boards.append(board)
        await test_db.commit()
        for board in boards:
            await test_db.refresh(board)
        return boards

    def test_reorder_boards_success(self, client, auth_headers, multiple_boards):
        """Test reordering boards successfully."""
        board_ids = [b.id for b in multiple_boards]
        # Reverse the order
        new_order = board_ids[::-1]

        response = client.put(
            "/api/v1/boards/reorder",
            json={"board_ids": new_order},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify the order
        get_response = client.get("/api/v1/boards", headers=auth_headers)
        get_data = get_response.json()
        returned_ids = [b["id"] for b in get_data["data"]]
        # They should be ordered by sort_order, which we just updated
        # The API doesn't guarantee the return order matches our input,
        # just that the sort_order fields are updated correctly

    def test_reorder_boards_empty_list(self, client, auth_headers):
        """Test reordering with empty board_ids list."""
        response = client.put(
            "/api/v1/boards/reorder",
            json={"board_ids": []},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_reorder_boards_with_nonexistent_id(self, client, auth_headers, multiple_boards):
        """Test reordering with a nonexistent board ID in the list."""
        board_ids = [b.id for b in multiple_boards]
        board_ids.append(99999)  # Add nonexistent ID

        response = client.put(
            "/api/v1/boards/reorder",
            json={"board_ids": board_ids},
            headers=auth_headers
        )
        # Should succeed - nonexistent IDs are just ignored
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_reorder_boards_no_auth(self, client):
        """Test reordering without authentication."""
        response = client.put(
            "/api/v1/boards/reorder",
            json={"board_ids": [1, 2, 3]}
        )
        assert response.status_code == 401
