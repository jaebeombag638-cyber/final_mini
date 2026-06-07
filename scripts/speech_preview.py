import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.speech import SpeechRecognizer


_RECORD_SECONDS = 5.0


def main() -> None:
    recognizer = SpeechRecognizer()
    try:
        print(f"{_RECORD_SECONDS:.0f}초 동안 말하세요.")
        result = recognizer.recognize(duration_seconds=_RECORD_SECONDS)

        if result.is_fallback:
            print(f"음성 인식 실패: {result.error_message}")
            return

        print(f"목표 문장: {result.target_text}")
        print(f"변환 텍스트: {result.recognized_text}")
        print(f"유사도: {result.similarity:.4f}")
        print(f"통과 여부: {result.passed}")
    finally:
        recognizer.release()


if __name__ == "__main__":
    main()
