from core.camera import Camera


class FakeCapture:
    def __init__(self, opened=True, frame=None):
        self.opened = opened
        self.frame = frame
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        if self.frame is None:
            return False, None
        return True, self.frame.copy()

    def release(self):
        self.released = True


def test_open_uses_capture_factory_and_reports_open_state():
    created_indexes = []

    def capture_factory(camera_index):
        created_indexes.append(camera_index)
        return FakeCapture(opened=True)

    camera = Camera(camera_index=2, capture_factory=capture_factory)

    assert camera.open() is True
    assert camera.is_opened is True
    assert created_indexes == [2]


def test_read_frame_keeps_original_frame_direction():
    frame = [
        [[1, 0, 0], [2, 0, 0]],
        [[3, 0, 0], [4, 0, 0]],
    ]
    camera = Camera(capture_factory=lambda camera_index: FakeCapture(frame=frame))
    camera.open()

    camera_frame = camera.read_frame()

    assert camera_frame.is_fallback is False
    assert camera_frame.image == frame


def test_read_frame_returns_fallback_when_camera_is_not_opened():
    camera = Camera(capture_factory=lambda camera_index: FakeCapture(opened=False))

    camera_frame = camera.read_frame()

    assert camera_frame.is_fallback is True
    assert len(camera_frame.image) == 480
    assert len(camera_frame.image[0]) == 640
    assert len(camera_frame.image[0][0]) == 3


def test_release_closes_capture_once():
    capture = FakeCapture(opened=True)
    camera = Camera(capture_factory=lambda camera_index: capture)
    camera.open()

    camera.release()

    assert capture.released is True
    assert camera.is_opened is False


def test_to_surface_converts_bgr_frame_to_mirrored_pygame_surface(monkeypatch):
    converted = {}
    frame = [[[10, 20, 30], [40, 50, 60]]]

    class FakeSurfArray:
        @staticmethod
        def make_surface(rgb_image):
            converted["rgb_image"] = rgb_image
            return "surface"

    class FakePygame:
        surfarray = FakeSurfArray()

    camera = Camera()

    surface = camera.to_surface(frame, pygame_module=FakePygame)

    assert surface == "surface"
    assert converted["rgb_image"] == [[[60, 50, 40], [30, 20, 10]]]


def test_to_surface_can_skip_mirror_display(monkeypatch):
    converted = {}
    frame = [[[10, 20, 30], [40, 50, 60]]]

    class FakeSurfArray:
        @staticmethod
        def make_surface(rgb_image):
            converted["rgb_image"] = rgb_image
            return "surface"

    class FakePygame:
        surfarray = FakeSurfArray()

    camera = Camera(mirror_display=False)

    surface = camera.to_surface(frame, pygame_module=FakePygame)

    assert surface == "surface"
    assert converted["rgb_image"] == [[[30, 20, 10], [60, 50, 40]]]
