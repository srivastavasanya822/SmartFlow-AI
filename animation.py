
import random
import sys
import pygame

# ============================================================
# SMARTFLOW AI - PERSON 1
# Animated Traffic Intersection
# Python 3.13 + Pygame
# ============================================================

pygame.init()

WIDTH = 1100
HEIGHT = 760
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SmartFlow AI - Intelligent Traffic Signal")
clock = pygame.time.Clock()

# Colours
WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
ROAD = (48, 50, 54)
DARK = (25, 28, 32)
YELLOW = (255, 205, 40)
GREEN = (40, 210, 100)
RED = (240, 65, 65)
BLUE = (55, 145, 255)
ORANGE = (255, 145, 45)
CYAN = (65, 220, 235)

CENTER_X = WIDTH // 2
CENTER_Y = 390
ROAD_WIDTH = 260

font_small = pygame.font.SysFont("arial", 16)
font_medium = pygame.font.SysFont("arial", 20)
font_large = pygame.font.SysFont("arial", 29, bold=True)
font_title = pygame.font.SysFont("arial", 35, bold=True)

# Signal timing
MIN_GREEN = 8.0
MAX_GREEN = 18.0
YELLOW_TIME = 2.0
ALL_RED_TIME = 1.0


# ============================================================
# VEHICLE
# ============================================================

class Vehicle:

    def __init__(self, direction, vehicle_id, emergency=False):
        self.direction = direction
        self.vehicle_id = vehicle_id
        self.emergency = emergency
        self.speed = random.uniform(1.4, 2.0)
        self.crossed = False

        self.color = ORANGE if emergency else random.choice([
            BLUE, GREEN, RED, YELLOW, CYAN, WHITE
        ])

        if direction == "N":
            self.x = CENTER_X - 45
            self.y = -35
        elif direction == "S":
            self.x = CENTER_X + 45
            self.y = HEIGHT + 35
        elif direction == "E":
            self.x = WIDTH + 35
            self.y = CENTER_Y + 45
        else:  # W
            self.x = -35
            self.y = CENTER_Y - 45

    def stop_coordinate(self):
        if self.direction == "N":
            return CENTER_Y - ROAD_WIDTH // 2 - 20
        if self.direction == "S":
            return CENTER_Y + ROAD_WIDTH // 2 + 20
        if self.direction == "E":
            return CENTER_X + ROAD_WIDTH // 2 + 20
        return CENTER_X - ROAD_WIDTH // 2 - 20

    def at_stop_line(self):
        stop = self.stop_coordinate()

        if self.direction == "N":
            return self.y >= stop
        if self.direction == "S":
            return self.y <= stop
        if self.direction == "E":
            return self.x <= stop
        return self.x >= stop

    def update(self, green_directions, vehicles):
        stop = self.stop_coordinate()

        # Stop at the signal when the light is red.
        if not self.crossed and self.at_stop_line():
            if self.direction not in green_directions:
                return
            self.crossed = True

        # Simple same-lane following distance.
        for other in vehicles:
            if other is self or other.direction != self.direction:
                continue

            if self.direction == "N":
                if other.y > self.y and other.y - self.y < 43:
                    return
            elif self.direction == "S":
                if other.y < self.y and self.y - other.y < 43:
                    return
            elif self.direction == "E":
                if other.x < self.x and self.x - other.x < 43:
                    return
            elif self.direction == "W":
                if other.x > self.x and other.x - self.x < 43:
                    return

        # Move the vehicle.
        if self.direction == "N":
            self.y += self.speed
        elif self.direction == "S":
            self.y -= self.speed
        elif self.direction == "E":
            self.x -= self.speed
        else:
            self.x += self.speed

    def outside_screen(self):
        margin = 80
        return (
            self.x < -margin or self.x > WIDTH + margin
            or self.y < -margin or self.y > HEIGHT + margin
        )

    def draw(self, surface):
        # Vehicle body
        if self.direction in ("N", "S"):
            rect = pygame.Rect(
                int(self.x - 12), int(self.y - 18), 24, 36
            )
        else:
            rect = pygame.Rect(
                int(self.x - 18), int(self.y - 12), 36, 24
            )

        pygame.draw.rect(surface, self.color, rect, border_radius=5)

        # Windows
        if self.direction in ("N", "S"):
            window = pygame.Rect(rect.x + 4, rect.y + 7, 16, 9)
        else:
            window = pygame.Rect(rect.x + 7, rect.y + 4, 9, 16)

        pygame.draw.rect(surface, DARK, window, border_radius=2)

        # Emergency marking
        if self.emergency:
            pygame.draw.circle(
                surface, WHITE, (int(self.x), int(self.y)), 4
            )


# ============================================================
# TRAFFIC SIMULATION
# ============================================================

class TrafficSimulation:

    def __init__(self):
        self.vehicles = []
        self.next_id = 1

        self.elapsed = 0.0
        self.spawn_timer = 0.0
        self.phase_timer = 0.0

        self.phase = "NS_GREEN"
        self.last_green_was_ns = True

        self.paused = False
        self.fixed_mode = False

        self.emergency_requested = False
        self.emergency_direction = "N"
        self.emergency_spawned = False

        self.total_spawned = 0
        self.total_passed = 0
        self.phase_changes = 0

        self.queues = {"N": 0, "S": 0, "E": 0, "W": 0}
        self.waiting_seconds = {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}

        for _ in range(8):
            self.spawn_vehicle()

    def spawn_vehicle(self, direction=None, emergency=False):
        if direction is None:
            direction = random.choice(["N", "S", "E", "W"])

        vehicle = Vehicle(direction, self.next_id, emergency)
        self.next_id += 1
        self.vehicles.append(vehicle)
        self.total_spawned += 1

    def request_emergency(self):
        if self.emergency_requested:
            return

        self.emergency_requested = True
        self.emergency_spawned = False
        self.emergency_direction = random.choice(["N", "S", "E", "W"])

    def green_directions(self):
        if self.phase == "NS_GREEN":
            return ["N", "S"]
        if self.phase == "EW_GREEN":
            return ["E", "W"]
        return []

    def calculate_queues(self):
        counts = {"N": 0, "S": 0, "E": 0, "W": 0}

        for vehicle in self.vehicles:
            if not vehicle.crossed and vehicle.at_stop_line():
                counts[vehicle.direction] += 1

        self.queues = counts

    def change_to_yellow(self):
        self.phase = "YELLOW"
        self.phase_timer = 0.0
        self.phase_changes += 1

    def update_signal(self, dt):
        self.phase_timer += dt

        if self.phase in ("NS_GREEN", "EW_GREEN"):
            green = self.green_directions()

            emergency_needs_green = (
                self.emergency_requested
                and self.emergency_direction not in green
            )

            if self.fixed_mode:
                if self.phase_timer >= 10:
                    self.change_to_yellow()
                return

            self.calculate_queues()

            ns_queue = self.queues["N"] + self.queues["S"]
            ew_queue = self.queues["E"] + self.queues["W"]

            should_switch = False

            if emergency_needs_green and self.phase_timer >= MIN_GREEN:
                should_switch = True
            elif self.phase_timer >= MAX_GREEN:
                should_switch = True
            elif self.phase_timer >= MIN_GREEN:
                if self.phase == "NS_GREEN" and ew_queue > ns_queue + 2:
                    should_switch = True
                elif self.phase == "EW_GREEN" and ns_queue > ew_queue + 2:
                    should_switch = True

            if should_switch:
                self.change_to_yellow()

        elif self.phase == "YELLOW":
            if self.phase_timer >= YELLOW_TIME:
                self.phase = "ALL_RED"
                self.phase_timer = 0.0

        elif self.phase == "ALL_RED":
            if self.phase_timer >= ALL_RED_TIME:
                if self.emergency_requested:
                    if self.emergency_direction in ("N", "S"):
                        self.phase = "NS_GREEN"
                    else:
                        self.phase = "EW_GREEN"
                    self.emergency_requested = False
                else:
                    if self.last_green_was_ns:
                        self.phase = "EW_GREEN"
                    else:
                        self.phase = "NS_GREEN"

                self.last_green_was_ns = (self.phase == "NS_GREEN")
                self.phase_timer = 0.0

    def reset(self):
        fixed = self.fixed_mode
        self.__init__()
        self.fixed_mode = fixed

    def update(self, dt):
        if self.paused:
            return

        self.elapsed += dt
        self.spawn_timer += dt

        # Spawn normal traffic.
        if self.spawn_timer >= 1.3:
            self.spawn_timer = 0.0
            self.spawn_vehicle()

            if random.random() < 0.25:
                self.spawn_vehicle()

        # Spawn one emergency vehicle per request.
        if self.emergency_requested and not self.emergency_spawned:
            self.spawn_vehicle(
                direction=self.emergency_direction,
                emergency=True
            )
            self.emergency_spawned = True

        # Signal changes happen in one place only.
        self.update_signal(dt)

        green = self.green_directions()

        for vehicle in list(self.vehicles):
            vehicle.update(green, self.vehicles)

            if vehicle.outside_screen():
                self.vehicles.remove(vehicle)
                if vehicle.crossed:
                    self.total_passed += 1

        self.calculate_queues()

        # Approximate cumulative queue waiting.
        for direction in ("N", "S", "E", "W"):
            if direction not in green:
                self.waiting_seconds[direction] += self.queues[direction] * dt


# ============================================================
# DRAWING FUNCTIONS
# ============================================================

def draw_road():
    screen.fill((32, 105, 68))

    # Main roads
    pygame.draw.rect(
        screen, ROAD,
        (0, CENTER_Y - ROAD_WIDTH // 2, WIDTH, ROAD_WIDTH)
    )
    pygame.draw.rect(
        screen, ROAD,
        (CENTER_X - ROAD_WIDTH // 2, 0, ROAD_WIDTH, HEIGHT)
    )

    # Road boundaries
    pygame.draw.line(
        screen, WHITE,
        (0, CENTER_Y - ROAD_WIDTH // 2),
        (WIDTH, CENTER_Y - ROAD_WIDTH // 2), 3
    )
    pygame.draw.line(
        screen, WHITE,
        (0, CENTER_Y + ROAD_WIDTH // 2),
        (WIDTH, CENTER_Y + ROAD_WIDTH // 2), 3
    )
    pygame.draw.line(
        screen, WHITE,
        (CENTER_X - ROAD_WIDTH // 2, 0),
        (CENTER_X - ROAD_WIDTH // 2, HEIGHT), 3
    )
    pygame.draw.line(
        screen, WHITE,
        (CENTER_X + ROAD_WIDTH // 2, 0),
        (CENTER_X + ROAD_WIDTH // 2, HEIGHT), 3
    )

    # Dashed lane markings outside the junction
    for x in range(0, WIDTH, 42):
        if not CENTER_X - 145 <= x <= CENTER_X + 145:
            pygame.draw.line(
                screen, YELLOW,
                (x, CENTER_Y), (x + 20, CENTER_Y), 2
            )

    for y in range(0, HEIGHT, 42):
        if not CENTER_Y - 145 <= y <= CENTER_Y + 145:
            pygame.draw.line(
                screen, YELLOW,
                (CENTER_X, y), (CENTER_X, y + 20), 2
            )


def draw_signal(x, y, direction, simulation):
    pygame.draw.rect(
        screen, DARK, (x, y, 42, 112), border_radius=8
    )

    active = simulation.phase
    if active == "YELLOW":
        active_colour = YELLOW
    elif active == "ALL_RED":
        active_colour = RED
    elif direction in simulation.green_directions():
        active_colour = GREEN
    else:
        active_colour = RED

    colours = [RED, YELLOW, GREEN]
    positions = [(x + 21, y + 20), (x + 21, y + 55), (x + 21, y + 90)]

    for colour, position in zip(colours, positions):
        lamp_colour = colour if colour == active_colour else (55, 55, 55)
        pygame.draw.circle(screen, lamp_colour, position, 12)

    label = font_small.render(direction, True, WHITE)
    screen.blit(label, (x + 14, y + 114))


def draw_dashboard(simulation):
    panel = pygame.Rect(15, 15, 335, 195)
    pygame.draw.rect(screen, DARK, panel, border_radius=12)
    pygame.draw.rect(screen, CYAN, panel, 2, border_radius=12)

    screen.blit(
        font_large.render("SMARTFLOW AI", True, CYAN), (30, 24)
    )

    mode = "FIXED-TIME MODE" if simulation.fixed_mode else "ADAPTIVE DEMO MODE"
    screen.blit(font_small.render(mode, True, YELLOW), (30, 61))

    screen.blit(
        font_medium.render(f"Signal: {simulation.phase}", True, WHITE),
        (30, 88)
    )
    screen.blit(
        font_medium.render(f"Vehicles: {len(simulation.vehicles)}", True, WHITE),
        (30, 116)
    )
    screen.blit(
        font_medium.render(f"Vehicles passed: {simulation.total_passed}", True, WHITE),
        (30, 144)
    )
    screen.blit(
        font_medium.render(f"Simulation time: {int(simulation.elapsed)} s", True, WHITE),
        (30, 172)
    )


def draw_queue_panel(simulation):
    panel = pygame.Rect(WIDTH - 245, 15, 230, 175)
    pygame.draw.rect(screen, DARK, panel, border_radius=12)

    screen.blit(
        font_medium.render("TRAFFIC QUEUES", True, YELLOW),
        (WIDTH - 230, 27)
    )

    for index, direction in enumerate(("N", "S", "E", "W")):
        text = f"{direction}: {simulation.queues[direction]} vehicles"
        screen.blit(
            font_medium.render(text, True, WHITE),
            (WIDTH - 230, 60 + index * 29)
        )


def draw_controls(simulation):
    panel = pygame.Rect(15, HEIGHT - 82, WIDTH - 30, 65)
    pygame.draw.rect(screen, DARK, panel, border_radius=10)

    controls = [
        "SPACE: Pause",
        "E: Emergency",
        "F: Fixed-time",
        "A: Adaptive",
        "R: Reset",
        "ESC: Exit"
    ]

    x = 28
    for item in controls:
        rendered = font_small.render(item, True, WHITE)
        screen.blit(rendered, (x, HEIGHT - 57))
        x += rendered.get_width() + 24


def draw_phase_indicator(simulation):
    text = font_medium.render(
        f"Current phase: {simulation.phase}", True, WHITE
    )
    rect = text.get_rect(center=(CENTER_X, 24))
    pygame.draw.rect(screen, DARK, rect.inflate(24, 14), border_radius=8)
    screen.blit(text, rect)


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    simulation = TrafficSimulation()
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    simulation.paused = not simulation.paused

                elif event.key == pygame.K_e:
                    simulation.request_emergency()

                elif event.key == pygame.K_f:
                    simulation.fixed_mode = True
                    simulation.phase = "NS_GREEN"
                    simulation.phase_timer = 0.0
                    simulation.last_green_was_ns = True

                elif event.key == pygame.K_a:
                    simulation.fixed_mode = False
                    simulation.phase = "NS_GREEN"
                    simulation.phase_timer = 0.0
                    simulation.last_green_was_ns = True

                elif event.key == pygame.K_r:
                    simulation.reset()

        simulation.update(dt)

        draw_road()

        # Traffic lights around the junction
        draw_signal(CENTER_X - 165, CENTER_Y - 180, "N", simulation)
        draw_signal(CENTER_X + 125, CENTER_Y + 65, "S", simulation)
        draw_signal(CENTER_X + 135, CENTER_Y - 180, "E", simulation)
        draw_signal(CENTER_X - 180, CENTER_Y + 65, "W", simulation)

        for vehicle in simulation.vehicles:
            vehicle.draw(screen)

        draw_dashboard(simulation)
        draw_queue_panel(simulation)
        draw_phase_indicator(simulation)
        draw_controls(simulation)

        if simulation.paused:
            pause_text = font_title.render("SIMULATION PAUSED", True, YELLOW)
            screen.blit(
                pause_text,
                pause_text.get_rect(center=(CENTER_X, HEIGHT - 115))
            )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
