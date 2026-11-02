
import pygame
import random
import sys
import math

pygame.init()

# ==========================================================
# SMARTFLOW AI - MODERN CITY TRAFFIC SIMULATION
# Realistic-style cars, mall, trees, footpaths and bypass
# ==========================================================

WIDTH, HEIGHT = 1200, 800
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SMARTFLOW AI - Smart City Traffic System")
clock = pygame.time.Clock()

# ---------------- COLORS ----------------

GRASS = (91, 145, 83)
GRASS_DARK = (69, 120, 68)
ROAD = (53, 56, 61)
ROAD_EDGE = (115, 117, 119)
SIDEWALK = (174, 174, 165)
WHITE = (245, 245, 235)
YELLOW = (255, 210, 45)
ORANGE = (255, 135, 20)
RED = (230, 45, 45)
GREEN = (35, 220, 85)
BLACK = (20, 22, 24)
GLASS = (115, 190, 210)

CX, CY = WIDTH // 2, HEIGHT // 2
ROAD_W = 240

CAR_W = 20
CAR_L = 34
CAR_GAP = 15

GREEN_TIME = 30.0
YELLOW_TIME = 2.0
ALL_RED_TIME = 1.0

DIRECTIONS = ("N", "S", "E", "W")

AXIS = {
    "N": "NS",
    "S": "NS",
    "E": "EW",
    "W": "EW"
}

STOP_DISTANCE = {
    "N": CY - ROAD_W // 2,
    "S": HEIGHT - (CY + ROAD_W // 2),
    "W": CX - ROAD_W // 2,
    "E": WIDTH - (CX + ROAD_W // 2)
}

# Separate emergency lanes
EMERGENCY_LANES = {
    "N": (CX - 90, None),
    "S": (CX + 90, None),
    "W": (None, CY - 90),
    "E": (None, CY + 90)
}

CAR_COLORS = [
    (40, 130, 230),
    (235, 235, 235),
    (210, 65, 65),
    (245, 180, 40),
    (145, 95, 190),
    (45, 185, 155),
    (70, 75, 85)
]

font = pygame.font.SysFont("Arial", 18, bold=True)
small_font = pygame.font.SysFont("Arial", 14, bold=True)
tiny_font = pygame.font.SysFont("Arial", 11, bold=True)
title_font = pygame.font.SysFont("Arial", 25, bold=True)


# ==========================================================
# SCENERY
# ==========================================================

def draw_text(text, x, y, color=WHITE, selected_font=font):
    image = selected_font.render(text, True, color)
    screen.blit(image, (x, y))


def draw_tree(x, y, scale=1.0):

    x, y = int(x), int(y)

    # Tree shadow
    pygame.draw.ellipse(
        screen, (45, 90, 48),
        (x - 19 * scale, y + 8 * scale,
         42 * scale, 16 * scale)
    )

    # Trunk
    pygame.draw.rect(
        screen, (105, 69, 40),
        (x - 4 * scale, y, 8 * scale, 22 * scale)
    )

    # Leaves
    pygame.draw.circle(
        screen, (35, 105, 55),
        (x, y - 8 * scale), int(19 * scale)
    )

    pygame.draw.circle(
        screen, (54, 140, 65),
        (x - 9 * scale, y - 13 * scale), int(12 * scale)
    )

    pygame.draw.circle(
        screen, (72, 155, 72),
        (x + 10 * scale, y - 14 * scale), int(12 * scale)
    )


def draw_bush(x, y):

    pygame.draw.ellipse(
        screen, (36, 105, 51),
        (x, y, 35, 19)
    )

    pygame.draw.circle(
        screen, (55, 145, 65),
        (x + 10, y + 7), 9
    )

    pygame.draw.circle(
        screen, (75, 160, 70),
        (x + 23, y + 6), 9
    )


def draw_building(x, y, w, h, name, color):

    # Shadow
    pygame.draw.rect(
        screen, (55, 75, 55),
        (x + 6, y + 7, w, h),
        border_radius=8
    )

    # Main building
    pygame.draw.rect(
        screen, color,
        (x, y, w, h),
        border_radius=8
    )

    # Roof edge
    pygame.draw.rect(
        screen, (210, 215, 215),
        (x, y, w, 12),
        border_radius=5
    )

    # Windows
    columns = max(2, w // 42)

    for row in range(2):

        for col in range(columns):

            wx = x + 12 + col * 38
            wy = y + 25 + row * 38

            if wx + 23 < x + w - 5 and wy + 24 < y + h - 5:

                pygame.draw.rect(
                    screen, GLASS,
                    (wx, wy, 23, 24),
                    border_radius=3
                )

                pygame.draw.line(
                    screen, WHITE,
                    (wx + 11, wy),
                    (wx + 11, wy + 24), 1
                )

    # Entrance
    pygame.draw.rect(
        screen, (75, 85, 90),
        (x + w // 2 - 15, y + h - 30, 30, 30)
    )

    pygame.draw.rect(
        screen, (130, 205, 220),
        (x + w // 2 - 11, y + h - 26, 22, 26)
    )

    draw_text(
        name,
        x + 10,
        y + 5,
        WHITE,
        tiny_font
    )


def draw_mall():

    x, y, w, h = 800, 45, 340, 170

    # Mall shadow
    pygame.draw.rect(
        screen, (45, 75, 50),
        (x + 8, y + 8, w, h),
        border_radius=10
    )

    # Mall building
    pygame.draw.rect(
        screen, (185, 194, 198),
        (x, y, w, h),
        border_radius=10
    )

    # Roof
    pygame.draw.rect(
        screen, (80, 100, 115),
        (x, y, w, 25),
        border_radius=8
    )

    # Glass front
    for i in range(6):

        wx = x + 15 + i * 52

        pygame.draw.rect(
            screen, (75, 165, 195),
            (wx, y + 38, 43, 75),
            border_radius=4
        )

        pygame.draw.line(
            screen, WHITE,
            (wx + 21, y + 38),
            (wx + 21, y + 113), 2
        )

    # Entrance
    pygame.draw.rect(
        screen, (55, 65, 75),
        (x + 140, y + 112, 60, 58)
    )

    pygame.draw.rect(
        screen, (100, 195, 220),
        (x + 146, y + 118, 48, 52)
    )

    # Mall sign
    pygame.draw.rect(
        screen, (35, 65, 100),
        (x + 90, y + 6, 160, 25),
        border_radius=5
    )

    draw_text(
        "CITY MALL",
        x + 126,
        y + 9,
        WHITE,
        small_font
    )

    draw_text(
        "SHOPPING  |  FOOD  |  CINEMA",
        x + 82,
        y + 150,
        BLACK,
        tiny_font
    )


def draw_parking():

    x, y = 820, 570

    pygame.draw.rect(
        screen, (95, 100, 95),
        (x, y, 300, 150),
        border_radius=7
    )

    draw_text("MALL PARKING", x + 90, y + 8, WHITE, small_font)

    for i in range(5):

        px = x + 20 + i * 53

        pygame.draw.rect(
            screen, WHITE,
            (px, y + 38, 43, 85), 2
        )

    # Parked cars
    for i in range(4):

        px = x + 27 + i * 53

        pygame.draw.rect(
            screen,
            CAR_COLORS[i],
            (px, y + 55, 27, 48),
            border_radius=5
        )

        pygame.draw.rect(
            screen, (120, 190, 210),
            (px + 4, y + 61, 19, 14),
            border_radius=3
        )


def draw_city_scenery():

    screen.fill(GRASS)

    # Small grass texture
    for x in range(0, WIDTH, 70):
        for y in range(0, HEIGHT, 70):

            pygame.draw.circle(
                screen, GRASS_DARK,
                (x + 10, y + 10), 2
            )

    # Buildings around the road
    draw_building(
        35, 65, 260, 155,
        "CITY OFFICE", (120, 135, 145)
    )

    draw_building(
        45, 570, 265, 155,
        "CITY CAFE", (165, 105, 75)
    )

    draw_building(
        820, 570, 300, 150,
        "PARKING AREA", (100, 110, 115)
    )

    draw_mall()

    # Mall parking
    draw_parking()

    # Trees
    for x, y in [
        (340, 85), (390, 165), (730, 90),
        (750, 180), (340, 660), (390, 735),
        (735, 660), (760, 735), (1150, 300),
        (1150, 520), (30, 350), (30, 490)
    ]:
        draw_tree(x, y, 1.0)

    # Bushes
    for x, y in [
        (320, 280), (340, 310), (750, 555),
        (770, 580), (315, 510), (720, 240)
    ]:
        draw_bush(x, y)


# ==========================================================
# ROAD DRAWING
# ==========================================================

def draw_dashed_line(start, end, color, width=2, dash=18, gap=14):

    x1, y1 = start
    x2, y2 = end

    dx = x2 - x1
    dy = y2 - y1

    length = math.hypot(dx, dy)

    if length == 0:
        return

    ux = dx / length
    uy = dy / length

    position = 0

    while position < length:

        end_position = min(position + dash, length)

        p1 = (
            int(x1 + ux * position),
            int(y1 + uy * position)
        )

        p2 = (
            int(x1 + ux * end_position),
            int(y1 + uy * end_position)
        )

        pygame.draw.line(
            screen, color, p1, p2, width
        )

        position += dash + gap


def draw_roads():

    # Sidewalk strips
    pygame.draw.rect(
        screen, SIDEWALK,
        (CX - ROAD_W // 2 - 18, 0, ROAD_W + 36, HEIGHT)
    )

    pygame.draw.rect(
        screen, SIDEWALK,
        (0, CY - ROAD_W // 2 - 18, WIDTH, ROAD_W + 36)
    )

    # Roads
    pygame.draw.rect(
        screen, ROAD,
        (CX - ROAD_W // 2, 0, ROAD_W, HEIGHT)
    )

    pygame.draw.rect(
        screen, ROAD,
        (0, CY - ROAD_W // 2, WIDTH, ROAD_W)
    )

    # Road edge lines
    for offset in [-ROAD_W // 2, ROAD_W // 2]:

        pygame.draw.line(
            screen, WHITE,
            (CX + offset, 0),
            (CX + offset, HEIGHT), 3
        )

        pygame.draw.line(
            screen, WHITE,
            (0, CY + offset),
            (WIDTH, CY + offset), 3
        )

    # Centre markings
    draw_dashed_line(
        (CX, 0), (CX, CY - ROAD_W // 2),
        YELLOW, 3
    )

    draw_dashed_line(
        (CX, CY + ROAD_W // 2), (CX, HEIGHT),
        YELLOW, 3
    )

    draw_dashed_line(
        (0, CY), (CX - ROAD_W // 2, CY),
        YELLOW, 3
    )

    draw_dashed_line(
        (CX + ROAD_W // 2, CY), (WIDTH, CY),
        YELLOW, 3
    )

    # Dedicated bypass lane markings
    for direction in DIRECTIONS:

        lane_x, lane_y = EMERGENCY_LANES[direction]

        if direction == "N":
            draw_dashed_line(
                (lane_x, 0),
                (lane_x, CY - ROAD_W // 2),
                ORANGE, 2, 12, 10
            )

        elif direction == "S":
            draw_dashed_line(
                (lane_x, CY + ROAD_W // 2),
                (lane_x, HEIGHT),
                ORANGE, 2, 12, 10
            )

        elif direction == "W":
            draw_dashed_line(
                (0, lane_y),
                (CX - ROAD_W // 2, lane_y),
                ORANGE, 2, 12, 10
            )

        elif direction == "E":
            draw_dashed_line(
                (CX + ROAD_W // 2, lane_y),
                (WIDTH, lane_y),
                ORANGE, 2, 12, 10
            )

    # Zebra crossings
    for i in range(8):

        x = CX - 110 + i * 30

        pygame.draw.rect(
            screen, WHITE,
            (x, CY - 143, 17, 28)
        )

        pygame.draw.rect(
            screen, WHITE,
            (x, CY + 115, 17, 28)
        )

    for i in range(8):

        y = CY - 110 + i * 30

        pygame.draw.rect(
            screen, WHITE,
            (CX - 143, y, 28, 17)
        )

        pygame.draw.rect(
            screen, WHITE,
            (CX + 115, y, 28, 17)
        )


# ==========================================================
# VEHICLE CLASS
# ==========================================================

class Vehicle:

    def __init__(self, direction, emergency=False, position=0):

        self.direction = direction
        self.emergency = emergency
        self.position = float(position)

        self.speed = (
            205 if emergency
            else random.uniform(95, 125)
        )

        self.color = (
            (245, 245, 245) if emergency
            else random.choice(CAR_COLORS)
        )

    def get_coordinates(self):

        p = self.position

        if self.emergency:

            lane_x, lane_y = EMERGENCY_LANES[self.direction]

            if self.direction == "N":
                return int(lane_x - 10), int(-CAR_L + p)

            if self.direction == "S":
                return int(lane_x - 10), int(HEIGHT - p)

            if self.direction == "W":
                return int(-CAR_L + p), int(lane_y - 10)

            return int(WIDTH - p), int(lane_y - 10)

        if self.direction == "N":
            return CX - 55, int(-CAR_L + p)

        if self.direction == "S":
            return CX + 25, int(HEIGHT - p)

        if self.direction == "W":
            return int(-CAR_L + p), CY + 25

        return int(WIDTH - p), CY - 55

    def draw(self):

        x, y = self.get_coordinates()

        vertical = self.direction in ("N", "S")

        if vertical:
            rect = pygame.Rect(x, y, CAR_W, CAR_L)
        else:
            rect = pygame.Rect(x, y, CAR_L, CAR_W)

        # Wheels
        if vertical:

            pygame.draw.rect(
                screen, BLACK,
                (x - 3, y + 5, 4, 9),
                border_radius=2
            )

            pygame.draw.rect(
                screen, BLACK,
                (x + CAR_W - 1, y + 5, 4, 9),
                border_radius=2
            )

            pygame.draw.rect(
                screen, BLACK,
                (x - 3, y + 23, 4, 9),
                border_radius=2
            )

            pygame.draw.rect(
                screen, BLACK,
                (x + CAR_W - 1, y + 23, 4, 9),
                border_radius=2
            )

        else:

            pygame.draw.rect(
                screen, BLACK,
                (x + 5, y - 3, 9, 4),
                border_radius=2
            )

            pygame.draw.rect(
                screen, BLACK,
                (x + 5, y + CAR_W - 1, 9, 4),
                border_radius=2
            )

            pygame.draw.rect(
                screen, BLACK,
                (x + 23, y - 3, 9, 4),
                border_radius=2
            )

            pygame.draw.rect(
                screen, BLACK,
                (x + 23, y + CAR_W - 1, 9, 4),
                border_radius=2
            )

        # Car body
        pygame.draw.rect(
            screen, self.color,
            rect,
            border_radius=6
        )

        pygame.draw.rect(
            screen, (25, 30, 35),
            rect,
            width=1,
            border_radius=6
        )

        # Windows
        if vertical:

            pygame.draw.rect(
                screen, (80, 160, 190),
                (x + 3, y + 7, CAR_W - 6, 9),
                border_radius=3
            )

            pygame.draw.rect(
                screen, (65, 125, 150),
                (x + 3, y + 19, CAR_W - 6, 7),
                border_radius=2
            )

            # Headlights
            pygame.draw.circle(
                screen, YELLOW, (x + 4, y + 3), 2
            )

            pygame.draw.circle(
                screen, YELLOW, (x + 16, y + 3), 2
            )

        else:

            pygame.draw.rect(
                screen, (80, 160, 190),
                (x + 8, y + 3, 10, CAR_W - 6),
                border_radius=3
            )

            pygame.draw.rect(
                screen, (65, 125, 150),
                (x + 21, y + 3, 7, CAR_W - 6),
                border_radius=2
            )

            pygame.draw.circle(
                screen, YELLOW, (x + 3, y + 4), 2
            )

            pygame.draw.circle(
                screen, YELLOW, (x + 3, y + 16), 2
            )

        # Emergency ambulance details
        if self.emergency:

            pygame.draw.rect(
                screen, RED,
                rect,
                width=3,
                border_radius=6
            )

            if vertical:

                pygame.draw.rect(
                    screen, RED,
                    (x + 7, y + 12, 6, 12)
                )

                pygame.draw.rect(
                    screen, RED,
                    (x + 4, y + 15, 12, 6)
                )

            else:

                pygame.draw.rect(
                    screen, RED,
                    (x + 12, y + 7, 12, 6)
                )

                pygame.draw.rect(
                    screen, RED,
                    (x + 15, y + 4, 6, 12)
                )

            pygame.draw.circle(
                screen, RED,
                rect.center, 4
            )

    def is_off_screen(self):

        x, y = self.get_coordinates()

        return (
            x < -60 or x > WIDTH + 60
            or y < -60 or y > HEIGHT + 60
        )


# ==========================================================
# TRAFFIC CONTROLLER
# ==========================================================

class SmartFlow:

    def __init__(self):

        self.vehicles = []
        self.mode = "ADAPTIVE"
        self.peak = False

        self.reset()

    def reset(self):

        self.vehicles.clear()

        self.phase = "GREEN"
        self.green_axis = "NS"
        self.target_axis = "NS"

        self.phase_time = 0.0
        self.green_duration = GREEN_TIME
        self.spawn_timer = 0.0

        self.total_passed = 0
        self.emergency_passed = 0

        self.emergency_active = False
        self.emergency_vehicle = None
        self.emergency_direction = None
        self.emergency_axis = None
        self.saved_state = None

    def queue_count(self, axis):

        return sum(
            1 for v in self.vehicles
            if not v.emergency
            and AXIS[v.direction] == axis
            and v.position <= STOP_DISTANCE[v.direction]
        )

    def request_emergency(self):

        if self.emergency_active:
            return

        direction = random.choice(DIRECTIONS)

        self.emergency_active = True
        self.emergency_direction = direction
        self.emergency_axis = AXIS[direction]

        # Save signal state and exact remaining time.
        self.saved_state = (
            self.phase,
            self.green_axis,
            self.target_axis,
            self.phase_time,
            self.green_duration,
            self.spawn_timer
        )

        self.emergency_vehicle = Vehicle(
            direction,
            emergency=True,
            position=0
        )

        self.vehicles.append(self.emergency_vehicle)

    def choose_next_axis(self):

        if self.mode == "FIXED":

            return "EW" if self.green_axis == "NS" else "NS"

        ns = self.queue_count("NS")
        ew = self.queue_count("EW")

        if ns > ew:
            return "NS"

        if ew > ns:
            return "EW"

        return "EW" if self.green_axis == "NS" else "NS"

    def update_signals(self, dt):

        if self.emergency_active:
            return

        self.phase_time += dt

        if self.phase == "GREEN":

            if self.phase_time >= self.green_duration:

                self.target_axis = self.choose_next_axis()
                self.phase = "YELLOW"
                self.phase_time = 0

        elif self.phase == "YELLOW":

            if self.phase_time >= YELLOW_TIME:

                self.phase = "ALL_RED"
                self.phase_time = 0

        elif self.phase == "ALL_RED":

            if self.phase_time >= ALL_RED_TIME:

                self.green_axis = self.target_axis
                self.phase = "GREEN"
                self.phase_time = 0
                self.green_duration = GREEN_TIME

    def spawn_traffic(self):

        for direction in DIRECTIONS:

            probability = 0.85 if self.peak else 0.48

            if random.random() > probability:
                continue

            lane = [
                v for v in self.vehicles
                if v.direction == direction
                and not v.emergency
            ]

            if lane:

                rear = min(v.position for v in lane)

                if rear < CAR_L + CAR_GAP:
                    continue

            self.vehicles.append(
                Vehicle(direction, position=0)
            )

    def move_normal(self, dt):

        for direction in DIRECTIONS:

            lane = [
                v for v in self.vehicles
                if v.direction == direction
                and not v.emergency
            ]

            lane.sort(
                key=lambda v: v.position,
                reverse=True
            )

            previous = None

            signal_green = (
                self.phase == "GREEN"
                and self.green_axis == AXIS[direction]
            )

            stop = STOP_DISTANCE[direction]

            for vehicle in lane:

                old = vehicle.position
                new = old + vehicle.speed * dt

                if not signal_green and old < stop:

                    new = min(new, stop - 1)

                if previous is not None:

                    maximum = previous - CAR_L - CAR_GAP
                    new = min(new, maximum)

                vehicle.position = max(old, new)
                previous = vehicle.position

    def finish_emergency(self):

        if self.emergency_vehicle in self.vehicles:
            self.vehicles.remove(self.emergency_vehicle)

        self.total_passed += 1
        self.emergency_passed += 1

        (
            self.phase,
            self.green_axis,
            self.target_axis,
            self.phase_time,
            self.green_duration,
            self.spawn_timer
        ) = self.saved_state

        self.emergency_active = False
        self.emergency_vehicle = None
        self.emergency_direction = None
        self.emergency_axis = None
        self.saved_state = None

    def update(self, dt):

        if self.emergency_active:

            # Only ambulance moves.
            # All normal cars and normal signal timer are frozen.
            if self.emergency_vehicle:

                self.emergency_vehicle.position += (
                    self.emergency_vehicle.speed * dt
                )

                if self.emergency_vehicle.is_off_screen():
                    self.finish_emergency()

            return

        self.spawn_timer += dt

        interval = 0.55 if self.peak else 1.0

        if self.spawn_timer >= interval:

            self.spawn_timer = 0
            self.spawn_traffic()

        self.update_signals(dt)
        self.move_normal(dt)

        for vehicle in self.vehicles[:]:

            if not vehicle.emergency and vehicle.is_off_screen():

                self.vehicles.remove(vehicle)
                self.total_passed += 1


# ==========================================================
# TRAFFIC LIGHTS
# ==========================================================

def draw_signal(x, y, axis, simulation):

    pygame.draw.rect(
        screen, (25, 25, 28),
        (x, y, 45, 110),
        border_radius=9
    )

    if simulation.emergency_active:

        active = (
            GREEN if axis == simulation.emergency_axis
            else RED
        )

    elif simulation.phase == "GREEN":

        active = (
            GREEN if axis == simulation.green_axis
            else RED
        )

    elif simulation.phase == "YELLOW":

        active = (
            YELLOW if axis == simulation.green_axis
            else RED
        )

    else:

        active = RED

    for i, color in enumerate([RED, YELLOW, GREEN]):

        shown = color if color == active else (65, 65, 65)

        pygame.draw.circle(
            screen, shown,
            (x + 22, y + 20 + i * 34), 11
        )


# ==========================================================
# STREETLIGHTS
# ==========================================================

def draw_streetlight(x, y):

    pygame.draw.rect(
        screen, BLACK,
        (x, y, 5, 55)
    )

    pygame.draw.line(
        screen, BLACK,
        (x + 2, y), (x + 20, y), 4
    )

    pygame.draw.circle(
        screen, YELLOW,
        (x + 21, y), 7
    )


# ==========================================================
# MAIN DRAW FUNCTION
# ==========================================================

def draw_scene(simulation, paused):

    draw_city_scenery()
    draw_roads()

    # Streetlights
    for x, y in [
        (420, 225), (770, 225),
        (420, 530), (770, 530)
    ]:
        draw_streetlight(x, y)

    # Cars
    for vehicle in simulation.vehicles:
        vehicle.draw()

    # Traffic lights
    draw_signal(
        CX - 115, CY - 185,
        "NS", simulation
    )

    draw_signal(
        CX + 70, CY - 185,
        "EW", simulation
    )

    # Dashboard panel
    pygame.draw.rect(
        screen, (22, 31, 43),
        (15, 15, 265, 250),
        border_radius=12
    )

    draw_text("SMARTFLOW AI", 30, 25, YELLOW, title_font)

    draw_text(
        f"Mode: {simulation.mode}",
        30, 65
    )

    draw_text(
        f"Signal: {simulation.phase}",
        30, 95
    )

    draw_text(
        f"Green axis: {simulation.green_axis}",
        30, 125, GREEN
    )

    draw_text(
        f"NS Queue: {simulation.queue_count('NS')}",
        30, 160
    )

    draw_text(
        f"EW Queue: {simulation.queue_count('EW')}",
        30, 188
    )

    draw_text(
        f"Vehicles passed: {simulation.total_passed}",
        30, 218
    )

    # Emergency status
    if simulation.emergency_active:

        pygame.draw.rect(
            screen, (90, 35, 20),
            (15, 280, 265, 120),
            border_radius=10
        )

        draw_text(
            "EMERGENCY PRIORITY!",
            28, 292, ORANGE
        )

        draw_text(
            f"Direction: {simulation.emergency_direction}",
            28, 325
        )

        draw_text(
            "Normal traffic: FROZEN",
            28, 355, YELLOW
        )

        draw_text(
            "Bypass lane: ACTIVE",
            28, 375, GREEN, small_font
        )

    elif simulation.phase == "GREEN":

        remaining = max(
            0,
            simulation.green_duration - simulation.phase_time
        )

        draw_text(
            f"Green timer: {remaining:.1f}s",
            30, 285, GREEN
        )

    if simulation.peak:

        draw_text(
            "PEAK TRAFFIC",
            30, 425, ORANGE
        )

    if paused:

        pygame.draw.rect(
            screen, (20, 25, 35),
            (450, 20, 300, 45),
            border_radius=8
        )

        draw_text(
            "SIMULATION PAUSED",
            490, 30, YELLOW
        )

    # Controls panel
    pygame.draw.rect(
        screen, (20, 28, 38),
        (300, HEIGHT - 48, 875, 35),
        border_radius=8
    )

    draw_text(
        "A: Adaptive   F: Fixed   E: Emergency   P: Peak   R: Reset   SPACE: Pause   ESC: Exit",
        320, HEIGHT - 40, WHITE, small_font
    )

    pygame.display.flip()


# ==========================================================
# MAIN LOOP
# ==========================================================

def main():

    simulation = SmartFlow()

    running = True
    paused = False

    while running:

        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_a:
                    simulation.mode = "ADAPTIVE"

                elif event.key == pygame.K_f:
                    simulation.mode = "FIXED"

                elif event.key == pygame.K_e:

                    if not paused:
                        simulation.request_emergency()

                elif event.key == pygame.K_p:
                    simulation.peak = not simulation.peak

                elif event.key == pygame.K_r:
                    simulation.reset()
                    paused = False

        if not paused:
            simulation.update(dt)

        draw_scene(simulation, paused)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
