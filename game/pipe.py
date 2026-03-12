import random
from typing import Tuple

import pygame


class Pipe:

    def __init__(self, x: float) -> None:
        self.x: float = x
        self.width: int = 80
        self.gap_size: int = 200
        self.gap_y: int = random.randint(150, 450)

        self.speed: float = 3.0
        self.color: Tuple[int, int, int] = (0, 255, 0)

        self.passed: bool = False

    def update(self) -> None:
        self.x -= self.speed

    def draw(self, screen: pygame.Surface, screen_height: int) -> None:
        top_height = self.gap_y - self.gap_size // 2
        bottom_y = self.gap_y + self.gap_size // 2

        pygame.draw.rect(screen, self.color, (int(self.x), 0, self.width, top_height))
        pygame.draw.rect(
            screen,
            self.color,
            (int(self.x), bottom_y, self.width, screen_height - bottom_y),
        )