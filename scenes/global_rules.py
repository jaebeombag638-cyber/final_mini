from core.game_state import GameState

"""실제 센서 값을 가져와서 `rules.py`에 넘기는 중간 연결 파일"""

def apply_global_rules(
    dt: float,
    now: float,
    game_state: GameState,
    services: dict[str, object],
) -> str | None:
    
    # services 딕셔너리(`main.py`에서 생성)에서 "rules" 값 가져오기
    rules = services.get("rules")
    if rules is None:
        return None

    face_detected = True
    audio_is_fallback = False
    frame = _read_camera_frame(services)  # 카메라에서 현재 프레임 기져오기

    audio_level = _read_audio_level(services)  # 마이크에서 현재 소리 크기 가져오기
    if audio_level is not None:
        game_state.update_audio_db(audio_level.db)
        audio_is_fallback = audio_level.is_fallback

    # 카메라 프레임으로부터 얼굴, 입 좌표(양쪽 입꼬리, 위아래 입술) 추적    
    face_result = _track_face(services, frame, now)
    if face_result is not None:
        baseline = game_state.baseline_mouth_landmarks
        if baseline is None and face_result.face_detected:
            baseline = face_result.mouth_landmarks
        game_state.update_mouth_landmarks(
            baseline=baseline,
            current=face_result.mouth_landmarks,
        )
        face_detected = face_result.face_detected
    
    # `rules.py`로 넘김 ; 위반이면 "game_over", 아니면 None 반환
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
