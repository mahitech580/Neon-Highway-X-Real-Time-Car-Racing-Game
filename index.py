import pygame
import random
import math
import sys
import json
import os
from dataclasses import dataclass
from enum import Enum, auto
from collections import deque

pygame.init()

WIDTH = 1280
HEIGHT = 720
FPS = 120

ROAD_X = 150
ROAD_WIDTH = 980
ROAD_RIGHT = ROAD_X + ROAD_WIDTH
LANES = 5
LANE_WIDTH = ROAD_WIDTH / LANES

PLAYER_Y = 565

RACE_TIME = 180.0
TOTAL_LAPS = 3

NORMAL_SPEED = 410.0
FAST_SPEED = 560.0
BOOST_SPEED = 690.0
NITRO_SPEED = 790.0

SAVE_FILE = "neon_racing_save.json"

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON HIGHWAY REAL TIME")
clock = pygame.time.Clock()

BLACK = (4, 7, 12)
WHITE = (245, 248, 255)
GRAY = (120, 130, 145)
DARK = (15, 19, 28)
DARK2 = (23, 28, 38)
ROAD = (38, 41, 48)
ROAD_LIGHT = (48, 52, 61)
GRASS = (10, 55, 32)

CYAN = (0, 225, 255)
BLUE = (35, 105, 240)
RED = (220, 40, 55)
GREEN = (45, 210, 105)
YELLOW = (255, 215, 45)
ORANGE = (255, 125, 25)
PURPLE = (180, 70, 250)
PINK = (255, 75, 185)
SILVER = (190, 200, 215)
GLASS = (25, 45, 60)
TIRE = (9, 9, 11)

FONT14 = pygame.font.SysFont("arial", 14, bold=True)
FONT16 = pygame.font.SysFont("arial", 16, bold=True)
FONT18 = pygame.font.SysFont("arial", 18, bold=True)
FONT22 = pygame.font.SysFont("arial", 22, bold=True)
FONT26 = pygame.font.SysFont("arial", 26, bold=True)
FONT32 = pygame.font.SysFont("arial", 32, bold=True)
FONT42 = pygame.font.SysFont("arial", 42, bold=True)
FONT56 = pygame.font.SysFont("arial", 56, bold=True)
FONT70 = pygame.font.SysFont("arial", 70, bold=True)


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def lane_center(lane):
    return ROAD_X + lane * LANE_WIDTH + LANE_WIDTH / 2


def draw_text(value, font, color, x, y, center=False):
    image = font.render(str(value), True, color)
    rect = image.get_rect()

    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))

    screen.blit(image, rect)
    return rect


def draw_panel(rect, fill, border, radius=12, width=2):
    pygame.draw.rect(
        screen,
        fill,
        rect,
        border_radius=radius
    )

    pygame.draw.rect(
        screen,
        border,
        rect,
        width,
        border_radius=radius
    )


def format_time(value):
    minutes = int(value // 60)
    seconds = value - minutes * 60
    return f"{minutes:02d}:{seconds:05.2f}"


class GameState(Enum):
    MENU = auto()
    COUNTDOWN = auto()
    RACING = auto()
    PAUSED = auto()
    FINISHED = auto()
    GAME_OVER = auto()


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: tuple
    life: float
    max_life: float
    size: float

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 120 * dt
        self.life -= dt

    def draw(self):
        if self.life <= 0:
            return

        alpha = clamp(
            self.life / self.max_life,
            0,
            1
        )

        radius = max(
            1,
            int(self.size * alpha)
        )

        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x), int(self.y)),
            radius
        )


class ParticleSystem:
    def __init__(self):
        self.items = []

    def emit(
        self,
        x,
        y,
        color,
        count=10,
        speed_min=40,
        speed_max=180
    ):
        for _ in range(count):
            angle = random.uniform(
                0,
                math.tau
            )

            speed = random.uniform(
                speed_min,
                speed_max
            )

            self.items.append(
                Particle(
                    x,
                    y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    color,
                    random.uniform(
                        0.2,
                        0.8
                    ),
                    0.8,
                    random.uniform(
                        2,
                        5
                    )
                )
            )

    def emit_trail(
        self,
        x,
        y,
        color
    ):
        self.emit(
            x,
            y,
            color,
            1,
            20,
            80
        )

    def update(self, dt):
        for item in self.items:
            item.update(dt)

        self.items = [
            item
            for item in self.items
            if item.life > 0
        ]

    def draw(self):
        for item in self.items:
            item.draw()


class Glow:
    @staticmethod
    def circle(
        x,
        y,
        radius,
        color
    ):
        for level in range(
            4,
            0,
            -1
        ):
            r = int(
                radius
                * (
                    1
                    + level * 0.2
                )
            )

            surface = pygame.Surface(
                (r * 2, r * 2),
                pygame.SRCALPHA
            )

            alpha = 12 + level * 10

            pygame.draw.circle(
                surface,
                (*color, alpha),
                (r, r),
                r
            )

            screen.blit(
                surface,
                (
                    int(x - r),
                    int(y - r)
                )
            )


class Road:
    def __init__(self):
        self.scroll = 0.0
        self.time = 0.0
        self.player_distance = 0.0

        self.side_objects = []

        for index in range(100):
            self.side_objects.append(
                {
                    "distance": random.uniform(
                        0,
                        100000
                    ),
                    "side": random.choice(
                        [-1, 1]
                    ),
                    "type": random.randint(
                        0,
                        2
                    ),
                    "size": random.randint(
                        15,
                        50
                    )
                }
            )

    def update(
        self,
        speed,
        dt
    ):
        self.scroll = (
            self.scroll
            + speed * dt
        ) % 120

        self.time += dt

    def draw(self):
        screen.fill(GRASS)

        pygame.draw.rect(
            screen,
            (23, 28, 35),
            (
                ROAD_X - 28,
                0,
                28,
                HEIGHT
            )
        )

        pygame.draw.rect(
            screen,
            ROAD,
            (
                ROAD_X,
                0,
                ROAD_WIDTH,
                HEIGHT
            )
        )

        pygame.draw.rect(
            screen,
            (23, 28, 35),
            (
                ROAD_RIGHT,
                0,
                28,
                HEIGHT
            )
        )

        pygame.draw.line(
            screen,
            WHITE,
            (
                ROAD_X,
                0
            ),
            (
                ROAD_X,
                HEIGHT
            ),
            5
        )

        pygame.draw.line(
            screen,
            WHITE,
            (
                ROAD_RIGHT,
                0
            ),
            (
                ROAD_RIGHT,
                HEIGHT
            ),
            5
        )

        for lane in range(1, LANES):
            x = int(
                ROAD_X
                + lane * LANE_WIDTH
            )

            y = (
                -120
                + self.scroll
            )

            while y < HEIGHT:
                pygame.draw.rect(
                    screen,
                    (155, 160, 170),
                    (
                        x - 3,
                        int(y),
                        6,
                        65
                    ),
                    border_radius=3
                )

                y += 120

        marker_y = (
            -80
            + self.scroll
        )

        while marker_y < HEIGHT:
            pygame.draw.rect(
                screen,
                CYAN,
                (
                    ROAD_X - 45,
                    int(marker_y),
                    13,
                    26
                ),
                border_radius=3
            )

            pygame.draw.rect(
                screen,
                PURPLE,
                (
                    ROAD_RIGHT + 32,
                    int(marker_y),
                    13,
                    26
                ),
                border_radius=3
            )

            marker_y += 80

        for item in self.side_objects:
            relative = (
                item["distance"]
                - self.player_distance
            )

            y = (
                PLAYER_Y
                - relative * 0.11
            )

            if y < -120 or y > HEIGHT + 120:
                continue

            side = item["side"]

            if side < 0:
                x = (
                    ROAD_X
                    - 75
                    - item["size"]
                )
            else:
                x = (
                    ROAD_RIGHT
                    + 50
                )

            if item["type"] == 0:
                color = (
                    16,
                    80,
                    48
                )

                pygame.draw.rect(
                    screen,
                    color,
                    (
                        int(x),
                        int(y),
                        item["size"],
                        item["size"] * 2
                    ),
                    border_radius=3
                )

            elif item["type"] == 1:
                pygame.draw.circle(
                    screen,
                    (
                        16,
                        95,
                        58
                    ),
                    (
                        int(x),
                        int(y)
                    ),
                    item["size"] // 2
                )

            else:
                pygame.draw.rect(
                    screen,
                    (
                        55,
                        35,
                        90
                    ),
                    (
                        int(x),
                        int(y),
                        item["size"],
                        item["size"]
                    )
                )


class Car:
    def __init__(
        self,
        x,
        y,
        color,
        name
    ):
        self.x = float(x)
        self.y = float(y)

        self.color = color
        self.name = name

        self.width = 68
        self.height = 116

        self.speed = 0.0
        self.distance = 0.0

        self.health = 100.0

        self.hit_timer = 0.0
        self.damage_flash = 0.0

    @property
    def rect(self):
        return pygame.Rect(
            int(
                self.x
                - self.width / 2
            ),
            int(
                self.y
                - self.height / 2
            ),
            self.width,
            self.height
        )

    def update_timers(self, dt):
        self.hit_timer = max(
            0,
            self.hit_timer - dt
        )

        self.damage_flash = max(
            0,
            self.damage_flash - dt
        )

    def damage(self, amount):
        if self.hit_timer > 0:
            return

        self.health = max(
            0,
            self.health - amount
        )

        self.hit_timer = 0.7
        self.damage_flash = 0.18

        self.speed *= 0.58

    def draw_shadow(self):
        shadow = pygame.Rect(
            int(self.x - 40),
            int(self.y + 45),
            80,
            24
        )

        surface = pygame.Surface(
            shadow.size,
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            surface,
            (0, 0, 0, 100),
            surface.get_rect()
        )

        screen.blit(
            surface,
            shadow.topleft
        )

    def draw_wheels(self):
        x = int(self.x)
        y = int(self.y)

        positions = [
            (
                x - 38,
                y - 32
            ),
            (
                x + 28,
                y - 32
            ),
            (
                x - 38,
                y + 25
            ),
            (
                x + 28,
                y + 25
            )
        ]

        for wx, wy in positions:
            pygame.draw.rect(
                screen,
                TIRE,
                (
                    wx,
                    wy,
                    11,
                    28
                ),
                border_radius=4
            )

            pygame.draw.rect(
                screen,
                (80, 85, 92),
                (
                    wx + 2,
                    wy + 5,
                    7,
                    18
                ),
                border_radius=2
            )

    def draw_windows(self):
        x = int(self.x)
        y = int(self.y)

        windshield = [
            (
                x - 22,
                y - 38
            ),
            (
                x + 22,
                y - 38
            ),
            (
                x + 17,
                y - 9
            ),
            (
                x - 17,
                y - 9
            )
        ]

        pygame.draw.polygon(
            screen,
            GLASS,
            windshield
        )

        pygame.draw.polygon(
            screen,
            SILVER,
            windshield,
            2
        )

        rear_window = [
            (
                x - 18,
                y - 6
            ),
            (
                x + 18,
                y - 6
            ),
            (
                x + 18,
                y + 12
            ),
            (
                x - 18,
                y + 12
            )
        ]

        pygame.draw.polygon(
            screen,
            (18, 29, 39),
            rear_window
        )

        pygame.draw.line(
            screen,
            SILVER,
            (
                x,
                y - 35
            ),
            (
                x,
                y - 10
            ),
            2
        )

    def draw_lights(self):
        x = int(self.x)
        y = int(self.y)

        pygame.draw.rect(
            screen,
            LIGHT if 'LIGHT' in globals() else WHITE,
            (
                x - 25,
                y - 51,
                17,
                9
            ),
            border_radius=3
        )

        pygame.draw.rect(
            screen,
            LIGHT if 'LIGHT' in globals() else WHITE,
            (
                x + 8,
                y - 51,
                17,
                9
            ),
            border_radius=3
        )

        pygame.draw.rect(
            screen,
            RED,
            (
                x - 25,
                y + 42,
                17,
                8
            ),
            border_radius=3
        )

        pygame.draw.rect(
            screen,
            RED,
            (
                x + 8,
                y + 42,
                17,
                8
            ),
            border_radius=3
        )

    def draw_body(self):
        x = int(self.x)
        y = int(self.y)

        color = (
            WHITE
            if self.damage_flash > 0
            else self.color
        )

        body = pygame.Rect(
            x - self.width // 2,
            y - self.height // 2,
            self.width,
            self.height
        )

        pygame.draw.rect(
            screen,
            color,
            body,
            border_radius=15
        )

        edge = tuple(
            clamp(
                value + 40,
                0,
                255
            )
            for value in color
        )

        pygame.draw.rect(
            screen,
            edge,
            (
                body.x + 5,
                body.y + 5,
                body.width - 10,
                body.height - 10
            ),
            2,
            border_radius=13
        )

        pygame.draw.polygon(
            screen,
            edge,
            [
                (
                    x,
                    y - 55
                ),
                (
                    x + 23,
                    y - 38
                ),
                (
                    x + 26,
                    y + 35
                ),
                (
                    x,
                    y + 54
                ),
                (
                    x - 26,
                    y + 35
                ),
                (
                    x - 23,
                    y - 38
                )
            ],
            2
        )

        self.draw_windows()
        self.draw_wheels()
        self.draw_lights()

        pygame.draw.line(
            screen,
            SILVER,
            (
                x - 25,
                y + 22
            ),
            (
                x + 25,
                y + 22
            ),
            2
        )

    def draw(self):
        self.draw_shadow()
        self.draw_body()


class PlayerCar(Car):
    def __init__(self):
        super().__init__(
            lane_center(2),
            PLAYER_Y,
            BLUE,
            "PLAYER"
        )

        self.normal_max = NORMAL_SPEED
        self.fast_max = FAST_SPEED
        self.boost_max = BOOST_SPEED
        self.nitro_max = NITRO_SPEED

        self.acceleration = 145.0
        self.steering = 580.0

        self.nitro_amount = 100.0

        self.fast = False
        self.nitro = False

        self.boost_timer = 0.0

        self.lateral_velocity = 0.0

    def reset(self):
        self.x = lane_center(2)
        self.y = PLAYER_Y

        self.speed = 0.0
        self.distance = 0.0

        self.health = 100.0

        self.nitro_amount = 100.0

        self.fast = False
        self.nitro = False

        self.boost_timer = 0.0

        self.lateral_velocity = 0.0

        self.hit_timer = 0
        self.damage_flash = 0

    def activate_boost(self):
        self.boost_timer = 5.0

    def update(self, game, dt):
        self.update_timers(dt)

        self.boost_timer = max(
            0,
            self.boost_timer - dt
        )

        keys = pygame.key.get_pressed()

        self.fast = bool(
            keys[pygame.K_f]
        )

        self.nitro = bool(
            keys[pygame.K_SPACE]
            and self.nitro_amount > 0
        )

        if self.nitro:
            self.nitro_amount = max(
                0,
                self.nitro_amount
                - 35 * dt
            )
        else:
            self.nitro_amount = min(
                100,
                self.nitro_amount
                + 5 * dt
            )

        if self.nitro:
            maximum = self.nitro_max
        elif self.boost_timer > 0:
            maximum = self.boost_max
        elif self.fast:
            maximum = self.fast_max
        else:
            maximum = self.normal_max

        self.speed += (
            self.acceleration
            * dt
        )

        self.speed = min(
            self.speed,
            maximum
        )

        steering = 0

        if (
            keys[pygame.K_a]
            or keys[pygame.K_LEFT]
        ):
            steering -= 1

        if (
            keys[pygame.K_d]
            or keys[pygame.K_RIGHT]
        ):
            steering += 1

        steering_power = (
            self.steering
            * (
                1.15
                - self.speed
                / 1000
            )
        )

        target_lateral = (
            steering
            * steering_power
        )

        self.lateral_velocity += (
            target_lateral
            - self.lateral_velocity
        ) * min(
            1,
            dt * 10
        )

        self.x += (
            self.lateral_velocity
            * dt
        )

        if (
            keys[pygame.K_s]
            or keys[pygame.K_DOWN]
        ):
            self.speed -= (
                500 * dt
            )

        self.speed = max(
            70,
            self.speed
        )

        self.x = clamp(
            self.x,
            ROAD_X + 45,
            ROAD_RIGHT - 45
        )

        self.distance += (
            self.speed * dt
        )

        if self.nitro:
            game.particles.emit_trail(
                self.x,
                self.y + 52,
                CYAN
            )

        elif self.boost_timer > 0:
            game.particles.emit_trail(
                self.x,
                self.y + 52,
                PURPLE
            )

        elif self.fast:
            game.particles.emit_trail(
                self.x,
                self.y + 52,
                ORANGE
            )

        else:
            game.particles.emit_trail(
                self.x,
                self.y + 52,
                BLUE
            )

    def draw_turbo(self):
        active = (
            self.fast
            or self.nitro
            or self.boost_timer > 0
        )

        if not active:
            return

        x = int(self.x)
        y = int(self.y)

        if self.nitro:
            color = CYAN
            length = 92
        elif self.boost_timer > 0:
            color = PURPLE
            length = 82
        else:
            color = ORANGE
            length = 68

        length += random.randint(
            0,
            15
        )

        pygame.draw.polygon(
            screen,
            YELLOW,
            [
                (
                    x - 16,
                    y + 48
                ),
                (
                    x,
                    y + length
                ),
                (
                    x + 16,
                    y + 48
                )
            ]
        )

        pygame.draw.polygon(
            screen,
            color,
            [
                (
                    x - 9,
                    y + 48
                ),
                (
                    x,
                    y + length - 18
                ),
                (
                    x + 9,
                    y + 48
                )
            ]
        )

    def draw(self):
        self.draw_shadow()
        self.draw_turbo()
        self.draw_body()

        if (
            self.fast
            or self.boost_timer > 0
        ):
            pygame.draw.circle(
                screen,
                ORANGE
                if self.fast
                else PURPLE,
                (
                    int(self.x),
                    int(self.y)
                ),
                50,
                2
            )


class AICar(Car):
    def __init__(
        self,
        lane,
        color,
        name,
        skill
    ):
        super().__init__(
            lane_center(lane),
            PLAYER_Y,
            color,
            name
        )

        self.lane = lane
        self.target_lane = lane
        self.skill = skill

        self.normal_max = (
            random.uniform(
                380,
                430
            )
            + skill * 70
        )

        self.acceleration = (
            random.uniform(
                125,
                180
            )
        )

        self.distance = random.uniform(
            250,
            1800
        )

        self.change_timer = random.uniform(
            1.5,
            4
        )

        self.overtake_timer = 0

    def reset(self, distance):
        self.lane = random.randrange(
            LANES
        )

        self.target_lane = self.lane

        self.x = lane_center(
            self.lane
        )

        self.y = PLAYER_Y

        self.speed = random.uniform(
            100,
            170
        )

        self.distance = distance

        self.health = 100

        self.change_timer = random.uniform(
            1.5,
            4
        )

        self.overtake_timer = 0

    def select_lane(self, game):
        options = [
            self.lane
        ]

        if self.lane > 0:
            options.append(
                self.lane - 1
            )

        if self.lane < LANES - 1:
            options.append(
                self.lane + 1
            )

        best_lane = self.lane
        best_score = -9999

        for lane in options:
            score = random.uniform(
                -1,
                1
            )

            if lane == self.lane:
                score += 0.35

            player_lane = (
                game.player_lane()
            )

            if lane == player_lane:
                if (
                    abs(
                        self.distance
                        - game.player.distance
                    )
                    < 500
                ):
                    score += 0.8

            for other in game.ai:
                if other is self:
                    continue

                if (
                    other.target_lane
                    == lane
                ):
                    gap = abs(
                        other.distance
                        - self.distance
                    )

                    if gap < 300:
                        score -= 2.5

                    if (
                        other.distance
                        > self.distance
                    ):
                        score -= 1.0

            if score > best_score:
                best_score = score
                best_lane = lane

        self.target_lane = best_lane

    def update(self, game, dt):
        self.update_timers(dt)

        self.change_timer -= dt

        if self.change_timer <= 0:
            self.change_timer = random.uniform(
                1.2,
                3.5
            )

            self.select_lane(game)

        target_x = lane_center(
            self.target_lane
        )

        difference = (
            target_x
            - self.x
        )

        self.x += clamp(
            difference,
            -420 * dt,
            420 * dt
        )

        player_gap = (
            game.player.distance
            - self.distance
        )

        desired = self.normal_max

        if player_gap > 500:
            desired += 35

        if player_gap < -1200:
            desired -= 25

        if random.random() < (
            self.skill * 0.018
        ):
            self.overtake_timer = (
                random.uniform(
                    1.5,
                    3
                )
            )

        if self.overtake_timer > 0:
            self.overtake_timer -= dt
            desired += 65

        self.max_speed = clamp(
            desired,
            350,
            550
        )

        self.accelerate(dt)

        self.distance += (
            self.speed * dt
        )

        relative = (
            self.distance
            - game.player.distance
        )

        self.y = (
            PLAYER_Y
            - relative * 0.115
        )

        if self.y < -250:
            self.distance -= 2200

        if self.y > HEIGHT + 250:
            self.distance += 1400

        self.x = clamp(
            self.x,
            ROAD_X + 45,
            ROAD_RIGHT - 45
        )

    def accelerate(self, dt):
        self.speed += (
            self.acceleration
            * dt
        )

        self.speed = min(
            self.speed,
            self.max_speed
        )

    def draw(self):
        if (
            self.y < -150
            or self.y > HEIGHT + 150
        ):
            return

        super().draw()

        if self.overtake_timer > 0:
            pygame.draw.circle(
                screen,
                YELLOW,
                (
                    int(self.x),
                    int(self.y)
                ),
                43,
                2
            )


class Booster:
    def __init__(
        self,
        distance,
        lane
    ):
        self.distance = distance
        self.lane = lane
        self.active = True
        self.phase = random.uniform(
            0,
            math.tau
        )

    @property
    def x(self):
        return lane_center(
            self.lane
        )

    def update(self, game, dt):
        if not self.active:
            return

        self.phase += dt * 8

        relative = (
            self.distance
            - game.player.distance
        )

        y = (
            PLAYER_Y
            - relative * 0.115
        )

        rect = pygame.Rect(
            int(self.x - 28),
            int(y - 28),
            56,
            56
        )

        if (
            rect.colliderect(
                game.player.rect
            )
            and abs(
                y - PLAYER_Y
            ) < 90
        ):
            self.active = False

            game.player.activate_boost()

            game.boosters_collected += 1

            game.particles.emit(
                self.x,
                y,
                CYAN,
                45,
                100,
                360
            )

            game.notification = (
                "BOOSTER COLLECTED"
            )

            game.notification_timer = 1.5

    def draw(self, player_distance):
        if not self.active:
            return

        relative = (
            self.distance
            - player_distance
        )

        y = (
            PLAYER_Y
            - relative * 0.115
        )

        if (
            y < -100
            or y > HEIGHT + 100
        ):
            return

        x = int(self.x)

        pulse = int(
            math.sin(
                self.phase
            ) * 5
        )

        Glow.circle(
            x,
            y,
            24 + pulse,
            CYAN
        )

        pygame.draw.circle(
            screen,
            CYAN,
            (
                x,
                int(y)
            ),
            26 + pulse,
            3
        )

        pygame.draw.polygon(
            screen,
            YELLOW,
            [
                (
                    x,
                    int(y) - 29
                ),
                (
                    x + 19,
                    int(y)
                ),
                (
                    x,
                    int(y) + 29
                ),
                (
                    x - 19,
                    int(y)
                )
            ]
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (
                x,
                int(y)
            ),
            6
        )


class BoosterManager:
    def __init__(self):
        self.items = []
        self.timer = 1.5

    def reset(self):
        self.items.clear()
        self.timer = 1.3

    def update(self, game, dt):
        self.timer -= dt

        if self.timer <= 0:
            self.timer = random.uniform(
                2.0,
                4.0
            )

            lane = random.randrange(
                LANES
            )

            distance = (
                game.player.distance
                + random.uniform(
                    900,
                    1500
                )
            )

            self.items.append(
                Booster(
                    distance,
                    lane
                )
            )

        for item in self.items:
            item.update(
                game,
                dt
            )

        self.items = [
            item
            for item in self.items
            if item.active
            and item.distance
            > game.player.distance - 800
            and item.distance
            < game.player.distance + 2800
        ]

    def draw(self, distance):
        for item in self.items:
            item.draw(distance)


class CollisionSystem:
    def __init__(self):
        pass

    def update(self, game):
        player = game.player

        for ai in game.ai:

            if ai.hit_timer > 0:
                continue

            if (
                ai.y < -120
                or ai.y > HEIGHT + 120
            ):
                continue

            if player.rect.colliderect(
                ai.rect
            ):
                self.resolve(
                    game,
                    player,
                    ai
                )

    def resolve(
        self,
        game,
        player,
        ai
    ):
        direction = (
            -1
            if player.x < ai.x
            else 1
        )

        player.x += (
            direction * 35
        )

        ai.x -= (
            direction * 35
        )

        player.x = clamp(
            player.x,
            ROAD_X + 45,
            ROAD_RIGHT - 45
        )

        ai.x = clamp(
            ai.x,
            ROAD_X + 45,
            ROAD_RIGHT - 45
        )

        player.damage(15)
        ai.damage(10)

        game.collisions += 1

        game.particles.emit(
            player.x,
            player.y,
            ORANGE,
            40,
            100,
            330
        )

        if game.settings_screen_shake:
            game.shake_timer = 0.25
            game.shake_amount = 10


class Profile:
    def __init__(self):
        self.races = 0
        self.wins = 0
        self.best_time = None
        self.total_boosters = 0
        self.total_collisions = 0
        self.load()

    def load(self):
        if not os.path.exists(
            SAVE_FILE
        ):
            return

        try:
            with open(
                SAVE_FILE,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            self.races = int(
                data.get(
                    "races",
                    0
                )
            )

            self.wins = int(
                data.get(
                    "wins",
                    0
                )
            )

            self.best_time = data.get(
                "best_time"
            )

            self.total_boosters = int(
                data.get(
                    "total_boosters",
                    0
                )
            )

            self.total_collisions = int(
                data.get(
                    "total_collisions",
                    0
                )
            )

        except Exception:
            pass

    def save(self):
        data = {
            "races": self.races,
            "wins": self.wins,
            "best_time": self.best_time,
            "total_boosters":
                self.total_boosters,
            "total_collisions":
                self.total_collisions
        }

        try:
            with open(
                SAVE_FILE,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2
                )
        except Exception:
            pass

    def record(
        self,
        won,
        elapsed,
        boosters,
        collisions
    ):
        self.races += 1

        if won:
            self.wins += 1

        if (
            won
            and (
                self.best_time is None
                or elapsed < self.best_time
            )
        ):
            self.best_time = elapsed

        self.total_boosters += boosters
        self.total_collisions += collisions

        self.save()


class Game:
    def __init__(self):
        self.running = True
        self.state = GameState.MENU

        self.road = Road()

        self.player = PlayerCar()

        self.ai = []

        colors = [
            RED,
            YELLOW,
            GREEN,
            PURPLE,
            ORANGE,
            PINK
        ]

        names = [
            "REDLINE",
            "VOLT",
            "NOVA",
            "SHADOW",
            "BLAZE",
            "PHANTOM"
        ]

        for index in range(6):
            self.ai.append(
                AICar(
                    index % LANES,
                    colors[index],
                    names[index],
                    0.35
                    + index * 0.1
                )
            )

        self.boosters = BoosterManager()

        self.particles = ParticleSystem()

        self.collision = CollisionSystem()

        self.profile = Profile()

        self.race_time = 0.0

        self.countdown = 0.0

        self.rank = 1

        self.lap = 1

        self.collisions = 0

        self.boosters_collected = 0

        self.notification = ""

        self.notification_timer = 0

        self.shake_amount = 0

        self.shake_timer = 0

        self.menu_time = 0

        self.settings_screen_shake = True

        self.button = pygame.Rect(
            WIDTH // 2 - 190,
            430,
            380,
            78
        )

        self.settings_button = pygame.Rect(
            WIDTH // 2 - 130,
            530,
            260,
            55
        )

    def player_lane(self):
        value = (
            self.player.x
            - ROAD_X
        ) / LANE_WIDTH

        return int(
            clamp(
                value,
                0,
                LANES - 1
            )
        )

    def reset(self):
        self.player.reset()

        self.race_time = 0

        self.lap = 1

        self.rank = 1

        self.collisions = 0

        self.boosters_collected = 0

        self.notification = ""

        self.notification_timer = 0

        self.shake_amount = 0

        self.shake_timer = 0

        self.boosters.reset()

        self.particles.items.clear()

        for index, ai in enumerate(
            self.ai
        ):
            ai.reset(
                450
                + index * 400
            )

        self.road.player_distance = 0

    def start_race(self):
        self.reset()

        self.profile.races += 1

        self.countdown = 3.0

        self.state = (
            GameState.COUNTDOWN
        )

    def begin_actual_race(self):
        self.state = GameState.RACING

        self.notification = "GO!"

        self.notification_timer = 1

    def resume(self):
        self.state = GameState.RACING

    def pause(self):
        self.state = GameState.PAUSED

    def current_rank(self):
        values = [
            self.player
        ] + self.ai

        values.sort(
            key=lambda car:
                car.distance,
            reverse=True
        )

        return (
            values.index(
                self.player
            )
            + 1
        )

    def update_countdown(self, dt):
        self.countdown -= dt

        if self.countdown <= 0:
            self.begin_actual_race()

    def update_race(self, dt):
        self.race_time += dt

        self.player.update(
            self,
            dt
        )

        for ai in self.ai:
            ai.update(
                self,
                dt
            )

        self.boosters.update(
            self,
            dt
        )

        self.collision.update(
            self
        )

        self.road.player_distance = (
            self.player.distance
        )

        self.road.update(
            self.player.speed,
            dt
        )

        self.rank = (
            self.current_rank()
        )

        self.lap = min(
            TOTAL_LAPS,
            int(
                self.player.distance
                / (
                    self.player.distance
                    / max(
                        1,
                        TOTAL_LAPS
                    )
                    if self.player.distance > 0
                    else 1
                )
            )
            + 1
        )

        if self.race_time >= RACE_TIME:
            self.state = (
                GameState.FINISHED
            )

            self.profile.record(
                self.rank == 1,
                self.race_time,
                self.boosters_collected,
                self.collisions
            )

        if self.player.health <= 0:
            self.state = (
                GameState.GAME_OVER
            )

            self.profile.record(
                False,
                self.race_time,
                self.boosters_collected,
                self.collisions
            )

        self.notification_timer = max(
            0,
            self.notification_timer
            - dt
        )

        self.shake_timer = max(
            0,
            self.shake_timer
            - dt
        )

    def update(self, dt):
        self.menu_time += dt

        self.particles.update(
            dt
        )

        if self.state == GameState.COUNTDOWN:
            self.update_countdown(
                dt
            )

        elif self.state == GameState.RACING:
            self.update_race(
                dt
            )

        elif self.state == GameState.MENU:
            self.notification_timer = max(
                0,
                self.notification_timer
                - dt
            )

    def event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if self.state == GameState.MENU:

            if (
                event.type
                == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                if self.button.collidepoint(
                    event.pos
                ):
                    self.start_race()

            if (
                event.type
                == pygame.KEYDOWN
            ):
                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                ):
                    self.start_race()

        elif self.state == GameState.RACING:

            if (
                event.type
                == pygame.KEYDOWN
            ):
                if event.key == pygame.K_p:
                    self.pause()

                elif event.key == pygame.K_r:
                    self.start_race()

                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU

        elif self.state == GameState.PAUSED:

            if (
                event.type
                == pygame.KEYDOWN
            ):
                if event.key == pygame.K_p:
                    self.resume()

                elif event.key == pygame.K_r:
                    self.start_race()

                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU

        elif self.state in (
            GameState.FINISHED,
            GameState.GAME_OVER
        ):

            if (
                event.type
                == pygame.KEYDOWN
            ):
                if event.key == pygame.K_r:
                    self.start_race()

                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU

            if (
                event.type
                == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                restart = pygame.Rect(
                    WIDTH // 2 - 180,
                    490,
                    360,
                    65
                )

                if restart.collidepoint(
                    event.pos
                ):
                    self.start_race()

    def draw_menu(self):
        screen.fill(
            (4, 7, 15)
        )

        for index in range(16):
            x = (
                index * 90
                + int(
                    math.sin(
                        self.menu_time
                        + index
                    )
                    * 25
                )
            )

            pygame.draw.line(
                screen,
                (10, 34, 49),
                (
                    x,
                    0
                ),
                (
                    x + 120,
                    HEIGHT
                ),
                1
            )

        for index in range(10):
            y = (
                index * 90
                + int(
                    self.menu_time
                    * 50
                )
            ) % HEIGHT

            pygame.draw.line(
                screen,
                (12, 28, 41),
                (
                    0,
                    y
                ),
                (
                    WIDTH,
                    y
                ),
                1
            )

        Glow.circle(
            WIDTH // 2,
            150,
            100,
            CYAN
        )

        draw_text(
            "NEON HIGHWAY",
            FONT70,
            CYAN,
            WIDTH // 2,
            150,
            True
        )

        draw_text(
            "REAL TIME RACING",
            FONT42,
            WHITE,
            WIDTH // 2,
            225,
            True
        )

        draw_text(
            "3 MINUTE RACE",
            FONT26,
            GREEN,
            WIDTH // 2,
            270,
            True
        )

        draw_text(
            "AUTOMATIC ACCELERATION",
            FONT22,
            WHITE,
            WIDTH // 2,
            315,
            True
        )

        draw_text(
            "A / D OR ARROWS  STEER",
            FONT18,
            WHITE,
            WIDTH // 2,
            350,
            True
        )

        draw_text(
            "F  FAST MODE",
            FONT18,
            ORANGE,
            WIDTH // 2,
            378,
            True
        )

        draw_text(
            "SPACE  NITRO",
            FONT18,
            CYAN,
            WIDTH // 2,
            405,
            True
        )

        mouse = pygame.mouse.get_pos()

        hover = self.button.collidepoint(
            mouse
        )

        button_color = (
            CYAN
            if hover
            else (
                18,
                70,
                120
            )
        )

        pygame.draw.rect(
            screen,
            button_color,
            self.button,
            border_radius=15
        )

        pygame.draw.rect(
            screen,
            WHITE,
            self.button,
            2,
            border_radius=15
        )

        draw_text(
            "START RACE",
            FONT32,
            BLACK,
            self.button.centerx,
            self.button.centery,
            True
        )

        draw_text(
            "ENTER OR CLICK TO START",
            FONT18,
            WHITE,
            WIDTH // 2,
            625,
            True
        )

        draw_text(
            f"RACES {self.profile.races}",
            FONT16,
            GRAY,
            25,
            HEIGHT - 25
        )

        draw_text(
            f"WINS {self.profile.wins}",
            FONT16,
            GREEN,
            125,
            HEIGHT - 25
        )

    def draw_countdown(self):
        self.draw_world()

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 80)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        if self.countdown > 2:
            value = "3"
        elif self.countdown > 1:
            value = "2"
        elif self.countdown > 0:
            value = "1"
        else:
            value = "GO!"

        color = (
            GREEN
            if value == "GO!"
            else YELLOW
        )

        draw_text(
            value,
            FONT70,
            color,
            WIDTH // 2,
            HEIGHT // 2,
            True
        )

    def draw_world(self):
        self.road.draw()

        self.boosters.draw(
            self.player.distance
        )

        visible_ai = sorted(
            self.ai,
            key=lambda car:
                car.y
        )

        for ai in visible_ai:
            ai.draw()

        self.player.draw()

        self.particles.draw()

        self.draw_hud()

    def draw_hud(self):
        pygame.draw.rect(
            screen,
            (7, 11, 18),
            (
                0,
                0,
                WIDTH,
                175
            )
        )

        draw_text(
            "HEALTH",
            FONT16,
            WHITE,
            25,
            20
        )

        pygame.draw.rect(
            screen,
            DARK,
            (
                25,
                47,
                250,
                20
            ),
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            RED,
            (
                25,
                47,
                int(
                    250
                    * self.player.health
                    / 100
                ),
                20
            ),
            border_radius=6
        )

        draw_text(
            "NITRO",
            FONT16,
            WHITE,
            25,
            82
        )

        pygame.draw.rect(
            screen,
            DARK,
            (
                25,
                109,
                250,
                20
            ),
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            CYAN,
            (
                25,
                109,
                int(
                    250
                    * self.player.nitro_amount
                    / 100
                ),
                20
            ),
            border_radius=6
        )

        draw_text(
            f"{int(self.player.speed)} KM/H",
            FONT32,
            (
                ORANGE
                if self.player.fast
                else CYAN
                if self.player.nitro
                else WHITE
            ),
            WIDTH - 280,
            20
        )

        mode = (
            "NITRO"
            if self.player.nitro
            else "BOOST"
            if self.player.boost_timer > 0
            else "FAST"
            if self.player.fast
            else "AUTO"
        )

        mode_color = (
            CYAN
            if mode == "NITRO"
            else PURPLE
            if mode == "BOOST"
            else ORANGE
            if mode == "FAST"
            else GREEN
        )

        draw_text(
            mode,
            FONT22 if False else FONT22,
            mode_color,
            WIDTH - 280,
            62
        )

        lap = min(
            TOTAL_LAPS,
            int(
                self.race_time
                / (
                    RACE_TIME
                    / TOTAL_LAPS
                )
            )
            + 1
        )

        draw_text(
            f"LAP {lap}/{TOTAL_LAPS}",
            FONT26,
            CYAN,
            WIDTH - 280,
            96
        )

        draw_text(
            f"POSITION {self.rank}/{len(self.ai)+1}",
            FONT18,
            YELLOW,
            WIDTH - 280,
            132
        )

        time_ratio = clamp(
            self.race_time
            / RACE_TIME,
            0,
            1
        )

        pygame.draw.rect(
            screen,
            DARK,
            (
                380,
                30,
                400,
                12
            ),
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            GREEN,
            (
                380,
                30,
                int(
                    400
                    * time_ratio
                ),
                12
            ),
            border_radius=5
        )

        draw_text(
            format_time(
                self.race_time
            ),
            FONT22,
            WHITE,
            WIDTH // 2,
            60,
            True
        )

        draw_text(
            "F = FAST",
            FONT18,
            ORANGE,
            WIDTH // 2,
            94,
            True
        )

        draw_text(
            "SPACE = NITRO",
            FONT18,
            CYAN,
            WIDTH // 2,
            122,
            True
        )

        draw_text(
            "A/D = STEER",
            FONT18,
            WHITE,
            WIDTH // 2,
            148,
            True
        )

        if self.notification_timer > 0:
            draw_text(
                self.notification,
                FONT26,
                YELLOW,
                WIDTH // 2,
                195,
                True
            )

    def draw_pause(self):
        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 185)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        draw_text(
            "PAUSED",
            FONT56,
            YELLOW,
            WIDTH // 2,
            260,
            True
        )

        draw_text(
            "P  RESUME",
            FONT24,
            WHITE,
            WIDTH // 2,
            340,
            True
        )

        draw_text(
            "R  RESTART",
            FONT24,
            CYAN,
            WIDTH // 2,
            385,
            True
        )

        draw_text(
            "ESC  MENU",
            FONT24,
            PURPLE,
            WIDTH // 2,
            430,
            True
        )

    def draw_result(self):
        self.draw_world()

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 0, 190)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        if self.state == GameState.FINISHED:
            title = "RACE FINISHED"
            color = (
                GREEN
                if self.rank == 1
                else YELLOW
            )
        else:
            title = "CAR DESTROYED"
            color = RED

        draw_text(
            title,
            FONT56,
            color,
            WIDTH // 2,
            175,
            True
        )

        draw_text(
            f"POSITION {self.rank}/{len(self.ai)+1}",
            FONT32,
            WHITE,
            WIDTH // 2,
            255,
            True
        )

        draw_text(
            f"TIME {format_time(self.race_time)}",
            FONT26,
            CYAN,
            WIDTH // 2,
            305,
            True
        )

        draw_text(
            f"BOOSTERS {self.boosters_collected}",
            FONT22,
            YELLOW,
            WIDTH // 2,
            345,
            True
        )

        draw_text(
            f"COLLISIONS {self.collisions}",
            FONT22,
            RED,
            WIDTH // 2,
            380,
            True
        )

        draw_text(
            f"CAREER WINS {self.profile.wins}",
            FONT22,
            GREEN,
            WIDTH // 2,
            415,
            True
        )

        restart = pygame.Rect(
            WIDTH // 2 - 180,
            490,
            360,
            65
        )

        pygame.draw.rect(
            screen,
            CYAN,
            restart,
            border_radius=12
        )

        draw_text(
            "RACE AGAIN",
            FONT26,
            BLACK,
            restart.centerx,
            restart.centery,
            True
        )

        draw_text(
            "R = RESTART     ESC = MENU",
            FONT18,
            WHITE,
            WIDTH // 2,
            585,
            True
        )

    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()

        elif self.state == GameState.COUNTDOWN:
            self.draw_countdown()

        elif self.state == GameState.RACING:
            self.draw_world()

        elif self.state == GameState.PAUSED:
            self.draw_world()
            self.draw_pause()

        elif self.state in (
            GameState.FINISHED,
            GameState.GAME_OVER
        ):
            self.draw_result()

        if self.shake_timer > 0:
            intensity = int(
                self.shake_amount
                * (
                    self.shake_timer
                    / 0.25
                )
            )

            if intensity > 0:
                overlay = pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )

                overlay.fill(
                    (
                        255,
                        255,
                        255,
                        min(
                            30,
                            intensity
                        )
                    )
                )

                screen.blit(
                    overlay,
                    (
                        random.randint(
                            -intensity,
                            intensity
                        ),
                        random.randint(
                            -intensity,
                            intensity
                        )
                    )
                )

        pygame.display.flip()

    def run(self):
        while self.running:

            dt = (
                clock.tick(FPS)
                / 1000.0
            )

            dt = min(
                dt,
                0.025
            )

            for event in pygame.event.get():
                self.event(event)

            self.update(dt)
            self.draw()

        self.profile.save()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
