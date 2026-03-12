import pygame
from typing import Tuple


class Bird:

    def __init__(self, x: float = 250, y: float = 400) -> None:
        self.x: float = x
        self.y: float = y
        self.size: int = 30
        self.color: Tuple[int, int, int] = (255, 255, 0)  # yellow

        self.velocity: float = 0.0
        self.max_velocity: float = 10.0
        self.gravity: float = 0.5
        self.flap_strength: float = -10.0

    def update(self) -> None:
        self.velocity += self.gravity
        self.y += self.velocity

    def flap(self) -> None:
        self.velocity = self.flap_strength

    def draw(self, screen: pygame.Surface) -> None:
        bird_pos = (int(self.x), int(self.y))
        pygame.draw.circle(screen, self.color, bird_pos, self.size)