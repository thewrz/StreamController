"""
Pytest configuration for StreamController tests.
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def pytest_configure(config):
    """Configure pytest."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "requires_gtk: mark test as requiring GTK"
    )
    config.addinivalue_line(
        "markers", "requires_dbus: mark test as requiring DBus session"
    )
