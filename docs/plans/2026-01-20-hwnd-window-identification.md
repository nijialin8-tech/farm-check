# HWND-Based Window Identification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace title-based window selection with HWND-based identification to support multiple MapleRoyals windows with identical titles, add preview flashing for window identification.

**Architecture:** Refactor window selection to use Windows HWND (window handle) as unique identifier. Add preview mechanism using taskbar flashing (FlashWindowEx API). Validate HWNDs on startup and prompt re-selection if windows closed.

**Tech Stack:** pywin32 (for FlashWindowEx API), pygetwindow (for window enumeration), existing keyboard/threading infrastructure

---

## Task 1: Add pywin32 Dependency

**Files:**
- Modify: `requirements.txt`

**Step 1: Add pywin32 to requirements**

Add line to requirements.txt:
```
pywin32==306
```

**Step 2: Verify dependencies install**

Run: `pip install -r requirements.txt`
Expected: Successfully installs pywin32

**Step 3: Commit dependency update**

```bash
git add requirements.txt
git commit -m "deps: add pywin32 for window flashing API"
```

---

## Task 2: Create Window Utilities Module

**Files:**
- Create: `window_utils.py`

**Step 1: Create window utilities with HWND validation**

Create `window_utils.py`:

```python
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
    except Exception:
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

        result = ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash_info))
        return result != 0
    except Exception as e:
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
            hwnd = w._hWnd

            # Skip duplicates
            if hwnd in seen_hwnds:
                continue

            # Verify window is accessible
            _ = w.size
            _ = w.title

            position_info = {
                'left': w.left,
                'top': w.top,
                'width': w.width,
                'height': w.height
            }

            windows.append((hwnd, w.title, position_info))
            seen_hwnds.add(hwnd)

        except Exception:
            continue

    return windows
```

**Step 2: Verify module imports**

Run: `python -c "import window_utils; print('OK')"`
Expected: Prints "OK"

**Step 3: Commit window utilities**

```bash
git add window_utils.py
git commit -m "feat: add window utilities with HWND validation and flashing"
```

---

## Task 3: Create Tests for Window Utilities

**Files:**
- Create: `tests/test_window_utils.py`

**Step 1: Create test directory**

Run: `mkdir -p tests`

**Step 2: Write tests for window utilities**

Create `tests/test_window_utils.py`:

```python
"""Tests for window_utils module."""
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


@patch('window_utils.ctypes.windll.user32.IsWindow')
def test_is_window_valid_with_valid_hwnd(mock_is_window):
    """Test that valid HWND returns True."""
    mock_is_window.return_value = 1
    result = window_utils.is_window_valid(12345)
    assert result is True
    mock_is_window.assert_called_once_with(12345)


@patch('pygetwindow.getAllWindows')
def test_get_maple_windows_empty(mock_get_all):
    """Test getting windows when none exist."""
    mock_get_all.return_value = []
    result = window_utils.get_maple_windows()
    assert result == []


@patch('pygetwindow.getAllWindows')
def test_get_maple_windows_filters_non_maple(mock_get_all):
    """Test that non-MapleRoyals windows are filtered out."""
    mock_window = MagicMock()
    mock_window.title = "Chrome Browser"
    mock_get_all.return_value = [mock_window]

    result = window_utils.get_maple_windows()
    assert result == []


@patch('pygetwindow.getAllWindows')
def test_get_maple_windows_returns_valid_windows(mock_get_all):
    """Test that MapleRoyals windows are returned with HWND."""
    mock_window = MagicMock()
    mock_window.title = "MapleRoyals"
    mock_window._hWnd = 12345
    mock_window.left = 100
    mock_window.top = 200
    mock_window.width = 800
    mock_window.height = 600
    mock_window.size = (800, 600)

    mock_get_all.return_value = [mock_window]

    result = window_utils.get_maple_windows()

    assert len(result) == 1
    hwnd, title, pos = result[0]
    assert hwnd == 12345
    assert title == "MapleRoyals"
    assert pos['left'] == 100
    assert pos['top'] == 200
    assert pos['width'] == 800
    assert pos['height'] == 600


@patch('pygetwindow.getAllWindows')
def test_get_maple_windows_deduplicates_by_hwnd(mock_get_all):
    """Test that duplicate HWNDs are filtered out."""
    mock_window1 = MagicMock()
    mock_window1.title = "MapleRoyals"
    mock_window1._hWnd = 12345
    mock_window1.left = 100
    mock_window1.top = 200
    mock_window1.width = 800
    mock_window1.height = 600
    mock_window1.size = (800, 600)

    mock_window2 = MagicMock()
    mock_window2.title = "MapleRoyals"
    mock_window2._hWnd = 12345  # Same HWND
    mock_window2.left = 100
    mock_window2.top = 200
    mock_window2.width = 800
    mock_window2.height = 600
    mock_window2.size = (800, 600)

    mock_get_all.return_value = [mock_window1, mock_window2]

    result = window_utils.get_maple_windows()

    assert len(result) == 1
```

**Step 3: Run tests**

Run: `pytest tests/test_window_utils.py -v`
Expected: All tests pass

**Step 4: Commit tests**

```bash
git add tests/test_window_utils.py
git commit -m "test: add comprehensive tests for window utilities"
```

---

## Task 4: Refactor Window Selection with Preview

**Files:**
- Modify: `timer.py:76-156` (replace `select_windows` function)

**Step 1: Import window utilities in timer.py**

Add at top of timer.py after existing imports:

```python
import window_utils
```

**Step 2: Replace select_windows function**

Replace the entire `select_windows()` function (lines 76-156) with:

```python
def select_windows():
    """
    Let user select which MapleRoyals windows to auto-click with preview.
    Returns list of HWNDs (integers) or None for all windows.
    """
    if not WINDOW_AUTOMATION_AVAILABLE:
        return None

    try:
        # Get all MapleRoyals windows with HWNDs
        windows = window_utils.get_maple_windows()

        if not windows:
            print("  No MapleRoyals windows currently running.")
            print("  Will auto-click all MapleRoyals windows when available.")
            return None

        print(f"\n  Found {len(windows)} MapleRoyals window(s):")
        for i, (hwnd, title, pos) in enumerate(windows, 1):
            position_str = f"at ({pos['left']}, {pos['top']})"
            print(f"    [{i}] {title} {position_str} (HWND: {hwnd})")

        print("\n  Commands:")
        print("    Type number (e.g., '1') to PREVIEW a window (it will flash)")
        print("    Type '/all' to select all windows")
        print("    Type numbers separated by commas (e.g., '1,3') to SELECT")
        print("    Press Enter to cancel")

        selected_hwnds = []

        while True:
            print("\n  Enter command: ", end='', flush=True)
            selection = input().strip().lower()

            if not selection:
                print("  Selection cancelled. Auto-click will be disabled.")
                return False

            if selection == '/all':
                all_hwnds = [hwnd for hwnd, _, _ in windows]
                print(f"  Selected: All {len(all_hwnds)} windows")
                return all_hwnds

            # Check if it's a single number (preview mode)
            if selection.isdigit():
                idx = int(selection)
                if 1 <= idx <= len(windows):
                    hwnd, title, pos = windows[idx - 1]
                    print(f"  Flashing window [{idx}]: {title}...")
                    if window_utils.flash_window(hwnd, count=5):
                        print(f"  -> Window flashed! Did you see it?")
                    else:
                        print(f"  -> Warning: Could not flash window (may be minimized)")
                    continue
                else:
                    print(f"  Invalid index: {idx}")
                    continue

            # Check if it's a comma-separated selection
            if ',' in selection or selection.isdigit():
                try:
                    indices = [int(x.strip()) for x in selection.split(',')]
                    selected_hwnds = []

                    for idx in indices:
                        if 1 <= idx <= len(windows):
                            hwnd, title, _ = windows[idx - 1]
                            selected_hwnds.append(hwnd)
                        else:
                            print(f"  Warning: Invalid index {idx}, skipping")

                    if not selected_hwnds:
                        print("  No valid windows selected. Try again.")
                        continue

                    print(f"  Selected {len(selected_hwnds)} window(s):")
                    for hwnd in selected_hwnds:
                        # Find matching window for display
                        for h, title, pos in windows:
                            if h == hwnd:
                                print(f"    - {title} (HWND: {hwnd})")
                                break

                    return selected_hwnds

                except ValueError:
                    print("  Invalid input. Use numbers separated by commas.")
                    continue

            print("  Unknown command. Try again.")

    except Exception as e:
        print(f"  Error during window selection: {e}")
        print("  Will auto-click all MapleRoyals windows.")
        return None
```

**Step 3: Test window selection manually**

Run: `python timer.py` and test:
1. Type a single number to preview
2. Verify window flashes in taskbar
3. Select multiple windows with commas
4. Verify selection works

**Step 4: Commit window selection refactor**

```bash
git add timer.py
git commit -m "feat: add HWND-based window selection with preview flashing"
```

---

## Task 5: Update Config to Store HWNDs

**Files:**
- Modify: `timer.py:245-252` (setup_config return statement)
- Modify: `timer.py:292-314` (click_maple_windows function)

**Step 1: Update setup_config to return HWNDs**

In `setup_config()`, replace the return statement (around line 245-252):

```python
    return {
        'trigger_key': trigger_key_name,
        'stop_key': stop_key_name,
        'countdown_seconds': countdown_seconds,
        'random_offset_seconds': random_offset,
        'auto_click_windows': auto_click,
        'selected_window_hwnds': selected_windows  # Changed from selected_window_titles
    }
```

**Step 2: Update click_maple_windows to use HWNDs**

Replace `click_maple_windows()` function (lines 254-391) with:

```python
def click_maple_windows():
    """
    Find and click MapleRoyals windows using stored HWNDs.
    Validates HWNDs before clicking.
    """
    if not WINDOW_AUTOMATION_AVAILABLE:
        print("Window automation not available")
        return

    try:
        # Get all current MapleRoyals windows
        all_windows = window_utils.get_maple_windows()

        if not all_windows:
            print("No MapleRoyals windows found")
            return

        # Get selected HWNDs from config
        selected_hwnds = config.get('selected_window_hwnds')

        # Build hwnd -> window mapping
        hwnd_map = {hwnd: (title, pos) for hwnd, title, pos in all_windows}

        if selected_hwnds is not None:
            # Validate selected HWNDs are still valid
            valid_hwnds = [h for h in selected_hwnds if h in hwnd_map]

            if not valid_hwnds:
                print(f"None of the selected windows are currently running.")
                print(f"Selected HWNDs: {selected_hwnds}")
                print(f"Available HWNDs: {list(hwnd_map.keys())}")
                print(f"\nPlease run '/setup' to re-select windows.")
                return

            # Check if some windows are missing
            missing_count = len(selected_hwnds) - len(valid_hwnds)
            if missing_count > 0:
                print(f"\nWarning: {missing_count} selected window(s) not running")

            windows_to_click = valid_hwnds
            print(f"\nFound {len(windows_to_click)} of {len(selected_hwnds)} selected window(s)")
        else:
            # Click all windows
            windows_to_click = list(hwnd_map.keys())
            print(f"\nFound {len(windows_to_click)} MapleRoyals window(s)")

        print("Starting auto-click sequence...")

        # Shuffle for human-like behavior
        import random
        random.shuffle(windows_to_click)

        # Calculate random delays
        total_time = 5.0
        num_windows = len(windows_to_click)
        delays = []
        remaining_time = total_time

        for i in range(num_windows - 1):
            max_delay = min(2.5, remaining_time - (num_windows - i - 1) * 0.3)
            delay = random.uniform(0.5, max_delay)
            delays.append(delay)
            remaining_time -= delay

        delays.append(max(0.3, remaining_time))

        # Click each window by HWND
        import pygetwindow as gw

        for i, hwnd in enumerate(windows_to_click):
            try:
                # Get window by HWND
                matching_windows = [w for w in gw.getAllWindows() if w._hWnd == hwnd]

                if not matching_windows:
                    print(f"  [{i+1}/{num_windows}] Window HWND {hwnd} no longer available")
                    continue

                window = matching_windows[0]
                title, pos = hwnd_map[hwnd]

                # Activate and click window
                try:
                    window_left, window_top = window.left, window.top
                    window_width, window_height = window.width, window.height

                    offset_x = int(random.uniform(-0.3, 0.3) * window_width)
                    offset_y = int(random.uniform(-0.3, 0.3) * window_height)

                    click_x = window_left + window_width // 2 + offset_x
                    click_y = window_top + window_height // 2 + offset_y

                    move_duration = random.uniform(0.3, 0.8)

                    import pyautogui
                    pyautogui.moveTo(click_x, click_y, duration=move_duration)
                    import time
                    time.sleep(random.uniform(0.05, 0.15))
                    pyautogui.click()
                    time.sleep(0.2)

                except Exception:
                    try:
                        window.activate()
                        time.sleep(0.15)
                    except:
                        print(f"  [{i+1}/{num_windows}] Warning: Could not activate HWND {hwnd}")

                keyboard.press_and_release(config['trigger_key'])
                print(f"  [{i+1}/{num_windows}] Clicked: {title} (HWND: {hwnd})")

                if i < len(delays):
                    time.sleep(delays[i])

            except Exception as e:
                print(f"  [{i+1}/{num_windows}] Error with HWND {hwnd}: {str(e)[:50]}...")
                continue

        print("Auto-click sequence completed")

    except Exception as e:
        print(f"Error in click_maple_windows: {e}")
```

**Step 3: Test auto-click with HWNDs**

Run program and verify:
1. Select windows and save config
2. Trigger timer completion
3. Verify auto-click uses HWNDs correctly

**Step 4: Commit HWND-based clicking**

```bash
git add timer.py
git commit -m "feat: use HWND-based window identification for auto-click"
```

---

## Task 6: Add HWND Validation on Startup

**Files:**
- Modify: `timer.py:604-658` (main function)

**Step 1: Add HWND validation after config load**

In `main()` function, after loading existing config (around line 612-628), add validation logic:

```python
    if existing_config:
        print("Found existing configuration:")
        print(f"  START/RESET: [{existing_config['trigger_key']}]")
        print(f"  STOP: [{existing_config['stop_key']}]")
        print(f"  Countdown: {existing_config['countdown_seconds']} seconds")
        auto_click_status = "ENABLED" if existing_config.get('auto_click_windows', False) else "DISABLED"
        print(f"  Auto-click MapleRoyals: {auto_click_status}")

        # Validate HWNDs if auto-click is enabled
        need_reselect = False
        if existing_config.get('auto_click_windows', False):
            selected_hwnds = existing_config.get('selected_window_hwnds')

            # Migration: convert old format to new format
            if selected_hwnds is None and 'selected_window_titles' in existing_config:
                print("\n  ⚠️  Old configuration format detected (title-based)")
                print("  Please re-select windows using new HWND-based system")
                need_reselect = True
            elif selected_hwnds:
                # Validate HWNDs
                import window_utils
                valid_hwnds = [h for h in selected_hwnds if window_utils.is_window_valid(h)]

                if len(valid_hwnds) == 0:
                    print(f"\n  ⚠️  All selected windows are closed")
                    print(f"  Please re-select windows")
                    need_reselect = True
                elif len(valid_hwnds) < len(selected_hwnds):
                    missing = len(selected_hwnds) - len(valid_hwnds)
                    print(f"\n  ⚠️  {missing} of {len(selected_hwnds)} selected window(s) are closed")
                    print(f"  You may want to re-select windows")
                else:
                    print(f"  Selected windows: {len(selected_hwnds)} window(s) (all valid)")

        if need_reselect:
            print("\nAuto-click needs reconfiguration. Type '/setup' or press Enter to skip: ", end='', flush=True)
        else:
            print("\nDo you want to reconfigure? (Type '/setup' or press Enter to skip): ", end='', flush=True)
```

**Step 2: Update backward compatibility logic**

In `main()`, ensure backward compatibility (around line 660-666):

```python
    # Ensure auto_click_windows exists in config (for backwards compatibility)
    if 'auto_click_windows' not in config:
        config['auto_click_windows'] = DEFAULT_AUTO_CLICK_WINDOWS

    # Ensure selected_window_hwnds exists in config (for backwards compatibility)
    if 'selected_window_hwnds' not in config:
        # Migration from old format
        if 'selected_window_titles' in config:
            del config['selected_window_titles']
        config['selected_window_hwnds'] = None
```

**Step 3: Update config display in main**

Update the display section (around line 668-681) to show HWND info:

```python
    print(f"\n=== Program started ===")
    print(f"Press [{config['trigger_key']}] to START/RESET")
    print(f"Press [{config['stop_key']}] to STOP")
    print(f"Countdown: {config['countdown_seconds']} seconds")
    if config.get('auto_click_windows', False):
        print("Auto-click MapleRoyals: ENABLED")
        selected_hwnds = config.get('selected_window_hwnds')
        if selected_hwnds:
            print(f"  Selected {len(selected_hwnds)} specific window(s)")
        else:
            print(f"  Mode: Click all windows")
    else:
        print("Auto-click MapleRoyals: DISABLED")
    print("Type '/setup' to reconfigure\n")
```

**Step 4: Test startup validation**

Test scenarios:
1. Start with valid HWNDs -> Should show "all valid"
2. Close one selected window -> Should show warning
3. Close all selected windows -> Should prompt re-selection
4. Load old config with titles -> Should prompt migration

**Step 5: Commit startup validation**

```bash
git add timer.py
git commit -m "feat: validate HWNDs on startup and migrate old configs"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

**Step 1: Update CLAUDE.md with HWND feature**

Add to CLAUDE.md under "### 7. 視覺化功能：即時進度條" section:

```markdown
---

### 8. 視窗識別改進：HWND 唯一識別

**用戶需求：**
```
自動點擊的部分因為遊戲本身可以多開，所有的名字都是一樣，有辦法找到系統上面的唯一識別碼去點嗎？
此外我需要當滑鼠點選到指定的視窗時，他必須在前景的最上面，避免被其他視窗卡到，導致功能不能使用
```

**實作內容：**
- ✅ 使用 Windows HWND (視窗控制碼) 作為唯一識別
- ✅ 加入視窗預覽功能 - 任務列閃爍確認視窗
- ✅ 啟動時驗證 HWND 是否仍有效
- ✅ 舊設定檔自動遷移提示
- ✅ 設定時可輸入單一數字預覽視窗（閃爍 5 次）
- ✅ 設定時可輸入逗號分隔數字選擇多個視窗

**技術細節：**
- 使用 `pywin32` 的 `FlashWindowEx` API 實現任務列閃爍
- 使用 `IsWindow` API 驗證 HWND 有效性
- HWND 在視窗生命週期內保持唯一且不變
- 視窗關閉後 HWND 失效，需重新選擇

**設定流程：**
```
Found 3 MapleRoyals window(s):
  [1] MapleRoyals at (0, 0) (HWND: 262148)
  [2] MapleRoyals at (800, 0) (HWND: 131074)
  [3] MapleRoyals at (1600, 0) (HWND: 393218)

Commands:
  Type number (e.g., '1') to PREVIEW a window (it will flash)
  Type '/all' to select all windows
  Type numbers separated by commas (e.g., '1,3') to SELECT
```

**設定檔格式：**
```json
{
  "selected_window_hwnds": [262148, 393218],
  "auto_click_windows": true
}
```
```

**Step 2: Update README.md**

Add section about window selection:

```markdown
## 視窗選擇功能

### HWND 唯一識別

程式使用 Windows 視窗控制碼 (HWND) 來識別視窗，即使多個 MapleRoyals 視窗名稱相同也能正確識別。

### 預覽功能

在設定時，輸入單一數字（如 `1`）可以讓對應視窗的任務列圖示閃爍，幫助你確認是哪個視窗。

### 選擇視窗

- `/all` - 選擇所有 MapleRoyals 視窗
- `1,3,5` - 選擇特定視窗（用逗號分隔）
- 單一數字 - 預覽該視窗（任務列閃爍）

### HWND 驗證

程式啟動時會自動檢查已選擇的視窗是否仍在執行：
- ✅ 所有視窗有效 - 直接使用
- ⚠️ 部分視窗關閉 - 顯示警告，仍可使用剩餘視窗
- ❌ 全部視窗關閉 - 提示重新選擇
```

**Step 3: Commit documentation updates**

```bash
git add CLAUDE.md README.md
git commit -m "docs: document HWND-based window identification feature"
```

---

## Task 8: Add Integration Test

**Files:**
- Create: `tests/test_integration_hwnd.py`

**Step 1: Create integration test**

Create `tests/test_integration_hwnd.py`:

```python
"""Integration tests for HWND-based window selection."""
import pytest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile


@pytest.fixture
def mock_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            'trigger_key': 'page up',
            'stop_key': 'page down',
            'countdown_seconds': 130,
            'random_offset_seconds': 5,
            'auto_click_windows': True,
            'selected_window_hwnds': [12345, 67890]
        }
        json.dump(config, f)
        temp_path = f.name

    yield temp_path

    os.unlink(temp_path)


def test_config_stores_hwnds(mock_config_file):
    """Test that config correctly stores HWNDs."""
    with open(mock_config_file, 'r') as f:
        config = json.load(f)

    assert 'selected_window_hwnds' in config
    assert config['selected_window_hwnds'] == [12345, 67890]
    assert 'selected_window_titles' not in config


@patch('window_utils.is_window_valid')
def test_hwnd_validation_all_valid(mock_is_valid):
    """Test HWND validation when all windows are valid."""
    mock_is_valid.return_value = True

    import window_utils
    hwnds = [12345, 67890, 11111]
    valid = [h for h in hwnds if window_utils.is_window_valid(h)]

    assert len(valid) == 3
    assert valid == hwnds


@patch('window_utils.is_window_valid')
def test_hwnd_validation_partial_valid(mock_is_valid):
    """Test HWND validation when some windows are closed."""
    def side_effect(hwnd):
        return hwnd in [12345, 11111]  # Only these are valid

    mock_is_valid.side_effect = side_effect

    import window_utils
    hwnds = [12345, 67890, 11111]
    valid = [h for h in hwnds if window_utils.is_window_valid(h)]

    assert len(valid) == 2
    assert valid == [12345, 11111]


@patch('window_utils.is_window_valid')
def test_hwnd_validation_none_valid(mock_is_valid):
    """Test HWND validation when all windows are closed."""
    mock_is_valid.return_value = False

    import window_utils
    hwnds = [12345, 67890, 11111]
    valid = [h for h in hwnds if window_utils.is_window_valid(h)]

    assert len(valid) == 0


def test_old_config_migration():
    """Test migration from old title-based config to HWND-based."""
    old_config = {
        'trigger_key': 'page up',
        'stop_key': 'page down',
        'countdown_seconds': 130,
        'auto_click_windows': True,
        'selected_window_titles': ['MapleRoyals', 'MapleRoyals']  # Old format
    }

    # Simulate migration
    if 'selected_window_titles' in old_config:
        del old_config['selected_window_titles']
        old_config['selected_window_hwnds'] = None

    assert 'selected_window_titles' not in old_config
    assert 'selected_window_hwnds' in old_config
    assert old_config['selected_window_hwnds'] is None
```

**Step 2: Run integration tests**

Run: `pytest tests/test_integration_hwnd.py -v`
Expected: All tests pass

**Step 3: Commit integration tests**

```bash
git add tests/test_integration_hwnd.py
git commit -m "test: add integration tests for HWND-based window selection"
```

---

## Task 9: Manual Testing and Cleanup

**Step 1: Manual end-to-end test**

Test checklist:
- [ ] Fresh install: `pip install -r requirements.txt`
- [ ] First run: Window selection with preview works
- [ ] Preview: Single number flashes correct window
- [ ] Selection: Comma-separated numbers selects correctly
- [ ] Config save: HWNDs saved to JSON
- [ ] Restart: HWNDs validated on startup
- [ ] Close window: Validation detects missing window
- [ ] Auto-click: Clicks correct windows by HWND
- [ ] Migration: Old config prompts re-selection

**Step 2: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

**Step 3: Update requirements if needed**

Verify `requirements.txt` has:
```
keyboard==0.13.5
pyinstaller==6.11.1
pygetwindow==0.0.9
pyautogui==0.9.54
pywin32==306
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup and verification for HWND feature"
```

---

## Task 10: Update Build Configuration

**Files:**
- Modify: `.github/workflows/build.yml` (if exists)

**Step 1: Verify pywin32 in build**

Check that GitHub Actions workflow includes pywin32 installation.
If `.github/workflows/build.yml` exists, verify dependencies are installed.

**Step 2: Test local build**

Run: `pyinstaller --onefile --console timer.py`
Expected: Builds successfully with pywin32 included

**Step 3: Test built executable**

Run: `dist/timer.exe`
Verify:
- Window selection works
- Preview flashing works
- Auto-click works

**Step 4: Commit build updates if needed**

```bash
git add .github/workflows/build.yml
git commit -m "ci: ensure pywin32 included in build"
```

---

## Summary

This plan implements HWND-based window identification with:

1. **Unique Identification**: Each window identified by HWND, not title
2. **Preview Mechanism**: Taskbar flashing to identify windows
3. **Validation**: Startup checks for closed windows
4. **Migration**: Automatic detection and prompting for old configs
5. **Testing**: Comprehensive unit and integration tests
6. **Documentation**: Updated CLAUDE.md and README.md

**Key Benefits:**
- Works with multiple identical window titles
- Reliable window identification
- User-friendly preview system
- Graceful handling of closed windows
- Backward compatible with old configs

**Testing Strategy:**
- Unit tests for window_utils module
- Integration tests for HWND validation
- Manual end-to-end testing
- Build verification

**Dependencies Added:**
- pywin32 (for FlashWindowEx and IsWindow APIs)

**Files Modified:**
- `timer.py` - Core logic updates
- `requirements.txt` - Add pywin32
- `CLAUDE.md`, `README.md` - Documentation

**Files Created:**
- `window_utils.py` - Window management utilities
- `tests/test_window_utils.py` - Unit tests
- `tests/test_integration_hwnd.py` - Integration tests
