
import pygame
import random
import sys

# --------------------------------------------------
# SMARTFLOW AI - TRAFFIC SIMULATION
# Standalone prototype; no external project files needed
# --------------------------------------------------

pygame.init()

WIDTH, HEIGHT = 1100, 760
FPS = 30

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SmartFlow AI | Intelligent Traffic Simulation")
clock = pygame.time.Clock()

# Colors
BG = (34, 95, 58)
ROAD = (48, 51, 59)
ROAD_LINE = (230, 230, 230)
WHITE = (245, 245, 245)
BLACK = (20, 22, 27)
RED = (235, 55, 55)
YELLOW = (255, 200, 35)
GREEN = (45, 220, 105)
BLUE = (55, 155, 255)
ORANGE = (255, 135, 40)
GREY = (125, 130, 140)
PANEL = (24, 29, 38)

CX, CY = 550, 390
ROAD_W = 280

# Each direction has its own lane.
# Progress runs from 0 (road entrance) to 1 (road exit).
LANES = {
    "N": (CX - 82, 0, 0, 1),
    "S": (CX + 42, HEIGHT, 0, -1),
    "W": (0, CY - 82, 1, 0),
    "E": (WIDTH, CY + 42, -1, 0),
}

# Approximate progress at the stop line for each approach.
STOP_LINE = {
    "N": (CY - ROAD_W / 2 - 22) / HEIGHT,
    "S": (HEIGHT - (CY + ROAD_W / 2 + 22)) / HEIGHT,
    "W": (CX - ROAD_W / 2 - 22) / WIDTH,
    "E": (WIDTH - (CX + ROAD_W / 2 + 22)) / WIDTH,
}

phase = "NS_GREEN"
phase_timer = 0.0
sim_time = 0.0
paused = False
mode = "AI Demo"
speed = 1
spawn_timer = 0.0

cars = []
next_car_id = 0
completed = 0
emergency_served = 0
total_wait = 0.0
wait_samples = 0

# Signal timing in simulated seconds
GREEN_TIME = 8.0
YELLOW_TIME = 2.0
ALL_RED_TIME = 1.0

# Emergency testing frequency. Lower to 0.12 for the final demo.
EMERGENCY_PROBABILITY = 0.18

# Vehicle dimensions and spacing
CAR_LENGTH = 25
MIN_GAP = 0.065
MOVE_STEP = 0.0032


def draw_text(text, x, y, size=20, color=WHITE):
    font = pygame.font.SysFont("arial", size, bold=True)
    surface = font.render(str(text), True, color)
    screen.blit(surface, (x, y))


def reset():
    global phase, phase_timer, sim_time, cars
    global next_car_id, completed, emergency_served
    global total_wait, wait_samples, spawn_timer

    phase = "NS_GREEN"
    phase_timer = 0.0
    sim_time = 0.0
    cars = []
    next_car_id = 0
    completed = 0
    emergency_served = 0
    total_wait = 0.0
    wait_samples = 0
    spawn_timer = 0.0


def spawn_car(direction=None, emergency=None):
    global next_car_id

    if direction is None:
        direction = random.choice(["N", "S", "E", "W"])

    if emergency is None:
        emergency = random.random() < EMERGENCY_PROBABILITY

    # Each vehicle gets a stable identity and its own waiting counter.
    cars.append({
        "id": next_car_id,
        "direction": direction,
        "progress": 0.0,
        "emergency": emergency,
        "wait": 0.0,
        "crossed_stop": False,
    })
    next_car_id += 1


def signal_group(direction):
    return "NS" if direction in ("N", "S") else "EW"


def green_for(direction):
    group = signal_group(direction)
    return phase == group + "_GREEN"


def emergency_waiting():
    # Only consider emergency vehicles that have not left the road.
    # Priority logic below acts on the approach, not on a vehicle
    # that has already exited the simulation.
    candidates = [
        car for car in cars
        if car["emergency"] and car["progress"] < 1.0
    ]
    if not candidates:
        return None

    return min(candidates, key=lambda car: car["progress"])


def change_phase():
    global phase, phase_timer

    phase_timer = 0.0

    # Normal safe sequence: green -> yellow -> all-red -> other green.
    if phase == "NS_GREEN":
        phase = "NS_YELLOW"
    elif phase == "NS_YELLOW":
        phase = "ALL_RED_TO_EW"
    elif phase == "ALL_RED_TO_EW":
        phase = "EW_GREEN"
    elif phase == "EW_GREEN":
        phase = "EW_YELLOW"
    elif phase == "EW_YELLOW":
        phase = "ALL_RED_TO_NS"
    elif phase == "ALL_RED_TO_NS":
        phase = "NS_GREEN"


def update_signal(dt):
    global phase_timer, phase

    phase_timer += dt

    # Fixed mode uses the regular signal cycle.
    if mode == "Fixed":
        duration = (
            YELLOW_TIME if phase.endswith("YELLOW")
            else ALL_RED_TIME if phase.startswith("ALL_RED")
            else GREEN_TIME
        )
        if phase_timer >= duration:
            change_phase()
        return

    # AI demo mode: request emergency priority when one is waiting.
    emergency = emergency_waiting()

    if emergency is not None:
        wanted = signal_group(emergency["direction"]) + "_GREEN"

        # Never jump directly from one green to the other.
        if phase in ("NS_GREEN", "EW_GREEN"):
            current_group = phase[:2]
            if current_group != signal_group(emergency["direction"]):
                change_phase()
                return

        elif phase in ("NS_YELLOW", "EW_YELLOW"):
            if phase_timer >= YELLOW_TIME:
                phase = (
                    "ALL_RED_TO_EW" if phase == "NS_YELLOW"
                    else "ALL_RED_TO_NS"
                )
                phase_timer = 0.0
            return

        elif phase.startswith("ALL_RED"):
            if phase_timer >= ALL_RED_TIME:
                phase = wanted
                phase_timer = 0.0
            return

    duration = (
        YELLOW_TIME if phase.endswith("YELLOW")
        else ALL_RED_TIME if phase.startswith("ALL_RED")
        else GREEN_TIME
    )

    if phase_timer >= duration:
        change_phase()


def update_vehicles(dt):
    global completed, emergency_served, total_wait, wait_samples

    # Generate vehicles at a controlled rate.
    global spawn_timer
    spawn_timer += dt

    spawn_interval = 1.4 if mode == "AI Demo" else 1.8
    if spawn_timer >= spawn_interval:
        spawn_timer = 0.0
        spawn_car()

    # Process each approach independently, front vehicle first.
    for direction in ("N", "S", "E", "W"):
        lane_cars = [
            car for car in cars
            if car["direction"] == direction
        ]

        lane_cars.sort(
            key=lambda car: car["progress"],
            reverse=True
        )

        front_position = None
        stop = STOP_LINE[direction]

        for car in lane_cars:
            progress = car["progress"]
            step = MOVE_STEP * speed

            # Determine whether this vehicle may enter the junction.
            green = green_for(direction)

            # Vehicles already past their stop line may clear the
            # junction. A red signal blocks new entries.
            if not car["crossed_stop"]:
                if green and progress + step >= stop:
                    car["progress"] = min(stop + step, 1.0)
                    car["crossed_stop"] = True
                elif green:
                    car["progress"] = min(progress + step, stop)
                elif progress + step < stop:
                    car["progress"] = progress + step
                else:
                    car["progress"] = min(progress, stop - 0.002)
                    car["wait"] += dt
                    total_wait += dt
                    wait_samples += 1
            else:
                car["progress"] = min(1.0, progress + step)

            # Enforce spacing behind the vehicle in front.
            # If there is not enough space, this vehicle stays behind.
            if front_position is not None:
                max_progress = front_position - MIN_GAP
                if car["progress"] > max_progress:
                    car["progress"] = max_progress
                    car["wait"] += dt

            front_position = car["progress"]

    # Remove vehicles that have completed their journey.
    for car in cars[:]:
        if car["progress"] >= 0.999:
            cars.remove(car)
            completed += 1
            if car["emergency"]:
                emergency_served += 1


def vehicle_position(car):
    direction = car["direction"]
    progress = car["progress"]
    x0, y0, dx, dy = LANES[direction]

    if direction == "N":
        return int(x0), int(progress * HEIGHT)
    if direction == "S":
        return int(x0), int(HEIGHT - progress * HEIGHT)
    if direction == "W":
        return int(progress * WIDTH), int(y0)
    return int(WIDTH - progress * WIDTH), int(y0)


def draw_road():
    screen.fill(BG)

    pygame.draw.rect(
        screen, ROAD,
        (CX - ROAD_W // 2, 0, ROAD_W, HEIGHT)
    )
    pygame.draw.rect(
        screen, ROAD,
        (0, CY - ROAD_W // 2, WIDTH, ROAD_W)
    )

    # Lane markings
    for y in range(0, HEIGHT, 42):
        pygame.draw.line(
            screen, ROAD_LINE,
            (CX, y), (CX, y + 20), 2
        )

    for x in range(0, WIDTH, 42):
        pygame.draw.line(
            screen, ROAD_LINE,
            (x, CY), (x + 20, CY), 2
        )

    # Stop lines on each approach
    pygame.draw.line(
        screen, WHITE,
        (CX - ROAD_W // 2, CY - ROAD_W // 2 - 22),
        (CX - 15, CY - ROAD_W // 2 - 22), 4
    )
    pygame.draw.line(
        screen, WHITE,
        (CX + 15, CY + ROAD_W // 2 + 22),
        (CX + ROAD_W // 2, CY + ROAD_W // 2 + 22), 4
    )
    pygame.draw.line(
        screen, WHITE,
        (CX - ROAD_W // 2 - 22, CY - ROAD_W // 2),
        (CX - ROAD_W // 2 - 22, CY - 15), 4
    )
    pygame.draw.line(
        screen, WHITE,
        (CX + ROAD_W // 2 + 22, CY + 15),
        (CX + ROAD_W // 2 + 22, CY + ROAD_W // 2), 4
    )


def draw_signal(x, y, group):
    pygame.draw.rect(
        screen, BLACK,
        (x, y, 46, 112),
        border_radius=8
    )

    if phase.startswith("ALL_RED"):
        red_on = True
        yellow_on = False
        green_on = False
    else:
        red_on = not phase.startswith(group + "_")
        yellow_on = phase == group + "_YELLOW"
        green_on = phase == group + "_GREEN"

    lamps = [
        (RED, red_on),
        (YELLOW, yellow_on),
        (GREEN, green_on),
    ]

    for i, (color, active) in enumerate(lamps):
        pygame.draw.circle(
            screen,
            color if active else (70, 73, 80),
            (x + 23, y + 19 + i * 36),
            12
        )


def draw_signals():
    draw_signal(CX - ROAD_W // 2 - 64, CY - ROAD_W // 2 - 100, "NS")
    draw_signal(CX + ROAD_W // 2 + 18, CY + ROAD_W // 2 - 12, "EW")


def draw_vehicles():
    for car in cars:
        x, y = vehicle_position(car)
        color = ORANGE if car["emergency"] else BLUE

        if car["direction"] in ("N", "S"):
            rect = pygame.Rect(x - 12, y - 18, 24, 36)
        else:
            rect = pygame.Rect(x - 18, y - 12, 36, 24)

        pygame.draw.rect(screen, color, rect, border_radius=5)

        if car["emergency"]:
            pygame.draw.circle(screen, WHITE, (x, y), 4)
            draw_text("E", x - 5, y - 31, 15, WHITE)


def draw_dashboard():
    pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 94))

    draw_text("SMARTFLOW AI", 18, 10, 27)
    draw_text("Intelligent Traffic Simulation", 18, 48, 16, GREY)

    draw_text(f"Mode: {mode}", 340, 12, 18)
    draw_text(f"Time: {sim_time:.1f}s", 340, 48, 17)

    draw_text(f"Vehicles: {len(cars)}", 535, 12, 17)
    draw_text(f"Completed: {completed}", 535, 48, 17)

    draw_text(f"Emergency served: {emergency_served}", 735, 12, 16)
    draw_text(f"Speed: {speed}x", 735, 48, 17)

    status = "PAUSED" if paused else "RUNNING"
    draw_text(status, 970, 14, 17, YELLOW)

    avg_wait = total_wait / wait_samples if wait_samples else 0.0
    draw_text(
        f"Average sampled wait: {avg_wait:.2f}s",
        20, HEIGHT - 50, 17
    )
    draw_text(
        "SPACE Pause | R Reset | 1 Fixed | 2 AI Demo | UP/DOWN Speed | E Test ambulance | ESC Quit",
        20, HEIGHT - 25, 15
    )


def main():
    global paused, mode, speed, sim_time

    running = True

    while running:
        real_dt = clock.tick(FPS) / 1000.0
        dt = min(real_dt, 0.05) * speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_r:
                    reset()

                elif event.key == pygame.K_1:
                    mode = "Fixed"

                elif event.key == pygame.K_2:
                    mode = "AI Demo"

                elif event.key == pygame.K_UP:
                    speed = min(4, speed + 1)

                elif event.key == pygame.K_DOWN:
                    speed = max(1, speed - 1)

                elif event.key == pygame.K_e:
                    # Deterministic emergency test vehicle.
                    spawn_car(
                        direction=random.choice(["N", "S", "E", "W"]),
                        emergency=True
                    )

        if not paused:
            sim_time += dt
            update_signal(dt)
            update_vehicles(dt)

        draw_road()
        draw_signals()
        draw_vehicles()
        draw_dashboard()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()