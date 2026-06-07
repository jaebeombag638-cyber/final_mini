from pathlib import Path

import config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_project_scaffold_files_exist():
    expected_paths = [
        "core/__init__.py",
        "scenes/__init__.py",
        "assets",
        "tests",
        "config.py",
        "requirements.txt",
        "scenes/start_page.py",
        "scenes/intro.py",
        "scenes/stage1.py",
        "scenes/stage2.py",
        "scenes/stage3.py",
        "scenes/ending.py",
        "scenes/game_over.py",
    ]

    for relative_path in expected_paths:
        assert (PROJECT_ROOT / relative_path).exists(), relative_path


def test_config_defaults_match_step1_plan():
    assert config.SCREEN_WIDTH == 1280
    assert config.SCREEN_HEIGHT == 720
    assert config.FPS == 30
    assert config.CAMERA_INDEX == 0
    assert config.AUDIO_LIMIT_DB == 65.0
    assert config.FONT_PATH.as_posix() == "assets/fonts/MUNMAK_DALBANCHE.ttf"
    assert config.STAGE1_DURATION_SECONDS == 10.0
    assert config.STAGE2_TIME_LIMIT_SECONDS == 20.0
    assert config.STAGE3_TIME_LIMIT_SECONDS == 30.0


def test_requirements_include_runtime_and_test_dependencies():
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "pygame" in requirements
    assert "pytest" in requirements
