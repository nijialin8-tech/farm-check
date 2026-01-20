"""Utilities for Windows window management and identification."""
import ctypes
from ctypes import wintypes

# Windows API constants
FLASHW_ALL = 0x00000003
FLASHW_TIMERNOFG = 0x0000000C


class FLASHWINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.UINT),
        ('hwnd', wintypes.HWND),
        ('dwFlags', wintypes.DWORD),
        ('uCount', wintypes.UINT),
        ('dwTimeout', wintypes.DWORD)
    ]


def is_window_valid(hwnd):
    """
    Check if a window handle is still valid.

    Args:
        hwnd: Windows window handle (integer)

    Returns:
        bool: True if window exists and is valid
    """
    try:
        return ctypes.windll.user32.IsWindow(hwnd) != 0
    except (OSError, AttributeError, ctypes.ArgumentError):
        return False


def flash_window(hwnd, count=3):
    """
    Flash a window's taskbar button to help user identify it.

    Args:
        hwnd: Windows window handle (integer)
        count: Number of times to flash (default: 3)

    Returns:
        bool: True if flash succeeded, False otherwise
    """
    if not is_window_valid(hwnd):
        return False

    try:
        flash_info = FLASHWINFO()
        flash_info.cbSize = ctypes.sizeof(FLASHWINFO)
        flash_info.hwnd = hwnd
        flash_info.dwFlags = FLASHW_ALL | FLASHW_TIMERNOFG
        flash_info.uCount = count
        flash_info.dwTimeout = 0

        # FlashWindowEx return value indicates previous window state,
        # not success/failure. Success is guaranteed if hwnd is valid.
        ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash_info))
        return True
    except (OSError, ctypes.ArgumentError) as e:
        print(f"Error flashing window: {e}")
        return False


def get_maple_windows():
    """
    Get all MapleRoyals windows with their HWNDs.

    Returns:
        list: List of tuples (hwnd, title, position_info)
              position_info is dict with 'left', 'top', 'width', 'height'
    """
    try:
        import pygetwindow as gw
    except ImportError:
        return []

    windows = []
    seen_hwnds = set()

    all_windows = [w for w in gw.getAllWindows() if 'MapleRoyals' in w.title]

    for w in all_windows:
        try:
            # Access internal _hWnd attribute (pygetwindow implementation detail)
            if not hasattr(w, '_hWnd'):
                continue
            hwnd = w._hWnd

            # Skip duplicates
            if hwnd in seen_hwnds:
                continue

            position_info = {
                'left': w.left,
                'top': w.top,
                'width': w.width,
                'height': w.height
            }

            windows.append((hwnd, w.title, position_info))
            seen_hwnds.add(hwnd)

        except (AttributeError, OSError):
            continue

    return windows
