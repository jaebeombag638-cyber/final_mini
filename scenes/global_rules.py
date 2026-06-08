from core.game_state import GameState


def apply_global_rules(
    dt: float,
    now: float,
    game_state: GameState,
    services: dict[str, object],
) -> str | None:
    rules = services.get("rules")
    if rules is None:
        return None

    face_detected = True
    audio_is_fallback = False
    frame = _read_camera_frame(services)

    audio_level = _read_audio_level(services)
    if audio_level is not None:
        game_state.update_audio_db(audio_level.db)
        audio_is_fallback = audio_level.is_fallback

    face_result = _track_face(services, frame, now)
    if face_result is not None:
        face_tracker = services.get("face_tracker")
        baseline = getattr(face_tracker, "baseline_mouth_landmarks", None)
        game_state.update_mouth_landmarks(
            baseline=baseline or game_state.baseline_mouth_landmarks,
            current=face_result.mouth_landmarks,
        )
        face_detected = face_result.face_detected

    return rules.apply_to_game_state(
        dt=dt,
        game_state=game_state,
        face_detected=face_detected,
        audio_is_fallback=audio_is_fallback,
    )


def _read_camera_frame(services: dict[str, object]):
    camera = services.get("camera")
    if camera is None:
        return None

    if hasattr(camera, "open"):
        camera.open()
    if not hasattr(camera, "read_frame"):
        return None

    return camera.read_frame()


def _read_audio_level(services: dict[str, object]):
    audio = services.get("audio")
    if audio is None:
        return None

    if hasattr(audio, "start"):
        audio.start()
    if not hasattr(audio, "read_db"):
        return None

    return audio.read_db()


def _track_face(services: dict[str, object], frame, now: float):
    face_tracker = services.get("face_tracker")
    if face_tracker is None or frame is None or not hasattr(face_tracker, "track"):
        return None

    return face_tracker.track(frame.image, now)
