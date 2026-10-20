
import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SmartFlow AI - Traffic Simulation")
clock = pygame.time.Clock()

GREEN_BG = (40, 110, 65)
ROAD = (55, 58, 65)
WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
RED = (235, 45, 45)
YELLOW = (255, 205, 40)
GREEN = (40, 210, 90)
BLUE = (50, 145, 255)
ORANGE = (255, 135, 40)

CX, CY = WIDTH // 2, HEIGHT // 2
ROAD_W = 260

phase = "NS_GREEN"
phase_timer = 0
sim_time = 0
paused = False
mode = "AI Demo"
speed = 1
cars = []
next_car_id = 0
spawn_timer = 0
completed = 0

def draw_text(text, x, y, size=20, color=WHITE):
    font = pygame.font.SysFont("arial", size, bold=True)
    screen.blit(font.render(str(text), True, color), (x, y))

def reset():
    global phase, phase_timer, sim_time, cars
    global next_car_id, spawn_timer, completed

    phase = "NS_GREEN"
    phase_timer = 0
    sim_time = 0
    cars = []
    next_car_id = 0
    spawn_timer = 0
    completed = 0

def spawn_car():
    global next_car_id

    direction = random.choice(["N", "S", "E", "W"])
    emergency = random.random() < 0.12

    cars.append({
        "id": next_car_id,
        "direction": direction,
        "progress": 0.0,
        "emergency": emergency,
        "stopped": False,
    })
    next_car_id += 1

def update_simulation():
    global phase, phase_timer, sim_time
    global spawn_timer, completed

    sim_time += 1 / 30
    phase_timer += 1 / 30
    spawn_timer += 1

    if spawn_timer >= 45:
        spawn_car()
        spawn_timer = 0

    # Simple demo signal cycle
    if phase_timer >= 6:
        phase_timer = 0

        if phase == "NS_GREEN":
            phase = "NS_YELLOW"
        elif phase == "NS_YELLOW":
            phase = "EW_GREEN"
        elif phase == "EW_GREEN":
            phase = "EW_YELLOW"
        else:
            phase = "NS_GREEN"

    for car in cars[:]:
        direction = car["direction"]
        progress = car["progress"]

        if direction in ("N", "S"):
            green = phase in ("NS_GREEN", "NS_YELLOW")
        else:
            green = phase in ("EW_GREEN", "EW_YELLOW")

        stop = 0.34
        can_move = green or progress < stop

        if can_move:
            car["progress"] += 0.0035 * speed

        if car["progress"] >= 1:
            cars.remove(car)
            completed += 1

def draw_road():
    screen.fill(GREEN_BG)

    pygame.draw.rect(
        screen, ROAD,
        (CX - ROAD_W // 2, 0, ROAD_W, HEIGHT)
    )
    pygame.draw.rect(
        screen, ROAD,
        (0, CY - ROAD_W // 2, WIDTH, ROAD_W)
    )

    for y in range(0, HEIGHT, 45):
        pygame.draw.line(
            screen, WHITE, (CX, y), (CX, y + 22), 2
        )

    for x in range(0, WIDTH, 45):
        pygame.draw.line(
            screen, WHITE, (x, CY), (x + 22, CY), 2
        )

def draw_signals():
    positions = [
        (CX - 180, CY - 205, "NS"),
        (CX + 125, CY + 85, "EW"),
    ]

    for x, y, group in positions:
        pygame.draw.rect(
            screen, BLACK, (x, y, 52, 122),
            border_radius=8
        )

        active_green = (
            phase == "NS_GREEN" if group == "NS"
            else phase == "EW_GREEN"
        )
        active_yellow = (
            phase == "NS_YELLOW" if group == "NS"
            else phase == "EW_YELLOW"
        )

        lights = [
            (RED, not active_green and not active_yellow),
            (YELLOW, active_yellow),
            (GREEN, active_green),
        ]

        for i, (colour, active) in enumerate(lights):
            pygame.draw.circle(
                screen,
                colour if active else (75, 75, 75),
                (x + 26, y + 23 + i * 38),
                13
            )

def draw_cars():
    for car in cars:
        p = car["progress"]
        direction = car["direction"]

        if direction == "N":
            x, y = CX - 75, int(p * HEIGHT)
        elif direction == "S":
            x, y = CX + 35, int(HEIGHT - p * HEIGHT)
        elif direction == "W":
            x, y = int(p * WIDTH), CY - 75
        else:
            x, y = int(WIDTH - p * WIDTH), CY + 35

        colour = ORANGE if car["emergency"] else BLUE

        pygame.draw.rect(
            screen, colour,
            (x - 14, y - 9, 28, 18),
            border_radius=4
        )
        pygame.draw.rect(
            screen, WHITE,
            (x - 5, y - 6, 10, 12),
            border_radius=2
        )

        if car["emergency"]:
            draw_text("E", x - 5, y - 28, 16, WHITE)

def draw_hud():
    pygame.draw.rect(screen, (22, 27, 35), (0, 0, WIDTH, 90))

    draw_text("SMARTFLOW AI", 20, 10, 27)
    draw_text(f"Mode: {mode}", 20, 52, 17)
    draw_text(f"Time: {sim_time:.1f}s", 260, 20)
    draw_text(f"Vehicles: {len(cars)}", 430, 20)
    draw_text(f"Completed: {completed}", 600, 20)
    draw_text("PAUSED" if paused else "RUNNING", 820, 52, 18, YELLOW)
    draw_text(
        "SPACE: Pause | R: Reset | 1: Fixed | 2: AI Demo | UP/DOWN: Speed",
        20, HEIGHT - 28, 15
    )

running = True

while running:
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_r:
                reset()
            elif event.key == pygame.K_1:
                mode = "Fixed"
            elif event.key == pygame.K_2:
                mode = "AI Demo"
            elif event.key == pygame.K_UP:
                speed = min(5, speed + 1)
            elif event.key == pygame.K_DOWN:
                speed = max(1, speed - 1)

    if not paused:
        update_simulation()

    draw_road()
    draw_signals()
    draw_cars()
    draw_hud()

    pygame.display.flip()

pygame.quit()
sys.exit()

