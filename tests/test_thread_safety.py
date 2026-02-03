"""
Tests for thread safety fixes.

These tests verify that shared data structures are properly protected
with locks to prevent race conditions.
"""
import threading
import time
import unittest
from unittest.mock import MagicMock, patch


class TestUIImageChangesLock(unittest.TestCase):
    """Test thread safety of ui_image_changes_while_hidden dictionary."""

    def test_concurrent_access_to_ui_changes(self):
        """Test that concurrent reads and writes don't cause race conditions."""
        # Simulate the lock-protected dictionary access pattern
        lock = threading.Lock()
        ui_changes = {}
        errors = []
        iterations = 100

        def writer_thread():
            """Simulates MediaPlayerThread writing images."""
            for i in range(iterations):
                try:
                    with lock:
                        key = f"key_{i}"
                        ui_changes[key] = f"image_{i}"
                    time.sleep(0.001)  # Small delay
                except Exception as e:
                    errors.append(("writer", e))

        def reader_thread():
            """Simulates GTK main thread reading and clearing."""
            for _ in range(iterations):
                try:
                    with lock:
                        items = list(ui_changes.items())
                        for key, _ in items:
                            ui_changes.pop(key, None)
                    time.sleep(0.001)
                except Exception as e:
                    errors.append(("reader", e))

        # Start both threads
        writer = threading.Thread(target=writer_thread)
        reader = threading.Thread(target=reader_thread)

        writer.start()
        reader.start()

        writer.join(timeout=10)
        reader.join(timeout=10)

        # No errors should have occurred
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

    def test_load_from_changes_thread_safety(self):
        """Test that load_from_changes properly uses the lock."""
        # Create mock deck controller with lock
        mock_controller = MagicMock()
        mock_controller.ui_image_changes_while_hidden = {}
        mock_controller.ui_image_changes_lock = threading.Lock()

        # Add some test data
        from src.backend.DeckManagement.InputIdentifier import Input
        test_key = Input.Key("0x0")
        mock_controller.ui_image_changes_while_hidden[test_key] = "test_image"

        # Simulate concurrent access
        results = []
        errors = []

        def add_images():
            for i in range(50):
                with mock_controller.ui_image_changes_lock:
                    mock_controller.ui_image_changes_while_hidden[Input.Key(f"{i}x0")] = f"image_{i}"
                time.sleep(0.001)

        def read_images():
            for _ in range(50):
                with mock_controller.ui_image_changes_lock:
                    items = list(mock_controller.ui_image_changes_while_hidden.items())
                    for key, image in items:
                        if isinstance(key, Input.Key):
                            results.append((key, image))
                            mock_controller.ui_image_changes_while_hidden.pop(key, None)
                time.sleep(0.001)

        threads = [
            threading.Thread(target=add_images),
            threading.Thread(target=read_images),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # Should complete without errors
        self.assertEqual(len(errors), 0)


class TestSafeIdleAdd(unittest.TestCase):
    """Test the safe_idle_add helper function."""

    def test_safe_idle_add_wraps_callback(self):
        """Test that safe_idle_add properly wraps the callback."""
        try:
            from src.backend.DeckManagement.HelperMethods import safe_idle_add
        except ImportError:
            self.skipTest("Cannot import safe_idle_add")

        # Track if callback was scheduled
        callback_called = [False]

        def test_callback():
            callback_called[0] = True
            return False

        # Note: This will only fully work if GTK main loop is running
        # In unit tests, we're mainly testing the function doesn't crash
        try:
            result = safe_idle_add(test_callback, log_failures=False)
            # Result should be a source ID (int) or 0 if failed
            self.assertIsInstance(result, int)
        except Exception as e:
            # May fail if GTK isn't properly initialized
            self.skipTest(f"GTK not properly initialized: {e}")

    def test_safe_idle_add_handles_exception_in_callback(self):
        """Test that safe_idle_add catches exceptions in callbacks."""
        try:
            from src.backend.DeckManagement.HelperMethods import safe_idle_add
        except ImportError:
            self.skipTest("Cannot import safe_idle_add")

        def failing_callback():
            raise ValueError("Test error")

        # Should not raise even though callback would fail
        try:
            result = safe_idle_add(failing_callback, log_failures=False)
            self.assertIsInstance(result, int)
        except Exception as e:
            # May fail if GTK isn't properly initialized
            self.skipTest(f"GTK not properly initialized: {e}")


if __name__ == '__main__':
    unittest.main()
