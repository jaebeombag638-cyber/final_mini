from scenes.stage3 import Stage3Scene


def test_stage3_scales_player_bbox_to_screen_coordinates():
    scene = Stage3Scene()
    frame = [[0 for _ in range(640)] for _ in range(480)]

    bbox = scene._scale_bbox_to_screen(
        bbox=(160, 120, 320, 360),
        frame=frame,
        mirror_display=False,
    )

    assert bbox == (320, 180, 640, 540)


def test_stage3_scales_mirrored_player_bbox_to_screen_coordinates():
    scene = Stage3Scene()
    frame = [[0 for _ in range(640)] for _ in range(480)]

    bbox = scene._scale_bbox_to_screen(
        bbox=(160, 120, 320, 360),
        frame=frame,
        mirror_display=True,
    )

    assert bbox == (640, 180, 960, 540)
