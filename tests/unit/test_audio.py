import numpy as np

from core.audio import AudioLevel, AudioMeter


class FakeInputStream:
    def __init__(self, callback=None, should_fail=False, **kwargs):
        self.callback = callback
        self.kwargs = kwargs
        self.should_fail = should_fail
        self.started = False
        self.closed = False

    def start(self):
        if self.should_fail:
            raise RuntimeError("마이크를 열 수 없습니다.")
        self.started = True

    def close(self):
        self.closed = True

    def push_samples(self, samples):
        self.callback(samples, len(samples), None, None)


def test_start_opens_sounddevice_input_stream():
    created_streams = []

    def stream_factory(**kwargs):
        stream = FakeInputStream(**kwargs)
        created_streams.append(stream)
        return stream

    audio = AudioMeter(stream_factory=stream_factory)

    assert audio.start() is True
    assert audio.is_opened is True
    assert created_streams[0].started is True
    assert created_streams[0].kwargs["channels"] == 1


def test_read_db_returns_relative_decibel_from_latest_samples():
    created_streams = []

    def stream_factory(**kwargs):
        stream = FakeInputStream(**kwargs)
        created_streams.append(stream)
        return stream

    audio = AudioMeter(stream_factory=stream_factory)
    audio.start()
    samples = np.array([[0.01], [-0.01], [0.01], [-0.01]], dtype=np.float32)

    stream = created_streams[0]
    stream.push_samples(samples)
    level = audio.read_db()

    assert level.is_fallback is False
    assert level.db == 60.0


def test_read_db_returns_zero_fallback_when_stream_is_not_available():
    audio = AudioMeter(
        stream_factory=lambda **kwargs: FakeInputStream(should_fail=True, **kwargs)
    )
    audio.start()

    level = audio.read_db()

    assert level == AudioLevel(db=0.0, is_fallback=True)


def test_is_over_threshold_compares_current_sound_level():
    created_streams = []

    def stream_factory(**kwargs):
        stream = FakeInputStream(**kwargs)
        created_streams.append(stream)
        return stream

    audio = AudioMeter(
        threshold_db=65.0,
        stream_factory=stream_factory,
    )
    audio.start()
    stream = created_streams[0]
    stream.push_samples(np.array([[0.1], [-0.1]], dtype=np.float32))

    assert audio.is_over_threshold() is True


def test_is_over_threshold_accepts_explicit_db_value():
    audio = AudioMeter(threshold_db=65.0)

    assert audio.is_over_threshold(64.9) is False
    assert audio.is_over_threshold(65.0) is True


def test_release_closes_stream_once():
    stream = FakeInputStream()
    audio = AudioMeter(stream_factory=lambda **kwargs: stream)
    audio.start()

    audio.release()

    assert stream.closed is True
    assert audio.is_opened is False
