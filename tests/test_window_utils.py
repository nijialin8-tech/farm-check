"""Tests for window_utils module."""
import sys
import pytest
from unittest.mock import patch, MagicMock
import window_utils


def test_is_window_valid_with_invalid_hwnd():
    """Test that invalid HWND returns False."""
    result = window_utils.is_window_valid(999999999)
    assert result is False


def test_flash_window_with_invalid_hwnd():
    """Test that flashing invalid window returns False."""
    result = window_utils.flash_window(999999999)
    assert result is False


def test_is_window_valid_with_valid_hwnd():
    """Test that valid HWND returns True."""
    import ctypes
    # Create windll if it doesn't exist (macOS/Linux)
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()

    with patch.object(ctypes.windll.user32, 'IsWindow', return_value=1) as mock_is_window:
        result = window_utils.is_window_valid(12345)
        assert result is True
        mock_is_window.assert_called_once_with(12345)


def test_get_maple_windows_empty():
    """Test getting windows when none exist."""
    mock_gw = MagicMock()
    mock_gw.getAllWindows.return_value = []

    with patch.dict(sys.modules, {'pygetwindow': mock_gw}):
        result = window_utils.get_maple_windows()
        assert result == []


def test_get_maple_windows_filters_non_maple():
    """Test that non-MapleRoyals windows are filtered out."""
    mock_window = MagicMock()
    mock_window.title = "Chrome Browser"

    mock_gw = MagicMock()
    mock_gw.getAllWindows.return_value = [mock_window]

    with patch.dict(sys.modules, {'pygetwindow': mock_gw}):
        result = window_utils.get_maple_windows()
        assert result == []


def test_get_maple_windows_returns_valid_windows():
    """Test that MapleRoyals windows are returned with HWND."""
    mock_window = MagicMock()
    mock_window.title = "MapleRoyals"
    mock_window._hWnd = 12345
    mock_window.left = 100
    mock_window.top = 200
    mock_window.width = 800
    mock_window.height = 600

    mock_gw = MagicMock()
    mock_gw.getAllWindows.return_value = [mock_window]

    with patch.dict(sys.modules, {'pygetwindow': mock_gw}):
        result = window_utils.get_maple_windows()

        assert len(result) == 1
        hwnd, title, pos = result[0]
        assert hwnd == 12345
        assert title == "MapleRoyals"
        assert pos['left'] == 100
        assert pos['top'] == 200
        assert pos['width'] == 800
        assert pos['height'] == 600


def test_get_maple_windows_deduplicates_by_hwnd():
    """Test that duplicate HWNDs are filtered out."""
    mock_window1 = MagicMock()
    mock_window1.title = "MapleRoyals"
    mock_window1._hWnd = 12345
    mock_window1.left = 100
    mock_window1.top = 200
    mock_window1.width = 800
    mock_window1.height = 600

    mock_window2 = MagicMock()
    mock_window2.title = "MapleRoyals"
    mock_window2._hWnd = 12345  # Same HWND
    mock_window2.left = 100
    mock_window2.top = 200
    mock_window2.width = 800
    mock_window2.height = 600

    mock_gw = MagicMock()
    mock_gw.getAllWindows.return_value = [mock_window1, mock_window2]

    with patch.dict(sys.modules, {'pygetwindow': mock_gw}):
        result = window_utils.get_maple_windows()

        assert len(result) == 1


# Additional tests for real logic verification and edge cases


def test_is_window_valid_converts_nonzero_to_true():
    """Verify that any non-zero return is treated as True."""
    import ctypes
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()

    with patch.object(ctypes.windll.user32, 'IsWindow', return_value=42):
        assert window_utils.is_window_valid(12345) is True


def test_is_window_valid_converts_zero_to_false():
    """Verify that zero return is treated as False."""
    import ctypes
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()

    with patch.object(ctypes.windll.user32, 'IsWindow', return_value=0):
        assert window_utils.is_window_valid(12345) is False


def test_is_window_valid_handles_os_error():
    """Verify OSError is caught and returns False."""
    import ctypes
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()

    with patch.object(ctypes.windll.user32, 'IsWindow', side_effect=OSError):
        assert window_utils.is_window_valid(12345) is False


def test_is_window_valid_handles_argument_error():
    """Verify ArgumentError is caught and returns False."""
    import ctypes
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()

    with patch.object(ctypes.windll.user32, 'IsWindow', side_effect=ctypes.ArgumentError):
        assert window_utils.is_window_valid(12345) is False


def test_flash_window_success_with_valid_hwnd():
    """Verify flash_window returns True for valid window."""
    import ctypes
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()

    with patch('window_utils.is_window_valid', return_value=True):
        with patch.object(ctypes.windll.user32, 'FlashWindowEx'):
            result = window_utils.flash_window(12345)
            assert result is True


def test_flash_window_handles_os_error():
    """Verify flash_window handles OSError gracefully."""
    import ctypes
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()

    with patch('window_utils.is_window_valid', return_value=True):
        with patch.object(ctypes.windll.user32, 'FlashWindowEx', side_effect=OSError):
            result = window_utils.flash_window(12345)
            assert result is False


def test_get_maple_windows_handles_missing_hwnd_attribute():
    """Verify windows without _hWnd are skipped."""
    mock_window = MagicMock()
    mock_window.title = "MapleRoyals"
    # Remove _hWnd to simulate hasattr check
    del mock_window._hWnd

    mock_gw = MagicMock()
    mock_gw.getAllWindows.return_value = [mock_window]

    with patch.dict(sys.modules, {'pygetwindow': mock_gw}):
        result = window_utils.get_maple_windows()
        assert result == []


def test_get_maple_windows_handles_os_error_during_access():
    """Verify OSError during position access is handled."""
    from unittest.mock import PropertyMock

    mock_window = MagicMock()
    mock_window.title = "MapleRoyals"
    mock_window._hWnd = 12345
    # Make accessing position info raise OSError
    type(mock_window).left = PropertyMock(side_effect=OSError("Window destroyed"))

    mock_gw = MagicMock()
    mock_gw.getAllWindows.return_value = [mock_window]

    with patch.dict(sys.modules, {'pygetwindow': mock_gw}):
        result = window_utils.get_maple_windows()
        assert result == []


def test_get_maple_windows_position_dict_structure():
    """Verify position dict contains all required keys with correct types."""
    mock_window = MagicMock()
    mock_window.title = "MapleRoyals"
    mock_window._hWnd = 999
    mock_window.left = 1
    mock_window.top = 2
    mock_window.width = 3
    mock_window.height = 4

    mock_gw = MagicMock()
    mock_gw.getAllWindows.return_value = [mock_window]

    with patch.dict(sys.modules, {'pygetwindow': mock_gw}):
        result = window_utils.get_maple_windows()
        assert len(result) == 1
        hwnd, title, pos = result[0]

        # Test structure, not specific values
        assert set(pos.keys()) == {'left', 'top', 'width', 'height'}
        assert all(isinstance(v, int) for v in pos.values())
