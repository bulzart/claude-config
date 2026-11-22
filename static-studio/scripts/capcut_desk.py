#!/usr/bin/env python3
"""capcut_desk.py - drive CapCut's own window on Windows, so the agent can export a project and look at it (manual 09).

Six abilities, each a command that prints one JSON object on its last line (exit 0 = done, 1 = failed, 2 = refused):
  shot     [--out PNG] [--region X,Y,W,H] [--scale S]   the screen (or a region) as a PNG to open and look at. The process
                                                       is DPI-aware: a pixel of the shot is a pixel of the screen. A shot
                                                       scaled down by S maps back with x / S + region x (the answer says so).
  click    X Y [--double] [--right]                     move the cursor there and press. Refused unless CapCut is in front
                                                       AND the window on top at that point is CapCut's.
  key      COMBO                                        e.g. ctrl+a, enter, esc, tab, alt+f4 is refused. Refused unless
                                                       CapCut is in front.
  type     TEXT                                         typed character by character as Unicode (never the clipboard).
                                                       Refused unless CapCut is in front.
  windows                                               the visible windows: title, rectangle, process, which is in front.
  focus                                                 bring CapCut's main window to the front (and say if it worked).
  app start|quit|status                                 start CapCut and wait for its window; quit = the normal close
                                                       message (WM_CLOSE) to its windows, repeated until it is gone.
                                                       CapCut saves its project itself. Never killed. A CapCut already
                                                       open that this tool did not start (the user's, another
                                                       session's) is refused: never taken over, never closed.
  export-path --set DIR | --restore | --show            where CapCut writes its exports: HKCU\\Software\\Bytedance\\CapCut\\
                                                       Modules\\Export, value ExportPath, read when CapCut starts. --set
                                                       keeps the current value first; --restore writes it back. Both only
                                                       while CapCut is closed.

The loop for an export is the agent's: one small action, then a shot to look at, nothing clicked from memory (manual 09).
CapCut's windows are found by their process (CapCut.exe), never by title: a terminal tab can carry the word too.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STUDIO = Path(__file__).resolve().parent.parent
EXPORT_KEY = os.environ.get('STUDIO_CAPCUT_EXPORT_KEY', r'Software\Bytedance\CapCut\Modules\Export')
SAVED = Path(os.environ.get('STUDIO_CAPCUT_EXPORT_SAVED', str(STUDIO / 'runs' / '.capcut-export-path.json')))
CAPCUT_EXE = Path(os.environ.get('LOCALAPPDATA', '')) / 'CapCut' / 'Apps' / 'CapCut.exe'
PROCESS = 'capcut.exe'

VK = {'ctrl': 0x11, 'control': 0x11, 'shift': 0x10, 'alt': 0x12, 'win': 0x5B, 'enter': 0x0D, 'return': 0x0D,
      'esc': 0x1B, 'escape': 0x1B, 'tab': 0x09, 'space': 0x20, 'backspace': 0x08, 'delete': 0x2E, 'del': 0x2E,
      'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22, 'left': 0x25, 'up': 0x26, 'right': 0x27,
      'down': 0x28, 'insert': 0x2D}
VK.update({f'f{i}': 0x6F + i for i in range(1, 13)})
VK.update({chr(c): c for c in range(0x41, 0x5B)})
VK.update({chr(c).lower(): c for c in range(0x41, 0x5B)})
VK.update({str(d): 0x30 + d for d in range(10)})
REFUSED_COMBOS = {('alt', 'f4'), ('ctrl', 'w')}          # closing goes through `app quit` (WM_CLOSE), never a keystroke


def out(obj, code=0):
    data = (json.dumps(obj, ensure_ascii=False) + '\n').encode('utf-8')   # window titles carry any character
    sys.stdout.flush()
    sys.stdout.buffer.write(data)
    sys.stdout.flush()
    sys.exit(code)


def parse_combo(text):
    """'ctrl+shift+s' -> (modifier VKs, key VK), names normalised; raises ValueError for an unknown key."""
    parts = [p.strip().lower() for p in str(text).split('+') if p.strip()]
    if not parts:
        raise ValueError('empty key combo')
    if tuple(parts) in REFUSED_COMBOS:
        raise ValueError(f'{text}: closing CapCut goes through `app quit` (it saves the project), never a keystroke')
    codes = []
    for p in parts:
        if p not in VK:
            raise ValueError(f'unknown key {p!r} in {text!r}')
        codes.append(VK[p])
    return codes[:-1], codes[-1]


def map_from_shot(x, y, scale=1.0, region=(0, 0)):
    """A point read off a shot (scaled by `scale`, of a region starting at `region`) -> the screen point to click."""
    return round(x / float(scale) + region[0]), round(y / float(scale) + region[1])


# --------------------------------------------------------------------------- Windows (user32 / kernel32 through ctypes)
if sys.platform == 'win32':
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    ULONG_PTR = ctypes.c_size_t

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [('wVk', wt.WORD), ('wScan', wt.WORD), ('dwFlags', wt.DWORD), ('time', wt.DWORD), ('dwExtraInfo', ULONG_PTR)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [('dx', wt.LONG), ('dy', wt.LONG), ('mouseData', wt.DWORD), ('dwFlags', wt.DWORD), ('time', wt.DWORD),
                    ('dwExtraInfo', ULONG_PTR)]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [('uMsg', wt.DWORD), ('wParamL', wt.WORD), ('wParamH', wt.WORD)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT), ('hi', HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [('type', wt.DWORD), ('u', _INPUTUNION)]

    INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
    KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = 0x0002, 0x0004
    MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = 0x0002, 0x0004, 0x0008, 0x0010
    WM_CLOSE, SW_RESTORE = 0x0010, 9
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def dpi_aware():
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:  # noqa: BLE001
            try:
                user32.SetProcessDPIAware()
            except Exception:  # noqa: BLE001
                pass

    def _send(inputs):
        arr = (INPUT * len(inputs))(*inputs)
        n = user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))
        if n != len(inputs):
            raise OSError(f'SendInput sent {n} of {len(inputs)} events (error {ctypes.get_last_error()})')

    def _key(vk, up=False):
        return INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP if up else 0,
                                                                     time=0, dwExtraInfo=0)))

    def _uni(ch, up=False):
        return INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=KEYBDINPUT(wVk=0, wScan=ord(ch),
                                                                     dwFlags=KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0),
                                                                     time=0, dwExtraInfo=0)))

    def _mouse(flags):
        return INPUT(type=INPUT_MOUSE, u=_INPUTUNION(mi=MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=flags, time=0, dwExtraInfo=0)))

    def _process_name(pid):
        h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return ''
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wt.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return Path(buf.value).name
            return ''
        finally:
            kernel32.CloseHandle(h)

    def list_windows():
        rows = []
        fg = user32.GetForegroundWindow()
        WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

        def cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            r = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            if r.right - r.left <= 1 or r.bottom - r.top <= 1:
                return True
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            rows.append({'hwnd': int(hwnd), 'title': buf.value, 'process': _process_name(pid.value), 'pid': int(pid.value),
                         'rect': [r.left, r.top, r.right - r.left, r.bottom - r.top], 'front': int(hwnd) == int(fg or 0)})
            return True
        user32.EnumWindows(WNDENUMPROC(cb), 0)
        return rows

    def capcut_windows():
        return [w for w in list_windows() if w['process'].lower() == PROCESS]

    def capcut_in_front():
        fg = user32.GetForegroundWindow()
        if not fg:
            return False
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
        return _process_name(pid.value).lower() == PROCESS

    def capcut_running():
        cp = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {PROCESS}', '/NH', '/FO', 'CSV'], capture_output=True, text=True)
        return PROCESS in (cp.stdout or '').lower()

    class POINT(ctypes.Structure):
        _fields_ = [('x', wt.LONG), ('y', wt.LONG)]

    user32.WindowFromPoint.argtypes = [POINT]
    user32.WindowFromPoint.restype = wt.HWND
    user32.GetAncestor.argtypes = [wt.HWND, wt.UINT]
    user32.GetAncestor.restype = wt.HWND

    def process_at(x, y):
        """The process whose window is on top at this screen point (what a click there would reach)."""
        h = user32.WindowFromPoint(POINT(int(x), int(y)))
        if not h:
            return ''
        root = user32.GetAncestor(h, 2) or h     # GA_ROOT: the top-level window
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(root, ctypes.byref(pid))
        return _process_name(pid.value)


def need_front(allow_any=False):
    if allow_any:
        return
    if not capcut_in_front():
        fg = next((w for w in list_windows() if w['front']), None)
        out({'ok': False, 'refused': 'CapCut is not the window in front: run `focus`, take a shot, then act',
             'front': fg}, 2)


def need_capcut_at(x, y, allow_any=False):
    """A click lands on whatever window is on top at that point: refused unless that is CapCut's."""
    if allow_any:
        return
    owner = process_at(x, y)
    if owner.lower() != PROCESS:
        out({'ok': False, 'refused': f'the window at ({x}, {y}) belongs to {owner or "nothing"}, not CapCut: take a shot '
                                     'and read the point again', 'point': [x, y]}, 2)


STARTED = Path(os.environ.get('STUDIO_CAPCUT_DESK_STATE', str(STUDIO / 'runs' / '.desk' / 'started.json')))


def started_pids():
    try:
        return set(json.loads(STARTED.read_text(encoding='utf-8')).get('pids') or [])
    except (OSError, ValueError):
        return set()


def mine_running():
    """CapCut windows that belong to a CapCut this tool started (never the user's own, never another session's)."""
    pids = started_pids()
    return [w for w in capcut_windows() if w['pid'] in pids]


def cmd_shot(a):
    from PIL import ImageGrab
    region = [int(v) for v in a.region.split(',')] if a.region else None
    bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3]) if region else None
    img = ImageGrab.grab(bbox=bbox, all_screens=True)
    scale = float(a.scale or 1.0)
    if scale != 1.0:
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))))
    path = Path(a.out or (STUDIO / 'runs' / '.desk' / f'shot-{datetime.now().strftime("%H%M%S")}.png'))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    out({'ok': True, 'file': str(path), 'size': [img.width, img.height], 'scale': scale,
         'region': region or [0, 0, None, None], 'capcut_in_front': capcut_in_front(),
         'map': f'screen x = shot x / {scale:g} + {region[0] if region else 0}, screen y = shot y / {scale:g} + '
                f'{region[1] if region else 0}'})


def cmd_click(a):
    need_front(a.any_window)
    x, y = int(a.x), int(a.y)
    need_capcut_at(x, y, a.any_window)
    user32.SetCursorPos(x, y)
    time.sleep(0.05)
    down, up = (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP) if a.right else (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP)
    for i in range(2 if a.double else 1):
        _send([_mouse(down), _mouse(up)])
        if a.double and i == 0:
            time.sleep(0.08)
    out({'ok': True, 'clicked': [x, y], 'button': 'right' if a.right else 'left', 'double': bool(a.double)})


def cmd_key(a):
    need_front(a.any_window)
    try:
        mods, key = parse_combo(a.combo)
    except ValueError as e:
        out({'ok': False, 'refused': str(e)}, 2)
    seq = [_key(m) for m in mods] + [_key(key), _key(key, True)] + [_key(m, True) for m in reversed(mods)]
    _send(seq)
    out({'ok': True, 'pressed': a.combo})


def cmd_type(a):
    need_front(a.any_window)
    for ch in str(a.text):
        _send([_uni(ch), _uni(ch, True)])
        time.sleep(0.01)
    out({'ok': True, 'typed_characters': len(str(a.text))})


def cmd_windows(a):
    rows = list_windows()
    if a.capcut:
        rows = [w for w in rows if w['process'].lower() == PROCESS]
    out({'ok': True, 'windows': rows, 'capcut_in_front': capcut_in_front()})


def main_window():
    ws = capcut_windows()
    return max(ws, key=lambda w: w['rect'][2] * w['rect'][3]) if ws else None


def cmd_focus(a):
    w = main_window()
    if not w:
        out({'ok': False, 'error': 'no CapCut window'}, 1)
    hwnd = wt.HWND(w['hwnd'])
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    # Windows lets a process take the foreground right after a key event of its own: a bare Alt press and release
    _send([_key(VK['alt']), _key(VK['alt'], True)])
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    out({'ok': capcut_in_front(), 'window': w, 'capcut_in_front': capcut_in_front()}, 0 if capcut_in_front() else 1)


def cmd_app(a):
    if a.action == 'status':
        out({'ok': True, 'running': capcut_running(), 'windows': capcut_windows(), 'capcut_in_front': capcut_in_front()})
    if a.action == 'start':
        if capcut_running():
            if mine_running():
                out({'ok': True, 'already_running': True, 'started_by_this_tool': True, 'windows': capcut_windows()})
            out({'ok': False, 'refused': 'CapCut is already open, and not by this tool: the user (or another session) is '
                                         'using it. Never take it over or close it: wait until it is closed, or ask.',
                 'windows': capcut_windows()}, 2)
        if not CAPCUT_EXE.is_file():
            out({'ok': False, 'error': f'no CapCut at {CAPCUT_EXE}'}, 1)
        flags = 0x00000008 | 0x00000200          # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP: CapCut outlives this command
        proc = subprocess.Popen([str(CAPCUT_EXE)], creationflags=flags, close_fds=True, cwd=str(CAPCUT_EXE.parent))
        t0 = time.time()
        while time.time() - t0 < float(a.timeout):
            w = main_window()
            if w and w['rect'][2] > 400:
                time.sleep(2.0)                   # let it finish drawing before the first shot
                pids = sorted({int(proc.pid)} | {x['pid'] for x in capcut_windows()})
                STARTED.parent.mkdir(parents=True, exist_ok=True)
                STARTED.write_text(json.dumps({'pids': pids, 'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}),
                                   encoding='utf-8')
                out({'ok': True, 'started_s': round(time.time() - t0, 1), 'window': main_window(), 'pids': pids})
            time.sleep(1.0)
        out({'ok': False, 'error': f'no CapCut window after {a.timeout} s', 'running': capcut_running()}, 1)
    if a.action == 'quit':
        if not capcut_running():
            STARTED.unlink(missing_ok=True)
            out({'ok': True, 'running': False, 'note': 'CapCut was not running'})
        if not mine_running():
            out({'ok': False, 'refused': 'the open CapCut was not started by this tool: it is the user\'s (or another '
                                         'session\'s). Never close it.', 'windows': capcut_windows()}, 2)
        rounds = []
        t0 = time.time()
        while capcut_running() and time.time() - t0 < float(a.timeout):
            ws = capcut_windows()
            for w in ws:
                user32.PostMessageW(wt.HWND(w['hwnd']), WM_CLOSE, 0, 0)
            rounds.append([w['title'] for w in ws])
            time.sleep(3.0)
        running = capcut_running()
        if not running:
            STARTED.unlink(missing_ok=True)
        out({'ok': not running, 'close_rounds': rounds, 'running': running,
             'note': 'closed with WM_CLOSE (CapCut saves its project itself); never killed' if not running else
                     'still running: a dialog may be waiting; take a shot and answer it, then quit again'}, 0 if not running else 1)


def _reg(write=False):
    import winreg
    access = winreg.KEY_READ | (winreg.KEY_WRITE if write else 0)
    return winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, EXPORT_KEY, 0, access) if write else \
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, EXPORT_KEY, 0, access)


def read_export_path():
    import winreg
    try:
        with _reg() as k:
            return winreg.QueryValueEx(k, 'ExportPath')[0]
    except FileNotFoundError:
        return None


def write_export_path(value):
    import winreg
    with _reg(write=True) as k:
        winreg.SetValueEx(k, 'ExportPath', 0, winreg.REG_SZ, str(value))


def cmd_export_path(a):
    if a.show:
        out({'ok': True, 'export_path': read_export_path(), 'saved': json.loads(SAVED.read_text(encoding='utf-8')) if SAVED.is_file() else None})
    if capcut_running():
        out({'ok': False, 'refused': 'CapCut is running: it reads the export folder when it starts and may write it when it '
                                     'quits. Quit it first (`app quit`).'}, 2)
    if a.set:
        target = Path(a.set).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        if not SAVED.is_file():                  # keep the user's own value once, even across repeated --set
            SAVED.parent.mkdir(parents=True, exist_ok=True)
            SAVED.write_text(json.dumps({'saved': read_export_path(), 'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}),
                             encoding='utf-8')
        write_export_path(target.as_posix())
        out({'ok': True, 'export_path': read_export_path(), 'kept_to_restore': json.loads(SAVED.read_text(encoding='utf-8'))['saved']})
    if a.restore:
        if not SAVED.is_file():
            out({'ok': True, 'restored': None, 'note': 'nothing kept: the export folder was not changed by this tool'})
        kept = json.loads(SAVED.read_text(encoding='utf-8')).get('saved')
        if kept is not None:
            write_export_path(kept)
        SAVED.unlink()
        out({'ok': True, 'restored': kept, 'export_path': read_export_path()})
    out({'ok': False, 'error': 'use --set DIR, --restore or --show'}, 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('shot'); p.add_argument('--out'); p.add_argument('--region'); p.add_argument('--scale', type=float)
    p.set_defaults(fn=cmd_shot)
    p = sub.add_parser('click'); p.add_argument('x'); p.add_argument('y'); p.add_argument('--double', action='store_true')
    p.add_argument('--right', action='store_true'); p.add_argument('--any-window', action='store_true'); p.set_defaults(fn=cmd_click)
    p = sub.add_parser('key'); p.add_argument('combo'); p.add_argument('--any-window', action='store_true'); p.set_defaults(fn=cmd_key)
    p = sub.add_parser('type'); p.add_argument('text'); p.add_argument('--any-window', action='store_true'); p.set_defaults(fn=cmd_type)
    p = sub.add_parser('windows'); p.add_argument('--capcut', action='store_true'); p.set_defaults(fn=cmd_windows)
    p = sub.add_parser('focus'); p.set_defaults(fn=cmd_focus)
    p = sub.add_parser('app'); p.add_argument('action', choices=['start', 'quit', 'status'])
    p.add_argument('--timeout', default='90'); p.set_defaults(fn=cmd_app)
    p = sub.add_parser('export-path'); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--set'); g.add_argument('--restore', action='store_true'); g.add_argument('--show', action='store_true')
    p.set_defaults(fn=cmd_export_path)
    a = ap.parse_args()
    if sys.platform != 'win32':
        out({'ok': False, 'error': 'Windows only'}, 2)
    dpi_aware()
    a.fn(a)


if __name__ == '__main__':
    main()
