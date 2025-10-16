"""Tests for DocumentApp class."""

from unittest.mock import Mock

from clippy.ui.document_app import DocumentApp


def test_document_app_initialization() -> None:
    """Test that DocumentApp initializes correctly."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent, auto_approve=False)

    assert app.agent is mock_agent
    assert app.auto_approve is False
    assert app.waiting_for_approval is False
    assert app.current_approval_dialog is None
    assert app.current_approval_backdrop is None


def test_document_app_initialization_with_auto_approve() -> None:
    """Test that DocumentApp can be initialized with auto_approve enabled."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent, auto_approve=True)

    assert app.agent is mock_agent
    assert app.auto_approve is True


def test_document_app_has_css() -> None:
    """Test that DocumentApp has CSS styles defined."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent)

    assert hasattr(app, "CSS")
    assert len(app.CSS) > 0
    # Check for some key CSS selectors
    assert "Screen" in app.CSS
    assert "#header" in app.CSS
    assert "#conversation-log" in app.CSS


def test_document_app_has_bindings() -> None:
    """Test that DocumentApp has key bindings defined."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent)

    assert hasattr(app, "BINDINGS")
    assert len(app.BINDINGS) > 0


def test_handle_approval_response_yes() -> None:
    """Test handling approval response 'y'."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent)
    app.waiting_for_approval = True
    app.current_approval_dialog = Mock()
    app.current_approval_backdrop = Mock()

    app.handle_approval_response("y")

    # Should clear approval state
    assert app.waiting_for_approval is False
    assert app.current_approval_dialog is None
    # Should have queued the response
    assert not app.approval_queue.empty()
    assert app.approval_queue.get() == "y"


def test_handle_approval_response_no() -> None:
    """Test handling approval response 'n'."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent)
    app.waiting_for_approval = True
    app.current_approval_dialog = Mock()
    app.current_approval_backdrop = Mock()

    app.handle_approval_response("n")

    assert app.waiting_for_approval is False
    assert not app.approval_queue.empty()
    assert app.approval_queue.get() == "n"


def test_handle_approval_response_stop() -> None:
    """Test handling approval response 'stop'."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent)
    app.waiting_for_approval = True
    app.current_approval_dialog = Mock()
    app.current_approval_backdrop = Mock()

    app.handle_approval_response("stop")

    assert app.waiting_for_approval is False
    assert not app.approval_queue.empty()
    assert app.approval_queue.get() == "stop"


def test_handle_approval_response_allow() -> None:
    """Test handling approval response 'allow'."""
    mock_agent = Mock()
    app = DocumentApp(mock_agent)
    app.waiting_for_approval = True
    app.current_approval_dialog = Mock()
    app.current_approval_backdrop = Mock()

    app.handle_approval_response("allow")

    assert app.waiting_for_approval is False
    assert not app.approval_queue.empty()
    assert app.approval_queue.get() == "allow"
