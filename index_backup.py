import pygame
import random
import math
import sys
from abc import ABC, abstractmethod

WIDTH = 1280
HEIGHT = 720
FPS = 120
ROAD_TOP = 120
GROUND = 620

WHITE = (245, 245, 245)
BLACK = (7, 9, 14)
ROAD = (48, 50, 58)
ROAD_LINE = (220, 220, 220)
GRASS = (18, 90, 52)
BLUE = (40, 170, 255)
RED = (240, 65, 70)
YELLOW = (255, 210, 50)
CYAN = (30, 240, 230)


class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def copy(self):
        return Vector2(self.x, self.y)

    def add(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def scale(self, value):
        self.x *= value
        self.y *= value
        return self

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)


class GameObject(ABC):
    @abstractmethod
    def update(self, game, dt):
        pass

    @abstractmethod
    def draw(self, screen, camera_y):
        pass


class Particle(GameObject):
    def __init__(self, x, y, color):
        self.position = Vector2(x, y)
        self.velocity = Vector2(random.uniform(-180, 180), random.uniform(-220, 20))
        self.life = random.uniform(0.2, 0.55)
        self.color = color
        self.radius = random.randint(2, 5)

    def update(self, game, dt):
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.velocity.y += 420 * dt
        self.life -= dt

    def draw(self, screen, camera_y):
        if self.life <= 0:
            return
        r = max(1, int(self.radius * self.life / 0.55))
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y - camera_y)), r)


class SparkEffect(GameObject):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 0.22
        self.radius = 8

    def update(self, game, dt):
        self.radius += 420 * dt
        self.life -= dt

    def draw(self, screen, camera_y):
        if self.life > 0:
            pygame.draw.circle(
                screen,
                YELLOW,
                (int(self.x), int(self.y - camera_y)),
                int(self.radius),
                max(1, int(self.life * 24)),
            )


class Road:
    def __init__(self):
        self.center = WIDTH / 2
        self.width = 800
        self.lane_width = self.width / 4
        self.scroll = 0.0
        self.decor = [
            (random.choice([-1, 1]), y, random.randint(16, 38))
            for y in range(-4000, 30000, 170)
        ]

    def update(self, speed, dt):
        self.scroll += speed * dt

    def lane_x(self, lane):
        return self.center + lane * self.lane_width

    def draw(self, screen, camera_y):
        screen.fill(GRASS)
        left = int(self.center - self.width / 2)
        pygame.draw.rect(screen, ROAD, (left, 0, self.width, HEIGHT))
        pygame.draw.line(screen, ROAD_LINE, (left, 0), (left, HEIGHT), 8)
        pygame.draw.line(screen, ROAD_LINE, (left + self.width, 0), (left + self.width, HEIGHT), 8)

        dash_offset = self.scroll % 100
        for lane in (-1.5, -0.5, 0.5, 1.5):
            x = int(self.lane_x(lane))
            y = -100 + dash_offset
            while y < HEIGHT + 100:
                pygame.draw.rect(screen, ROAD_LINE, (x - 3, int(y), 6, 48), border_radius=3)
                y += 100

        for side, world_y, size in self.decor:
            y = world_y - camera_y
            if -100 <= y <= HEIGHT + 100:
                x = left - size - 8 if side < 0 else left + self.width + size + 8
                pygame.draw.rect(
                    screen,
                    (25, 125, 65),
                    (int(x - size), int(y - size), size * 2, size * 2),
                    border_radius=6,
                )


class Car(GameObject):
    def __init__(self, game, x, y, color, name):
        self.game = game
        self.position = Vector2(x, y)
        self.velocity = Vector2()
        self.color = color
        self.name = name
        self.width = 54
        self.height = 102
        self.max_speed = 760.0
        self.acceleration = 680.0
        self.brake_power = 1150.0
        self.steering = 470.0
        self.health = 100.0
        self.nitro = 100.0
        self.damage_flash = 0.0
        self.boosting = False

    def rect(self, camera_y=0):
        return pygame.Rect(
            int(self.position.x - self.width / 2),
            int(self.position.y - self.height / 2 - camera_y),
            self.width,
            self.height,
        )

    def accelerate(self, dt):
        self.velocity.y = min(self.max_speed, self.velocity.y + self.acceleration * dt)

    def brake(self, dt):
        self.velocity.y = max(0.0, self.velocity.y - self.brake_power * dt)

    def steer(self, direction, dt):
        grip = 0.72 + 0.65 * min(1.0, self.velocity.y / self.max_speed)
        self.position.x += direction * self.steering * grip * dt
        left = self.game.road.center - self.game.road.width / 2 + 32
        right = self.game.road.center + self.game.road.width / 2 - 32
        self.position.x = max(left, min(right, self.position.x))

    def boost(self, dt):
        if self.nitro > 0:
            self.boosting = True
            self.nitro = max(0.0, self.nitro - 40.0 * dt)
            self.velocity.y = min(self.max_speed * 1.5, self.velocity.y + 1300 * dt)

    def take_damage(self, amount):
        self.health = max(0.0, self.health - amount)
        self.damage_flash = 0.12

    def update_common(self, dt):
        self.position.y -= self.velocity.y * dt
        self.velocity.y *= max(0.0, 1.0 - 0.55 * dt)
        self.nitro = min(100.0, self.nitro + 5.0 * dt)
        if self.damage_flash > 0:
            self.damage_flash -= dt
        self.boosting = False

    def draw(self, screen, camera_y):
        rect = self.rect(camera_y)
        color = WHITE if self.damage_flash > 0 else self.color
        shadow = rect.inflate(10, 10)
        pygame.draw.rect(screen, (12, 12, 18), shadow, border_radius=14)
        pygame.draw.rect(screen, color, rect, border_radius=12)
        cabin = pygame.Rect(rect.x + 10, rect.y + 13, rect.w - 20, 38)
        pygame.draw.rect(screen, (25, 40, 65), cabin, border_radius=10)
        pygame.draw.line(screen, (190, 220, 240), cabin.midleft, cabin.midright, 2)
        pygame.draw.rect(screen, WHITE, (rect.x + 7, rect.bottom - 18, 11, 6), border_radius=3)
        pygame.draw.rect(screen, WHITE, (rect.right - 18, rect.bottom - 18, 11, 6), border_radius=3)
        if self.boosting:
            for dx in (-13, 13):
                pygame.draw.polygon(
                    screen,
                    YELLOW,
                    [
                        (rect.centerx + dx, rect.bottom),
                        (rect.centerx + dx - 8, rect.bottom + 28),
                        (rect.centerx + dx + 8, rect.bottom + 28),
                    ],
                )


class PlayerCar(Car):
    def __init__(self, game):
        super().__init__(game, WIDTH / 2 - 100, 550, BLUE, "PLAYER")

    def update(self, game, dt):
        keys = pygame.key.get_pressed()
        self.accelerate(dt)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.brake(dt)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.steer(-1, dt)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.steer(1, dt)
        if keys[pygame.K_SPACE]:
            self.boost(dt)
        self.update_common(dt)


class AICar(Car):
    def __init__(self, game, x, y, lane, color):
        super().__init__(game, x, y, color, "AI")
        self.lane = lane
        self.change_timer = random.uniform(1.0, 3.0)

    def update(self, game, dt):
        self.accelerate(dt)
        self.change_timer -= dt
        if self.change_timer <= 0:
            self.lane = random.choice([-1.5, -0.5, 0.5, 1.5])
            self.change_timer = random.uniform(1.2, 3.8)
        desired = game.road.lane_x(self.lane)
        direction = 0
        if self.position.x < desired - 12:
            direction = 1
        elif self.position.x > desired + 12:
            direction = -1
        if direction:
            self.steer(direction, dt)
        self.update_common(dt)


class CollisionSystem:
    def handle(self, game):
        cars = [game.player] + game.ai_cars
        for i in range(len(cars)):
            for j in range(i + 1, len(cars)):
                a = cars[i]
                b = cars[j]
                if a.rect(game.camera_y).colliderect(b.rect(game.camera_y)):
                    dx = a.position.x - b.position.x
                    push = 24 if dx >= 0 else -24
                    a.position.x += push
                    b.position.x -= push
                    a.velocity.y *= 0.86
                    b.velocity.y *= 0.86
                    a.take_damage(5)
                    b.take_damage(5)
                    game.effects.append(
                        SparkEffect((a.position.x + b.position.x) / 2, (a.position.y + b.position.y) / 2)
                    )
                    game.spawn_particles((a.position.x + b.position.x) / 2, (a.position.y + b.position.y) / 2, YELLOW, 10)


class RaceManager:
    def __init__(self):
        self.distance = 0.0
        self.target_distance = 24000.0
        self.lap = 1
        self.total_laps = 3
        self.time = 0.0
        self.finished = False

    def update(self, game, dt):
        self.time += dt
        self.distance += max(0.0, game.player.velocity.y) * dt
        self.lap = min(
            self.total_laps,
            int(self.distance / (self.target_distance / self.total_laps)) + 1,
        )
        if self.distance >= self.target_distance:
            self.finished = True

    def ratio(self):
        return min(1.0, self.distance / self.target_distance)


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.small = pygame.font.SysFont("arial", 17, bold=True)
        self.big = pygame.font.SysFont("arial", 48, bold=True)

    def text(self, screen, value, x, y, color=WHITE, center=False, big=False):
        font = self.big if big else self.font
        surface = font.render(str(value), True, color)
        rect = surface.get_rect()
        rect.center = (x, y) if center else (x + rect.width / 2, y + rect.height / 2)
        screen.blit(surface, rect)

    def bar(self, screen, x, y, width, height, value, maximum, color):
        pygame.draw.rect(screen, (27, 28, 36), (x, y, width, height), border_radius=7)
        ratio = max(0.0, min(1.0, value / maximum))
        pygame.draw.rect(screen, color, (x, y, int(width * ratio), height), border_radius=7)
        pygame.draw.rect(screen, WHITE, (x, y, width, height), 2, border_radius=7)

    def draw(self, screen, game):
        self.bar(screen, 28, 25, 340, 24, game.player.health, 100, BLUE)
        self.bar(screen, 28, 60, 250, 12, game.player.nitro, 100, CYAN)
        self.bar(screen, WIDTH - 368, 25, 340, 24, game.enemy_target_health(), 100, RED)
        self.text(screen, "PLAYER", 28, 2, BLUE)
        self.text(screen, "CPU", WIDTH - 52, 2, RED)
        self.text(screen, f"Speed {int(game.player.velocity.y)}", 30, 90, WHITE)
        self.text(screen, f"Lap {game.race.lap}/{game.race.total_laps}", WIDTH // 2, 34, WHITE, True)
        self.text(screen, f"{game.race.time:06.1f}s", WIDTH // 2, 65, YELLOW, True)
        self.text(
            screen,
            "WASD / Arrows Drive    SPACE Nitro    P Pause    R Restart",
            WIDTH // 2,
            HEIGHT - 24,
            WHITE,
            True,
        )
        if game.paused:
            self.text(screen, "PAUSED", WIDTH // 2, HEIGHT // 2, WHITE, True, True)
        elif game.game_over:
            self.text(screen, "FINISH", WIDTH // 2, HEIGHT // 2 - 35, YELLOW, True, True)
            self.text(screen, "Press R to race again", WIDTH // 2, HEIGHT // 2 + 25, WHITE, True)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Neon Highway - Python OOP Racing")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        self.road = Road()
        self.player = PlayerCar(self)
        colors = [RED, YELLOW, (170, 80, 255), (255, 130, 55), (70, 230, 140)]
        self.ai_cars = [
            AICar(self, self.road.lane_x(random.choice([-1.5, -0.5, 0.5, 1.5])), 100 + i * 220, random.choice([-1.5, -0.5, 0.5, 1.5]), colors[i])
            for i in range(5)
        ]
        self.particles = []
        self.effects = []
        self.collision = CollisionSystem()
        self.race = RaceManager()
        self.hud = HUD()
        self.camera_y = 0.0
        self.paused = False
        self.game_over = False
        self.running = True

    def enemy_target_health(self):
        nearest = min(self.ai_cars, key=lambda car: abs(car.position.y - self.player.position.y))
        return nearest.health

    def spawn_particles(self, x, y, color, count=4):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def reset(self):
        self.player = PlayerCar(self)
        colors = [RED, YELLOW, (170, 80, 255), (255, 130, 55), (70, 230, 140)]
        self.ai_cars = [
            AICar(
                self,
                self.road.lane_x(random.choice([-1.5, -0.5, 0.5, 1.5])),
                100 + i * 220,
                random.choice([-1.5, -0.5, 0.5, 1.5]),
                colors[i],
            )
            for i in range(5)
        ]
        self.particles.clear()
        self.effects.clear()
        self.race = RaceManager()
        self.camera_y = 0.0
        self.paused = False
        self.game_over = False

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset()

    def update_effects(self, dt):
        for item in self.particles:
            item.update(self, dt)
        for item in self.effects:
            item.update(self, dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.effects = [e for e in self.effects if e.life > 0]

    def update(self, dt):
        if self.paused or self.game_over:
            return
        self.player.update(self, dt)
        for car in self.ai_cars:
            car.update(self, dt)
        self.road.update(self.player.velocity.y, dt)
        self.collision.handle(self)
        self.race.update(self, dt)
        self.camera_y = self.player.position.y - 520
        self.update_effects(dt)
        if self.player.health <= 0 or self.race.finished:
            self.game_over = True

    def draw(self):
        self.road.draw(self.screen, self.camera_y)
        for particle in self.particles:
            particle.draw(self.screen, self.camera_y)
        for effect in self.effects:
            effect.draw(self.screen, self.camera_y)
        ordered = sorted(self.ai_cars, key=lambda c: c.position.y)
        for car in ordered:
            car.draw(self.screen, self.camera_y)
        self.player.draw(self.screen, self.camera_y)
        self.hud.draw(self.screen, self)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.03)
            self.events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()

