"""A placed sound a phone cannot play: audio_review.small_speaker_share reads where a file's energy lies."""
import math
import shutil
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audio_review as ar  # noqa: E402


def tone(path, partials, seconds=3.0, rate=48000):
    """A mono 16-bit file made of sine partials [(hz, amplitude)]."""
    n = int(seconds * rate)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b''.join(
            struct.pack('<h', int(32767 * sum(a * math.sin(2 * math.pi * hz * i / rate) for hz, a in partials)))
            for i in range(n)))


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg is not installed')
class SmallSpeakerShare(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_a_tone_on_55_and_110_hz_is_silence_on_a_phone(self):
        f = self.dir / 'low.wav'
        tone(f, [(55, 0.5), (110, 0.3)])
        share = ar.small_speaker_share(f)
        self.assertIsNotNone(share)
        self.assertLess(share, ar.SMALL_SPEAKER_SHARE)

    def test_the_same_tone_with_overtones_is_heard(self):
        f = self.dir / 'rich.wav'
        tone(f, [(55, 0.30), (110, 0.21), (220, 0.105), (330, 0.065), (440, 0.04)])
        self.assertGreater(ar.small_speaker_share(f), ar.SMALL_SPEAKER_SHARE)

    def test_a_file_without_sound_gives_no_figure(self):
        f = self.dir / 'empty.wav'
        tone(f, [(440, 0.0)], seconds=0.01)
        self.assertIsNone(ar.small_speaker_share(f))


if __name__ == '__main__':
    unittest.main()
