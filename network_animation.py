
import sys
import pygame

from multi_junction import (
    MultiJunctionController,
    JUNCTIONS,
    ROAD_NETWORK,
)

# =====================================================
# SMARTFLOW AI - MULTI JUNCTION EMERGENCY ANIMATION
# A* ROUTING + EMERGENCY SIGNAL PRIORITY
# =====================================================

pygame.init()

WIDTH, HEIGHT = 900, 650
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SmartFlow AI - Multi Junction Emergency System")

clock = pygame.time.Clock()

WHITE = (245, 245, 245)
BLACK = (25, 25, 25)
ROAD = (65, 68, 75)
ROAD_LINE = (220, 220, 220)
BLUE = (40, 130, 230)
RED = (230, 45, 45)
GREEN = (40, 200, 90)
YELLOW = (245, 190, 35)
ORANGE = (255, 135, 20)
GREY = (150, 155, 160)
DARK = (30, 35, 42)

font = pygame.font.SysFont("Arial", 22, bold=True)
small_font = pygame.font.SysFont("Arial", 16, bold=True)
tiny_font = pygame.font.SysFont("Arial", 13)

# Positions for the five junctions
POSITIONS = {
    "A": (110, 430),
    "B": (330, 150),
    "C": (330, 470),
    "D": (570, 310),
    "E": (790, 150),
}

# A* route controller
controller = MultiJunctionController()
route, route_cost = controller.plan_emergency_route("A", "E")

# Ambulance movement
current_segment = 0
segment_elapsed = 0.0
segment_duration = 0.0

ambulance_position = POSITIONS[route[0]]
ambulance_arrived = False

# First emergency signal request
signal_request = controller.get_next_signal_request()

# Modes and controls
mode = "AI"
traffic_level = "Normal"
paused = False
running = True
simulation_time = 0.0

# Normal signal cycle duration
FIXED_GREEN_TIME = 8.0


def draw_text(text, x, y, color=WHITE, selected_font=small_font):
    image = selected_font.render(text, True, color)
    screen.blit(image, (x, y))


def interpolate(start, end, fraction):
    x = start[0] + (end[0] - start[0]) * fraction
    y = start[1] + (end[1] - start[1]) * fraction
    return int(x), int(y)


def get_normal_phase(junction):
    """Simple normal signal cycle for this visual demonstration."""

    if mode == "Fixed":
        index = int(simulation_time // FIXED_GREEN_TIME) % 2
        return "NS_GREEN" if index == 0 else "EW_GREEN"

    # Simple adaptive demonstration:
    # alternate phases using a shorter cycle.
    index = int(simulation_time // 6) % 2
    return "NS_GREEN" if index == 0 else "EW_GREEN"


def get_signal_phase(junction):
    signal = controller.signals[junction]

    if signal["emergency_priority"]:
        return signal["phase"], True

    return get_normal_phase(junction), False


def draw_roads():
    screen.fill((85, 135, 80))

    # Draw every road only once
    drawn = set()

    for start, neighbours in ROAD_NETWORK.items():
        for end in neighbours:
            edge = frozenset((start, end))

            if edge in drawn:
                continue

            drawn.add(edge)

            pygame.draw.line(
                screen,
                ROAD,
                POSITIONS[start],
                POSITIONS[end],
                24,
            )

            pygame.draw.line(
                screen,
                ROAD_LINE,
                POSITIONS[start],
                POSITIONS[end],
                2,
            )


def draw_junctions():
    for junction, position in POSITIONS.items():

        phase, emergency_active = get_signal_phase(junction)

        if emergency_active:
            signal_color = GREEN
        elif phase == "NS_GREEN":
            signal_color = GREEN
        else:
            signal_color = RED

        # Junction body
        pygame.draw.circle(
            screen,
            DARK,
            position,
            31,
        )

        pygame.draw.circle(
            screen,
            WHITE,
            position,
            25,
            2,
        )

        label = font.render(junction, True, WHITE)
        screen.blit(
            label,
            label.get_rect(center=position),
        )

        # Signal indicator
        signal_position = (
            position[0] + 29,
            position[1] - 28,
        )

        pygame.draw.circle(
            screen,
            BLACK,
            signal_position,
            11,
        )

        pygame.draw.circle(
            screen,
            signal_color,
            signal_position,
            7,
        )

        if emergency_active:
            draw_text(
                "EMERGENCY GREEN",
                position[0] - 65,
                position[1] + 38,
                GREEN,
                tiny_font,
            )


def draw_route():
    if len(route) < 2:
        return

    for index in range(len(route) - 1):

        start = POSITIONS[route[index]]
        end = POSITIONS[route[index + 1]]

        pygame.draw.line(
            screen,
            BLUE,
            start,
            end,
            6,
        )


def draw_ambulance(position):
    x, y = position

    # Ambulance body
    pygame.draw.rect(
        screen,
        WHITE,
        (x - 17, y - 11, 34, 22),
        border_radius=5,
    )

    # Red emergency marking
    pygame.draw.rect(
        screen,
        RED,
        (x - 4, y - 10, 8, 20),
    )

    # Emergency light
    pygame.draw.circle(
        screen,
        RED,
        (x, y - 15),
        5,
    )

    pygame.draw.circle(
        screen,
        BLUE,
        (x + 9, y - 15),
        4,
    )

    # Wheels
    pygame.draw.circle(screen, BLACK, (x - 10, y + 11), 4)
    pygame.draw.circle(screen, BLACK, (x + 10, y + 11), 4)


def draw_dashboard():
    pygame.draw.rect(
        screen,
        DARK,
        (0, 0, WIDTH, 95),
    )

    draw_text(
        "SMARTFLOW AI - MULTI JUNCTION SYSTEM",
        20,
        12,
        WHITE,
        font,
    )

    draw_text(
        "A* Route: " + " -> ".join(route),
        20,
        48,
        (120, 190, 255),
        small_font,
    )

    draw_text(
        f"Mode: {mode}   Traffic: {traffic_level}",
        610,
        15,
        WHITE,
        small_font,
    )

    draw_text(
        f"Route cost: {route_cost} seconds",
        610,
        45,
        WHITE,
        small_font,
    )


def draw_controls():
    pygame.draw.rect(
        screen,
        DARK,
        (0, HEIGHT - 65, WIDTH, 65),
    )

    draw_text(
        "A: Adaptive   F: Fixed   P: Normal/Peak",
        18,
        HEIGHT - 52,
        WHITE,
        tiny_font,
    )

    draw_text(
        "SPACE: Pause   R: Reset   ESC: Exit",
        18,
        HEIGHT - 28,
        WHITE,
        tiny_font,
    )


def reset_simulation():
    global controller
    global route, route_cost
    global current_segment, segment_elapsed
    global segment_duration, ambulance_position
    global ambulance_arrived, signal_request
    global simulation_time, paused

    controller = MultiJunctionController()
    route, route_cost = controller.plan_emergency_route("A", "E")

    current_segment = 0
    segment_elapsed = 0.0
    segment_duration = float(
        ROAD_NETWORK[route[0]][route[1]]
    )

    ambulance_position = POSITIONS[route[0]]
    ambulance_arrived = False

    signal_request = controller.get_next_signal_request()

    simulation_time = 0.0
    paused = False


# Set the first road travel duration
if len(route) > 1:
    segment_duration = float(
        ROAD_NETWORK[route[0]][route[1]]
    )


while running:

    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                paused = not paused

            elif event.key == pygame.K_a:
                mode = "AI"

            elif event.key == pygame.K_f:
                mode = "Fixed"

            elif event.key == pygame.K_p:
                traffic_level = (
                    "Peak" if traffic_level == "Normal"
                    else "Normal"
                )

            elif event.key == pygame.K_r:
                reset_simulation()

    if not paused and not ambulance_arrived:

        simulation_time += dt

        if current_segment < len(route) - 1:

            start_node = route[current_segment]
            end_node = route[current_segment + 1]

            start_position = POSITIONS[start_node]
            end_position = POSITIONS[end_node]

            segment_elapsed += dt

            fraction = min(
                1.0,
                segment_elapsed / segment_duration,
            )

            ambulance_position = interpolate(
                start_position,
                end_position,
                fraction,
            )

            if fraction >= 1.0:

                ambulance_position = end_position
                current_segment += 1
                segment_elapsed = 0.0

                if current_segment >= len(route) - 1:
                    ambulance_arrived = True
                    signal_request = None

                else:
                    signal_request = (
                        controller.ambulance_reached_junction()
                    )

                    next_start = route[current_segment]
                    next_end = route[current_segment + 1]

                    segment_duration = float(
                        ROAD_NETWORK[next_start][next_end]
                    )

    # Drawing
    draw_roads()
    draw_route()
    draw_junctions()
    draw_ambulance(ambulance_position)
    draw_dashboard()
    draw_controls()

    if paused:
        draw_text(
            "PAUSED",
            WIDTH // 2 - 45,
            110,
            YELLOW,
            font,
        )

    if ambulance_arrived:
        draw_text(
            "AMBULANCE REACHED DESTINATION E",
            WIDTH // 2 - 175,
            110,
            GREEN,
            font,
        )

    if signal_request:
        draw_text(
            f"Next priority: Junction {signal_request['junction']}",
            20,
            115,
            ORANGE,
            small_font,
        )

    pygame.display.flip()


pygame.quit()
sys.exit()
