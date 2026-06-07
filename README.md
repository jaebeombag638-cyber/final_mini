# Your Face 실행 가이드

이 문서는 다른 사용자가 현재 구현된 `main.py`를 실행해 보기 위한 단계별 안내서입니다.  
Python 3.10 기준으로 작성되어 있습니다.

## 1. 준비물

먼저 아래 항목이 준비되어 있어야 합니다.

- Python 3.10 실행 환경
- 웹캠
- 마이크
- 인터넷 연결

## 2. 프로젝트 폴더로 이동

터미널을 열고 프로젝트 폴더로 이동합니다.

```powershell
cd C:\your_face
```

## 3. 의존성 설치

프로젝트에서 사용하는 패키지를 설치합니다.

```powershell
python -m pip install -r requirements.txt
```

## 4. 게임 실행

아래 명령으로 현재 구현된 메인 루프를 실행합니다.

```powershell
python main.py
```

## 5. 카메라만 따로 확인하기

카메라 입력만 확인하려면 아래 스크립트를 실행합니다.

```powershell
python scripts\camera_preview.py
```

카메라가 없거나 열리지 않으면 fallback 화면이 사용됩니다.

## 6. 음성 인식만 따로 확인하기

Whisper 음성 인식만 간단히 확인하려면 아래 스크립트를 실행합니다.

```powershell
python scripts\speech_preview.py
```

이 스크립트는 5초 동안 마이크 입력을 받은 뒤 변환 텍스트, 목표 문장, 유사도, 통과 여부를 출력합니다.

## 7. YOLO 감지만 따로 확인하기

YOLO bbox 감지만 확인하려면 아래 스크립트를 실행합니다.

```powershell
python scripts\yolo_bbox_preview.py
```

웹캠 화면에서 사람 bbox가 정상적으로 잡히는지 확인할 수 있습니다.



