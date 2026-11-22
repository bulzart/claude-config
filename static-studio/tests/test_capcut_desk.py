"""capcut_desk.py: the hands for exporting a CapCut project from CapCut's own window (manual 09, "Export and look").
No test here moves the mouse, presses a key, starts CapCut or writes the registry: every Windows call is a stand-in."""
import argparse
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parent.parent / 'scripts' / 'capcut_desk.py'


def load():
    spec = importlib.util.spec_from_file_location('capcut_desk_under_test', TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(fn, **kw):
    """Run one command function; returns (exit code, its JSON answer)."""
    buf = io.BytesIO()
    fake = io.TextIOWrapper(buf, encoding='utf-8')
    with mock.patch.object(sys, 'stdout', fake):
        try:
            fn(argparse.Namespace(**kw))
            code = None
        except SystemExit as e:
            code = e.code
        fake.flush()
    text = buf.getvalue().decode('utf-8').strip().splitlines()
    return code, (json.loads(text[-1]) if text else None)


class ComboAndMapTests(unittest.TestCase):
    def test_key_combos_are_parsed_and_closing_keystrokes_refused(self):
        m = load()
        self.assertEqual(m.parse_combo('ctrl+a'), ([0x11], 0x41))
        self.assertEqual(m.parse_combo('Ctrl+Shift+S'), ([0x11, 0x10], 0x53))
        self.assertEqual(m.parse_combo('enter'), ([], 0x0D))
        for bad in ('alt+f4', 'ctrl+w', 'ctrl+nope', ''):
            with self.assertRaises(ValueError):
                m.parse_combo(bad)

    def test_a_point_read_off_a_scaled_region_shot_maps_back_to_the_screen(self):
        m = load()
        self.assertEqual(m.map_from_shot(100, 50, 0.5, (560, 140)), (760, 240))
        self.assertEqual(m.map_from_shot(1000, 300), (1000, 300))


@unittest.skipUnless(sys.platform == 'win32', 'Windows only')
class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.m.SAVED = Path(self.td.name) / 'export-path.json'
        self.m.STARTED = Path(self.td.name) / 'started.json'
        self.reg = {'value': 'C:/Users/someone/Documents/output'}
        self.m.read_export_path = lambda: self.reg['value']
        self.m.write_export_path = lambda v: self.reg.__setitem__('value', str(v))

    def test_export_folder_set_keeps_the_users_value_once_and_restore_puts_it_back(self):
        m = self.m
        with mock.patch.object(m, 'capcut_running', return_value=False):
            a = Path(self.td.name) / 'run-a' / 'export'
            b = Path(self.td.name) / 'run-b' / 'export'
            code, ans = run(m.cmd_export_path, show=False, set=str(a), restore=False)
            self.assertEqual((code, ans['kept_to_restore']), (0, 'C:/Users/someone/Documents/output'))
            self.assertEqual(self.reg['value'], a.resolve().as_posix())
            run(m.cmd_export_path, show=False, set=str(b), restore=False)       # a second set never loses the user's value
            code, ans = run(m.cmd_export_path, show=False, set=None, restore=True)
            self.assertEqual((code, ans['restored']), (0, 'C:/Users/someone/Documents/output'))
            self.assertEqual(self.reg['value'], 'C:/Users/someone/Documents/output')
            self.assertFalse(m.SAVED.exists())

    def test_export_folder_is_never_changed_while_capcut_runs(self):
        m = self.m
        with mock.patch.object(m, 'capcut_running', return_value=True):
            code, ans = run(m.cmd_export_path, show=False, set=self.td.name, restore=False)
        self.assertEqual(code, 2)
        self.assertEqual(self.reg['value'], 'C:/Users/someone/Documents/output')

    def test_a_capcut_this_tool_did_not_start_is_never_taken_over_or_closed(self):
        m = self.m
        users = [{'hwnd': 1, 'title': 'CapCut', 'process': 'CapCut.exe', 'pid': 4242, 'rect': [0, 0, 1440, 960], 'front': True}]
        with mock.patch.object(m, 'capcut_running', return_value=True), \
                mock.patch.object(m, 'capcut_windows', return_value=users), \
                mock.patch.object(m, 'user32') as u32, \
                mock.patch.object(m.subprocess, 'Popen', side_effect=AssertionError('must not start CapCut')):
            code, ans = run(m.cmd_app, action='start', timeout='5')
            self.assertEqual(code, 2)
            code, ans = run(m.cmd_app, action='quit', timeout='5')
            self.assertEqual(code, 2)
            u32.PostMessageW.assert_not_called()
            # once this tool started it (its pids on record), quitting it is allowed
            m.STARTED.write_text(json.dumps({'pids': [4242]}), encoding='utf-8')
            self.assertEqual([w['pid'] for w in m.mine_running()], [4242])

    def test_a_click_is_refused_where_another_window_is_on_top(self):
        m = self.m
        with mock.patch.object(m, 'capcut_in_front', return_value=True), \
                mock.patch.object(m, 'process_at', return_value='WindowsTerminal.exe'), \
                mock.patch.object(m, '_send', side_effect=AssertionError('must not click')), \
                mock.patch.object(m, 'user32') as u32:
            code, ans = run(m.cmd_click, x='960', y='540', double=False, right=False, any_window=False)
        self.assertEqual(code, 2)
        u32.SetCursorPos.assert_not_called()
        with mock.patch.object(m, 'capcut_in_front', return_value=True), \
                mock.patch.object(m, 'process_at', return_value='CapCut.exe'), \
                mock.patch.object(m, '_send') as send, mock.patch.object(m, 'user32'):
            code, ans = run(m.cmd_click, x='960', y='540', double=False, right=False, any_window=False)
        self.assertEqual((code, ans['clicked']), (0, [960, 540]))
        self.assertEqual(send.call_count, 1)

    def test_the_screen_is_shared_never_pulled_from_someone_using_it_and_never_captured(self):
        m = self.m
        other = {'hwnd': 1, 'title': 'my private letter.docx - Word', 'process': 'WINWORD.EXE', 'pid': 7,
                 'rect': [0, 0, 1920, 1080], 'front': True}
        mine = {'hwnd': 2, 'title': 'CapCut', 'process': 'CapCut.exe', 'pid': 9, 'rect': [0, 0, 1920, 1080], 'front': False}
        with mock.patch.object(m, 'capcut_in_front', return_value=False), \
                mock.patch.object(m, 'capcut_windows', return_value=[mine]), \
                mock.patch.object(m, 'idle_seconds', return_value=4.0), \
                mock.patch.object(m, 'user32') as u32, mock.patch.object(m, '_send', side_effect=AssertionError('no keys')):
            code, ans = run(m.cmd_focus, when_idle=120)
        self.assertEqual(code, 2)                                   # someone typed 4 s ago: CapCut stays behind
        u32.SetForegroundWindow.assert_not_called()
        with mock.patch.object(m, 'capcut_in_front', return_value=False), \
                mock.patch.object(m, 'list_windows', return_value=[other, mine]):
            code, ans = run(m.cmd_shot, out=None, region=None, scale=None, any_window=False)
            self.assertEqual((code, ans['front_process']), (2, 'WINWORD.EXE'))   # no shot of the user's screen
            code, ans = run(m.cmd_windows, capcut=False)
        titles = {w['process']: w['title'] for w in ans['windows']}
        self.assertEqual(titles, {'WINWORD.EXE': '', 'CapCut.exe': 'CapCut'})   # another program's title stays private
        with mock.patch.object(m, 'idle_seconds', side_effect=[30.0, 200.0]), mock.patch.object(m.time, 'sleep'):
            code, ans = run(m.cmd_idle, wait=600, at_least=120)
        self.assertEqual((code, ans['idle_s']), (0, 200.0))

    def test_keys_and_typing_are_refused_unless_capcut_is_in_front(self):
        m = self.m
        with mock.patch.object(m, 'capcut_in_front', return_value=False), \
                mock.patch.object(m, 'list_windows', return_value=[]), \
                mock.patch.object(m, '_send', side_effect=AssertionError('must not type')):
            self.assertEqual(run(m.cmd_key, combo='ctrl+a', any_window=False)[0], 2)
            self.assertEqual(run(m.cmd_type, text='hello', any_window=False)[0], 2)


if __name__ == '__main__':
    unittest.main()
