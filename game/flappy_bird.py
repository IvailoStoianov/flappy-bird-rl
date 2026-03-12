from __future__ import annotations

from typing import List, Tuple

import pygame
import numpy as np

from .bird import Bird
from .pipe import Pipe


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


class FlappyBird:

    def __init__(self) -> None:
        # Pygame rendering objects (only created when needed)
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.title_font: pygame.font.Font | None = None
        self.text_font: pygame.font.Font | None = None

        self.reset()

    def reset(self) -> None:
        self.bird = Bird(x=WINDOW_WIDTH / 2, y=WINDOW_HEIGHT / 2)
        # Start with a single pipe ahead of the bird so observations are always valid
        self.pipes: List[Pipe] = [Pipe(WINDOW_WIDTH)]
        self.spawn_timer = 0
        self.score = 0
        self.game_over = False

        return self._get_observation()
    
    def take_action(self, action=None):
        """
        Step the Flappy Bird game once for RL.

        action:
          - 0: do nothing
          - 1: flap
        """
        # If the episode is already over, just return final observation
        if self.game_over:
            return self._get_observation(), 0.0, True, False, {"score": self.score}

        # Interpret action (supports scalar or numpy array from SB3)
        if action is not None:
            act = int(np.asarray(action).item())
            if act == 1:
                self.bird.flap()

        # Run one game update step
        prev_score = self.score
        self.update()

        terminated = self.game_over

        # Reward shaping:
        # staying alive +0.1
        # passing a pipe +10
        # death -100
        reward = 0.1
        if self.score > prev_score:
            reward = 10.0
        if terminated:
            reward = -100.0

        observation = self._get_observation()
        info = {"score": self.score}

        # No time-limit truncation logic yet, so truncated=False
        return observation, reward, terminated, False, info
    
    def _get_observation(self):
        # Find the next pipe that the bird has not passed yet
        next_pipe = None
        for pipe in self.pipes:
            if not pipe.passed:
                next_pipe = pipe
                break

        # If there are no pipes yet, create a "virtual" one straight ahead
        if next_pipe is None:
            pipe_x = WINDOW_WIDTH
            gap_center_y = WINDOW_HEIGHT / 2
            gap_size = 200
        else:
            pipe_x = next_pipe.x
            gap_center_y = next_pipe.gap_y
            gap_size = next_pipe.gap_size

        # Bird state
        bird_x = self.bird.x
        bird_y = self.bird.y
        bird_velocity = self.bird.velocity

        # Pipe gap geometry derived from center + gap size
        top_pipe_bottom = gap_center_y - gap_size / 2
        bottom_pipe_top = gap_center_y + gap_size / 2

        # --- Observations (normalized) ---

        # Bird vertical position relative to screen height
        bird_height_norm = bird_y / WINDOW_HEIGHT

        # Bird vertical velocity normalized by max velocity
        bird_velocity_norm = bird_velocity / self.bird.max_velocity

        # Horizontal distance from bird to next pipe
        # Positive = pipe is ahead, negative = bird passed it
        horizontal_distance_to_pipe = (pipe_x - bird_x) / WINDOW_WIDTH

        # Vertical distance between bird and center of pipe gap
        # Helps the agent align with the gap
        vertical_distance_to_gap = (gap_center_y - bird_y) / WINDOW_HEIGHT

        # Distance between bird and bottom of the top pipe
        # Helps avoid hitting the top pipe
        distance_to_top_pipe = (top_pipe_bottom - bird_y) / WINDOW_HEIGHT

        # Distance between bird and top of the bottom pipe
        # Helps avoid hitting the bottom pipe
        distance_to_bottom_pipe = (bird_y - bottom_pipe_top) / WINDOW_HEIGHT

        # Clip values to keep them in stable range for RL algorithms
        horizontal_distance_to_pipe = np.clip(horizontal_distance_to_pipe, -1, 1)
        vertical_distance_to_gap = np.clip(vertical_distance_to_gap, -1, 1)
        bird_velocity_norm = np.clip(bird_velocity_norm, -1, 1)

        # Return observation vector
        return np.array([
            bird_height_norm,
            bird_velocity_norm,
            horizontal_distance_to_pipe,
            vertical_distance_to_gap,
            distance_to_top_pipe,
            distance_to_bottom_pipe
        ], dtype=np.float32)

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
        if self.screen is None or self.text_font is None or self.title_font is None:
            return

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

    def render(self, mode: str = "human") -> None:
        """Render the current game frame for Gymnasium."""
        if mode == "human":
            # Lazily create the window and rendering resources
            if self.screen is None:
                self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
                pygame.display.set_caption("Flappy Bird")
                self.clock = pygame.time.Clock()
                self.title_font = pygame.font.SysFont("Arial", 60)
                self.text_font = pygame.font.SysFont("Arial", 40)

            self.draw()
            pygame.display.flip()

            if self.clock is not None:
                self.clock.tick(FPS)

    def close(self) -> None:
        """Close the game and pygame."""
        pygame.quit()


def main() -> None:
    pygame.init()

    game = FlappyBird()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update()
        game.render("human")

    pygame.quit()


if __name__ == "__main__":
    main()
