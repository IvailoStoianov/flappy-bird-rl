from __future__ import annotations

from typing import List, Tuple

import pygame

from bird import Bird
from pipe import Pipe


# Window and game configuration
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800
FPS = 60

GROUND_HEIGHT = 50
GROUND_Y = WINDOW_HEIGHT - GROUND_HEIGHT

PIPE_SPAWN_DELAY_FRAMES = 90

BACKGROUND_COLOR: Tuple[int, int, int] = (0, 0, 255)  # blue
GROUND_COLOR: Tuple[int, int, int] = (139, 69, 19) # brown
TEXT_COLOR: Tuple[int, int, int] = (255, 255, 255) # white
GAME_OVER_COLOR: Tuple[int, int, int] = (255, 0, 0) # red


class Game:

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title_font = pygame.font.SysFont("Arial", 60)
        self.text_font = pygame.font.SysFont("Arial", 40)
        self.reset()

    def reset(self) -> None:
        self.bird = Bird(x=WINDOW_WIDTH / 2, y=WINDOW_HEIGHT / 2)
        self.pipes: List[Pipe] = []
        self.spawn_timer = 0
        self.score = 0
        self.game_over = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not self.game_over:
                self.bird.flap()
            elif event.key == pygame.K_RETURN and self.game_over:
                self.reset()

    def update(self) -> None:
        if self.game_over:
            return

        self.bird.update()

        # collision check for ground
        if self.bird.y >= GROUND_Y:
            self.bird.y = GROUND_Y
            self.bird.velocity = 0
            self.game_over = True

        # generate pipes
        self.spawn_timer += 1
        if self.spawn_timer > PIPE_SPAWN_DELAY_FRAMES:
            self.pipes.append(Pipe(WINDOW_WIDTH))
            self.spawn_timer = 0

        # update pipes, handle collisions and scoring
        for pipe in self.pipes:
            pipe.update()

            # collision check for pipes
            if self.bird.x + self.bird.size > pipe.x and self.bird.x < pipe.x + pipe.width:
                top = pipe.gap_y - pipe.gap_size // 2
                bottom = pipe.gap_y + pipe.gap_size // 2
                if self.bird.y < top or self.bird.y > bottom:
                    self.game_over = True

            # increase score if pipe is passed
            if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                self.score += 1
                pipe.passed = True

        # remove pipes that have moved off-screen
        self.pipes = [pipe for pipe in self.pipes if pipe.x + pipe.width > 0]

    def draw(self) -> None:
        # draw background
        self.screen.fill(BACKGROUND_COLOR)

        # draw ground
        pygame.draw.rect(
            self.screen,
            GROUND_COLOR,
            (0, GROUND_Y, WINDOW_WIDTH, GROUND_HEIGHT),
        )

        # draw pipes
        for pipe in self.pipes:
            pipe.draw(self.screen, WINDOW_HEIGHT)

        # draw bird
        self.bird.draw(self.screen)

        if not self.game_over:
            # display score
            score_text = self.text_font.render(str(self.score), True, TEXT_COLOR)
            text_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 100))
            self.screen.blit(score_text, text_rect)
        else:
            game_over_text = self.title_font.render("YOU DIED", True, GAME_OVER_COLOR)
            score_text = self.text_font.render(
                f"Final Score: {self.score}", True, TEXT_COLOR
            )
            restart_text = self.text_font.render(
                "Press ENTER to restart", True, TEXT_COLOR
            )

            self.screen.blit(
                game_over_text,
                game_over_text.get_rect(center=(WINDOW_WIDTH // 2, 300)),
            )
            self.screen.blit(
                score_text,
                score_text.get_rect(center=(WINDOW_WIDTH // 2, 380)),
            )
            self.screen.blit(
                restart_text,
                restart_text.get_rect(center=(WINDOW_WIDTH // 2, 450)),
            )


def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()

    game = Game(screen)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update()

        game.draw()
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
