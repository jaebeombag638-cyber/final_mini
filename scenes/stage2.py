import pygame
import config
import numpy as np
import sys
from core.audio import AudioMeter
from core.scene import Scene
from core.rules import SOUND_LIMIT_REASON
from core.speech import SpeechRecognizer
from scenes.global_rules import apply_global_rules

_FAIL_RESULT_DISPLAY_SECONDS = 5.0
_TARGET_TEXT = "얄리얄리 얄라셩 얄라리 얄라"


class Stage2Scene(Scene):
    def __init__(self) -> None:
        self.stream = None
        self.recognizer = SpeechRecognizer()
        self.audio_meter = AudioMeter(sample_rate=48000, channels=2)
        self._reset()

    def _reset(self) -> None:
        # Stage 1 스타일 타이머 연동
        self._elapsed: float = 0.0
        self.intro_duration: float = 1.0    
        self.intro_done: bool = False       
        
        # 단계 제어 (총 10초 내에 돌파해야 함)
        self.progress: float = 0.0          
        self.time_elapsed: float = 0.0    
        self.time_limit: float = 10.0 
        
        # 오디오 및 AI 상태 제어
        self.audio_status: str = "RECORDING" 
        self.recorded_chunks = []           
        self.current_live_db: float = 0.0   
        self.user_spoken_text: str = ""     
        self.match_ratio_percent: float = 0.0 
        self.custom_audio_limit = 30.0      # 목소리 감지 커트라인
        
        self.capture_timer: float = 0.0     # 💡 목소리 감지 후 '3초' 동안 끝까지 담기 위한 타이머
        self.delay_timer: float = 0.0       
        self._legacy_speech_checked: bool = False
        self._pending_speech_game_over: bool = False
        self._ignore_next_fail_dt: bool = False

    def reset(self) -> None:
        self.stop_stream()
        self._reset()

    def _start_audio_stream(self):
        if self.stream is not None:
            return

        import sounddevice as sd

        def callback(indata, frames, time_info, status):
            if status: pass
            
            # 실시간 데시벨 측정은 core.audio의 공통 계산식을 사용합니다.
            rms = self.audio_meter.calculate_rms(indata)
            self.current_live_db = self.audio_meter.calculate_relative_db(rms)

            # 콜백은 항상 버퍼에 데이터를 채워 넣습니다.
            self.recorded_chunks.append(indata.copy())

        try:
            self.stream = sd.InputStream(samplerate=48000, channels=2, dtype='float32', callback=callback)
            self.stream.start()
        except Exception as e:
            self.stream = None
            print(f"[마이크 에러]: {e}")

    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def handle_event(self, event, game_state) -> str | None:
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return "stage3"
        if getattr(event, "type", None) == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._release_stage_audio()
            return "quit"
        return None

    def update(self, dt, game_state, services) -> str | None:
        self._elapsed += dt

        # 인트로 2초 대기
        if not self.intro_done:
            transition = apply_global_rules(dt, self._elapsed, game_state, services)
            if transition is not None:
                self._release_stage_audio()
                return transition
            if self._elapsed >= self.intro_duration:
                self.intro_done = True
                self._prepare_stage_audio(services)
                return None
            return None

        # 현재 목표 대사 세팅
        target_text = _TARGET_TEXT
        
        self.recognizer.target_text = target_text

        speech = services.get("speech")
        if speech is not None and hasattr(speech, "target_text"):
            speech.target_text = target_text
        if services.get("audio") is None and hasattr(speech, "recognize"):
            return self._update_without_audio_stream(dt, game_state, speech)

        # -----------------------------------------------------------------
        # 1. 10초 카운트다운 (말하기 전 대기 상태)
        # -----------------------------------------------------------------
        if self.audio_status == "RECORDING":
            self.time_elapsed += dt
            self.progress = min((self.time_elapsed / self.time_limit) * 100.0, 100.0)

            # 조용할 때는 버퍼를 계속 비워줍니다. (첫 음절이 안 잘리게 최근 데이터만 유지)
            if self.current_live_db < self.custom_audio_limit:
                if len(self.recorded_chunks) > 10: 
                    self.recorded_chunks = self.recorded_chunks[-5:]
            
            # 💥 50dB 이상 소리가 감지되면 즉시 녹음 집중 모드로 전환!
            else:
                self.audio_status = "CAPTURING_SPEECH"
                self.capture_timer = 0.0
                print(f"[목소리 감지!] {self.current_live_db}dB")

            # 제한 시간 동안 조용히 있으면 통과
            if self.progress >= 100.0:
                self._release_stage_audio()
                game_state.mark_stage_clear(2)
                return "stage3"

        # -----------------------------------------------------------------
        # 2. 목소리 담기 (💡 3초 동안 프로그래스 바 정지 후 느긋하게 끝까지 듣기!)
        # -----------------------------------------------------------------
        elif self.audio_status == "CAPTURING_SPEECH":
            self.capture_timer += dt
            # 말을 시작한 시점부터 3초 동안 충분히 녹음합니다.
            if self.capture_timer >= 3.0:
                self.audio_status = "ANALYZING"
                
                if len(self.recorded_chunks) > 0:
                    merged_audio = np.concatenate(self.recorded_chunks, axis=0)
                    try:
                        # 48000Hz 데이터를 Scipy로 변환하여 정밀 채점
                        result = self.recognizer.recognize_buffer(merged_audio, source_sample_rate=48000)
                        
                        if result.recognized_text:
                            self.user_spoken_text = result.recognized_text.strip()
                            self.match_ratio_percent = round(result.similarity * 100.0, 1)
                        else:
                            self.user_spoken_text = "(판독 불가)"
                            self.match_ratio_percent = 0.0
                            
                        print(f"[인식 문장] '{self.user_spoken_text}' | 일치율: {self.match_ratio_percent}%")
                        
                        if result.recognized_text:
                            self.audio_status = "FAILED_MATCH"
                            self._ignore_next_fail_dt = True
                        else:
                            self.audio_status = "RECORDING"
                            self.recorded_chunks = []
                            
                    except Exception as e:
                        print(f"[에러]: {e}")
                        self.audio_status = "FAILED_MATCH"
                        self._ignore_next_fail_dt = True
                
                self.delay_timer = 0.0

        # -----------------------------------------------------------------
        # 3-A. 실패: 인식된 문장이 있으면 결과를 잠시 보여준 뒤 게임 오버
        # -----------------------------------------------------------------
        elif self.audio_status == "FAILED_MATCH":
            if self._ignore_next_fail_dt:
                self._ignore_next_fail_dt = False
                return None

            self.delay_timer += dt
            if self.delay_timer >= _FAIL_RESULT_DISPLAY_SECONDS:
                self._release_stage_audio()
                game_state.enter_game_over(SOUND_LIMIT_REASON)
                return "game_over"

        # -----------------------------------------------------------------
        # 3-B. 통과 -> 다음 단계 진입
        # -----------------------------------------------------------------
        elif self.audio_status == "PHASE_CLEAR":
            self.delay_timer += dt
            if self.delay_timer >= 2.0:
                self._release_stage_audio()
                game_state.mark_stage_clear(2)
                return "stage3"

        return None

    def _prepare_stage_audio(self, services) -> None:
        audio = services.get("audio")
        if audio is None:
            return
        if audio is not None and hasattr(audio, "release"):
            audio.release()
        self._start_audio_stream()

    def _release_stage_audio(self) -> None:
        self.stop_stream()
        self.recognizer.release()

    def _update_without_audio_stream(self, dt, game_state, speech) -> str | None:
        if self._pending_speech_game_over:
            if self._ignore_next_fail_dt:
                self._ignore_next_fail_dt = False
                return None

            self.delay_timer += dt
            if self.delay_timer >= _FAIL_RESULT_DISPLAY_SECONDS:
                game_state.enter_game_over(SOUND_LIMIT_REASON)
                return "game_over"
            return None

        if self._legacy_speech_checked:
            self.time_elapsed += dt
            self.progress = min((self.time_elapsed / self.time_limit) * 100.0, 100.0)
            if self.progress >= 100.0:
                game_state.mark_stage_clear(2)
                return "stage3"
            return None

        self._legacy_speech_checked = True
        self.time_elapsed += dt
        self.progress = min((self.time_elapsed / self.time_limit) * 100.0, 100.0)
        result = speech.recognize(5.0)
        if result.recognized_text:
            self.user_spoken_text = result.recognized_text.strip()
            self.match_ratio_percent = round(result.similarity * 100.0, 1)
            self.audio_status = "FAILED_MATCH"
            self.delay_timer = 0.0
            self._pending_speech_game_over = True
            self._ignore_next_fail_dt = True
            return None

        self.user_spoken_text = "(판독 불가)"
        self.match_ratio_percent = 0.0
        if self.progress >= 100.0:
            game_state.mark_stage_clear(2)
            return "stage3"
        return None

    def draw(self, screen, game_state, services) -> None:
        if not hasattr(screen, "fill"): return None
        screen.fill((0, 0, 0))
        
        # 💡 Stage 1과 완벽하게 동일한 인트로 CSS 연출
        if not self.intro_done:
            font = pygame.font.Font(config.FONT_PATH, 96)
            text = font.render("STAGE 2", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)))
            return

        # 본 게임 폰트 설정
        font = pygame.font.Font(config.FONT_PATH, 38)
        sub_font = pygame.font.Font(config.FONT_PATH, 22)
        phase_font = pygame.font.Font(config.FONT_PATH, 26)
        status_font = pygame.font.Font(config.FONT_PATH, 26)
        debug_font = pygame.font.Font(config.FONT_PATH, 22)

        warning_text = "그들의 기척이 더 가까워졌어요"
        instruction_text = "당장 아래 말을 따라 읽으세요"
        bar_color = (0, 180, 255)

        warning_surface = font.render(warning_text, True, (220, 0, 0))
        screen.blit(warning_surface, warning_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 72)))

        instruction_surface = sub_font.render(instruction_text, True, (220, 0, 0))
        screen.blit(instruction_surface, instruction_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 122)))

        target_surface = font.render(_TARGET_TEXT, True, (255, 255, 255))
        screen.blit(target_surface, target_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 178)))

        if self.audio_status == "RECORDING":
            status_str, status_color = "[ 침묵 유지 중 ]", (0, 255, 100)
        elif self.audio_status == "CAPTURING_SPEECH":
            status_str, status_color = "[ 목소리 감지됨 ]", (255, 100, 100)
        elif self.audio_status == "ANALYZING":
            status_str, status_color = "[ 분석 중 ]", (0, 255, 255)
        elif self.audio_status == "FAILED_MATCH":
            status_str, status_color = f"[ 실패 ] {self.match_ratio_percent}%", (255, 50, 50)
        elif self.audio_status == "PHASE_CLEAR":
            status_str, status_color = "[ 통과 ] 오!", (0, 255, 0)
            
        status_surface = status_font.render(status_str, True, status_color)
        screen.blit(status_surface, status_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 15)))

        spoken_display = f"AI 인식 문장: \"{self.user_spoken_text}\"  |  현재 일치율: {self.match_ratio_percent}%"
        result_surface = debug_font.render(spoken_display, True, (180, 180, 180) if self.match_ratio_percent < 50.0 else (100, 255, 100))
        screen.blit(result_surface, result_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 35)))

        db_display = f"현재 소음도: {self.current_live_db} dB  /  음성 인식 커트라인: {self.custom_audio_limit} dB"
        db_surface = debug_font.render(db_display, True, (0, 220, 100) if self.current_live_db < self.custom_audio_limit else (255, 100, 0))
        screen.blit(db_surface, db_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 65)))

        remaining_time = max(0.0, self.time_limit - self.time_elapsed)
        phase_surface = phase_font.render(f"음성 돌파 단계  |  남은 시간: {round(remaining_time, 1)}초", True, (255, 255, 255))
        screen.blit(phase_surface, phase_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 105)))

        bar_width, bar_height = 500, 20
        bar_x, bar_y = (config.SCREEN_WIDTH - bar_width) // 2, (config.SCREEN_HEIGHT // 2) + 140
        pygame.draw.rect(screen, (70, 70, 70), (bar_x, bar_y, bar_width, bar_height), 2)
        if (fill_width := int(bar_width * (self.progress / 100.0))) > 0:
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_width, bar_height))

        return None
