import config


def run() -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Your Face")
    clock = pygame.time.Clock()   # 프레임 제한용 시계

    running = True
    while running:
        for event in pygame.event.get():   # 사용자 입력 이벤트 처리
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        pygame.display.flip()   # 화면 업데이트 (지금까지 그린 거 출력)
        clock.tick(config.FPS)  # 프레임 제한

    pygame.quit()


if __name__ == "__main__":
    run()
