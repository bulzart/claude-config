"""The voice sheet (27 Nov 2026). No paid API calls, no Whisper.

No agent here hears, so a narration went undirected: a line was recorded once and nobody looked at how it was said.
The voice sheet draws what the voice really did over the words. An instrument is trusted only for what it has shown it
can tell, so these tests plant differences in a made voice (a word said higher, a word said louder, a word held, a
silence, a falling ending) and ask the sheet to find each one, and nothing else."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_static_core import cli, save                             # noqa: E402

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import av_tools as av                                              # noqa: E402

SR = av.SR
TEXTS = ['paper', 'travels', 'slowly', 'over', 'the', 'mountain', 'toward', 'home']


def voice(words, tail_s=0.4):
    """A made voice: each word a buzz of harmonics at its own pitch and level. words: [(text, seconds, hz, level,
    silence after, hz at its end or None)]. Returns (signal, word times)."""
    import numpy as np
    out, times, t = [np.zeros(int(0.3 * SR), dtype='float32')], [], 0.3
    for text, secs, hz, level, gap, end_hz in words:
        n = int(secs * SR)
        f = np.linspace(hz, end_hz or hz, n)
        phase = 2 * np.pi * np.cumsum(f) / SR
        y = sum(np.sin(k * phase) / k for k in range(1, 9)) * level
        ramp = int(0.01 * SR)
        y[:ramp] *= np.linspace(0, 1, ramp)
        y[-ramp:] *= np.linspace(1, 0, ramp)
        out.append(y.astype('float32'))
        times.append({'text': text, 'start_s': round(t, 3), 'end_s': round(t + secs, 3)})
        t += secs
        out.append(np.zeros(int(gap * SR), dtype='float32'))
        t += gap
    out.append(np.zeros(int(tail_s * SR), dtype='float32'))
    return np.concatenate(out), times


def even(**changed):
    """Eight even words (0.14 s a syllable at 120 Hz, 60 ms apart); changed: {word index: {field: value}}."""
    rows = []
    for i, text in enumerate(TEXTS):
        row = {'secs': 0.14 * av.syllables(text), 'hz': 120.0, 'level': 0.2, 'gap': 0.06, 'end_hz': None}
        row.update(changed.get(f'w{i}', {}))
        rows.append((text, row['secs'], row['hz'], row['level'], row['gap'], row['end_hz']))
    return voice(rows)


class VoiceSheetTests(unittest.TestCase):
    def stretch(self, y, words):
        f = av.voice_stretch(y, words, words[0]['start_s'], words[-1]['end_s'])
        f.pop('_draw')
        return f

    def test_syllables_tell_a_held_word_from_a_quick_one(self):
        for word, n in (('a', 1), ('the', 1), ('late', 1), ('workers', 2), ('drainage', 2), ('people', 2),
                        ('clay,', 1), ('Mother.', 2)):
            self.assertEqual(av.syllables(word), n, word)
        self.assertGreaterEqual(av.syllables('1975,'), 4)
        self.assertIn(av.syllables('archaeologists'), (4, 5))          # rough on purpose

    def test_an_even_delivery_has_no_word_pushed(self):
        y, words = even()
        f = self.stretch(y, words)
        self.assertEqual(f['standouts'], [], f['standouts'])
        self.assertEqual(f['pauses'], [])
        self.assertEqual(f['word_count'], 8)
        self.assertAlmostEqual(f['register_hz'], 120.0, delta=2.0)
        self.assertLess(f['pitch_range_st'], 1.0)

    def test_a_word_said_higher_is_found(self):
        y, words = even(w3={'hz': 170.0})                      # six semitones up
        f = self.stretch(y, words)
        self.assertEqual([s['word'] for s in f['standouts']], ['over'], f['standouts'])
        self.assertTrue(any('st above' in h for h in f['standouts'][0]['how']), f['standouts'])
        over = next(w for w in f['words'] if w['text'] == 'over')
        self.assertAlmostEqual(over['pitch_st'], 6.0, delta=0.6)

    def test_a_word_said_louder_is_found(self):
        y, words = even(w5={'level': 0.5})                     # eight decibels up
        f = self.stretch(y, words)
        self.assertEqual([s['word'] for s in f['standouts']], ['mountain'], f['standouts'])
        self.assertTrue(any('dB louder' in h for h in f['standouts'][0]['how']), f['standouts'])

    def test_a_word_held_is_found(self):
        y, words = even(w1={'secs': 0.9})                      # 'travels' (two syllables) held far past the others
        f = self.stretch(y, words)
        self.assertEqual(f['standouts'][0]['word'], 'travels', f['standouts'])
        self.assertTrue(any('held' in h for h in f['standouts'][0]['how']), f['standouts'])

    def test_a_silence_inside_the_line_is_found_with_its_length(self):
        y, words = even(w4={'gap': 0.5})
        f = self.stretch(y, words)
        self.assertEqual(len(f['pauses']), 1, f['pauses'])
        self.assertEqual(f['pauses'][0]['after'], 'the')
        self.assertAlmostEqual(f['pauses'][0]['length_s'], 0.5, delta=0.06)
        self.assertEqual(f['longest_pause_s'], f['pauses'][0]['length_s'])

    def test_a_falling_ending_reads_as_falling_and_a_level_one_as_level(self):
        y, words = even(w7={'secs': 0.5, 'end_hz': 75.0})
        self.assertEqual(self.stretch(y, words)['ending']['reads'], 'falls')
        y, words = even()
        self.assertEqual(self.stretch(y, words)['ending']['reads'], 'stays level')
        y, words = even(w7={'secs': 0.5, 'hz': 150.0, 'end_hz': 190.0})
        self.assertEqual(self.stretch(y, words)['ending']['reads'], 'rises')

    def test_the_zero_line_is_the_narrators_usual_when_it_is_given(self):
        y, words = even()
        f = av.voice_stretch(y, words, words[0]['start_s'], words[-1]['end_s'], ref_f0=100.0)
        f.pop('_draw')
        self.assertEqual(f['register_hz'], 100.0)
        self.assertAlmostEqual(f['words'][0]['pitch_st'], 3.2, delta=0.4)     # 120 Hz against 100 Hz
        self.assertAlmostEqual(f['own_middle_hz'], 120.0, delta=2.0)

    def test_the_sheet_is_drawn_and_a_long_stretch_wraps(self):
        from PIL import Image

        def size(path):
            with Image.open(path) as im:
                return im.width, im.height
        with tempfile.TemporaryDirectory() as tmp:
            y, words = even(w3={'hz': 170.0}, w4={'gap': 0.5})
            f = av.voice_sheet(y, words, words[0]['start_s'], words[-1]['end_s'], Path(tmp) / 'one.png', 'a take',
                               notes=['Asked of this moment: the word "over" carries it'], marks=[(0.3, 'L001')])
            self.assertNotIn('_draw', f)
            one = size(f['sheet'])
            self.assertEqual(one[0], 60 + int(av.VS_ROW_S * av.VS_PX_PER_S) + 24)
            with Image.open(f['sheet']) as im:
                small = im.convert('RGB').resize((64, 32))
                colours = {small.getpixel((x, yy)) for x in range(64) for yy in range(32)}
            self.assertGreater(len(colours), 4)                                       # something is drawn
            # a stretch of about 26 s takes three rows; one a little over a row is squeezed into it
            rows = [(t, 0.25, 120.0, 0.2, 0.15, None) for t in TEXTS * 8]            # 64 words, about 26 s
            y2, w2 = voice(rows)
            long = size(av.voice_sheet(y2, w2, w2[0]['start_s'], w2[-1]['end_s'], Path(tmp) / 'long.png', 'long')['sheet'])
            self.assertGreater(long[1], one[1] * 2)
            rows = [(t, 0.25, 120.0, 0.2, 0.15, None) for t in TEXTS * 3]            # 24 words, about 10 s
            y3, w3 = voice(rows)
            near = size(av.voice_sheet(y3, w3, w3[0]['start_s'], w3[-1]['end_s'], Path(tmp) / 'near.png', 'near')['sheet'])
            self.assertEqual(near[1], one[1] - 18)             # one row too: only the note line is missing
            both = size(av.stack_sheets([f['sheet'], str(Path(tmp) / 'near.png')], Path(tmp) / 'both.png'))
            self.assertEqual(both[1], one[1] + near[1] + 8)


class VoiceSheetCommandTests(unittest.TestCase):
    """The command reads a recording and writes only its own sheets."""

    def setUp(self):
        import soundfile as sf
        self._tmp = tempfile.TemporaryDirectory()
        self.td = Path(self._tmp.name)
        self.rd = self.td / 'run'
        save(self.rd / 'state.json', {'schema': 'static-youtube-longform-v1', 'run_id': 'voice-sheet-test'})
        self.sf = sf

    def tearDown(self):
        self._tmp.cleanup()

    def take(self, name, **changed):
        y, words = even(**changed)
        f = self.td / f'{name}.wav'
        self.sf.write(str(f), y, SR)
        save(f.with_suffix('.json'), {'segments': [{'start_s': words[0]['start_s'], 'end_s': words[-1]['end_s'],
                                                    'text': ' '.join(TEXTS), 'words': words}]})
        return f

    def test_two_takes_are_drawn_and_read_together(self):
        a, b = self.take('take-a'), self.take('take-b', w3={'hz': 170.0})
        out = self.td / 'sheets'
        res = cli('voice-sheet', '--run', self.rd, '--file', f'{a},{b}', '--out', out,
                  '--asked', 'the word "over" carries the line')
        self.assertTrue(res['ok'])
        self.assertEqual([Path(p).name for p in res['sheets']], ['take-a.png', 'take-b.png'])
        self.assertTrue(Path(res['takes_together']).is_file())
        facts = {s['name']: ' '.join(s['facts']) for s in res['summary']}
        self.assertIn('none stands clearly above', facts['take-a'])
        self.assertIn('"over"', facts['take-b'])
        index = json.loads((out / 'index.json').read_text(encoding='utf-8'))
        # read together, the takes share one zero line: the first take's own middle
        self.assertEqual({s['register_hz'] for s in index['sheets']}, {index['register_hz']})
        self.assertIn('never a hearing', (out / 'index.md').read_text(encoding='utf-8'))
        # nothing was written into the run, and nothing beside the takes
        self.assertEqual(sorted(p.name for p in self.rd.rglob('*') if p.is_file()), ['state.json'])
        self.assertEqual(sorted(p.name for p in self.td.glob('take-*')),
                         ['take-a.json', 'take-a.wav', 'take-b.json', 'take-b.wav'])

    def test_lines_of_a_measured_narration_are_drawn_beside_what_their_beat_asked(self):
        y, words = even(w4={'gap': 0.5}, w7={'secs': 0.5, 'end_hz': 75.0})
        folder = self.rd / '50-audio/video-01'
        folder.mkdir(parents=True)
        self.sf.write(str(folder / 'narration.wav'), y, SR)
        vd = self.rd / '40-plans/video-01'
        save(vd / 'script.json', {'lines': [{'id': 'L001', 'text': '[quietly] Paper travels slowly over the'},
                                            {'id': 'L002', 'text': 'mountain toward home'}]})
        save(vd / 'beat-map.json', {'beats': [{'id': 'B01', 'line_start': 1, 'line_end': 2,
                                               'narration_direction': 'Confide it; let "home" land low and final.'}]})
        save(vd / 'length-lock.json', {'language': 'en'})
        wt = [[w['start_s'], w['end_s']] for w in words]
        save(folder / 'line-times.json', {'complete': True, 'lines': [
            {'id': 'L001', 'index': 1, 'start_s': wt[0][0], 'end_s': wt[4][1], 'word_times': wt[:5]},
            {'id': 'L002', 'index': 2, 'start_s': wt[5][0], 'end_s': wt[7][1], 'word_times': wt[5:]}]})
        save(folder / 'manifest.json', {'chunks': []})
        res = cli('voice-sheet', '--run', self.rd, '--video', 1, '--lines', 'L002,L001-L002')
        self.assertTrue(res['ok'])
        self.assertEqual([Path(p).name for p in res['sheets']], ['L002.png', 'L001-L002.png'])
        by = {s['name']: s for s in res['summary']}
        self.assertEqual(by['L002']['said'], 'mountain toward home')
        self.assertIn('let "home" land low', by['L002']['asked'])
        self.assertIn('falls', ' '.join(by['L002']['facts']))
        self.assertIn('s after "the"', ' '.join(by['L001-L002']['facts']))      # the half-second silence
        index = json.loads((folder / 'voice-sheets/index.json').read_text(encoding='utf-8'))
        both = next(s for s in index['sheets'] if s.get('name') == 'L001-L002')
        self.assertEqual(both['cues'], ['[quietly]'])
        self.assertNotIn('quietly', both['said'])
        # a line the script does not have, and a narration not measured, are refused with the reason
        self.assertIn('--lines names lines', cli('voice-sheet', '--run', self.rd, '--video', 1, '--lines', 'L009',
                                                 expected=2)['error'])
        (folder / 'line-times.json').unlink()
        self.assertIn('not measured yet', cli('voice-sheet', '--run', self.rd, '--video', 1, '--lines', 'L001',
                                              expected=2)['error'])


if __name__ == '__main__':
    unittest.main()
