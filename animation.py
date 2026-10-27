import random
import sys
import pygame

# ============================================================
# SMARTFLOW AI - INTELLIGENT TRAFFIC SIGNAL SIMULATION
# Fixed Timing + Adaptive Signals + Emergency Priority
# ============================================================

pygame.init()

WIDTH = 1100
HEIGHT = 760
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SmartFlow AI - Intelligent Traffic Signal")
clock = pygame.time.Clock()

# -------------------- COLOURS --------------------

BG = (45, 115, 65)
ROAD = (48, 48, 52)
WHITE = (245, 245, 245)
BLACK = (15, 15, 15)
RED = (235, 45, 45)
YELLOW = (255, 205, 35)
GREEN = (40, 230, 90)
ORANGE = (255, 135, 20)
GREY = (170, 170, 170)

CAR_COLOURS = [
    (55, 150, 255),
    (240, 240, 240),
    (210, 80, 80),
    (255, 190, 50),
    (160, 100, 220),
    (50, 210, 190),
]

# -------------------- ROAD SETTINGS --------------------

CX = WIDTH // 2
CY = HEIGHT // 2

ROAD_W = 230
CAR_LENGTH = 30
CAR_WIDTH = 18
CAR_GAP = 12

# -------------------- SIGNAL SETTINGS --------------------

GREEN_TIME = 30.0
YELLOW_TIME = 2.0
ALL_RED_TIME = 1.0

MIN_GREEN = 30.0
MAX_GREEN = 30.0

SPAWN_INTERVAL = 1.0

DIRECTIONS = ("N", "S", "E", "W")

AXIS = {
    "N": "NS",
    "S": "NS",
    "E": "EW",
    "W": "EW",
}

STOP_DISTANCE = {
    "N": CY - ROAD_W // 2,
    "S": HEIGHT - (CY + ROAD_W // 2),
    "W": CX - ROAD_W // 2,
    "E": WIDTH - (CX + ROAD_W // 2),
}


# ============================================================
# VEHICLE CLASS
# ============================================================

class Vehicle:

    def __init__(self, direction, emergency=False, position=0):

        self.direction = direction
        self.emergency = emergency

        self.position = float(position)

        self.speed = (
            180.0 if emergency
            else random.uniform(100.0, 130.0)
        )

        self.colour = (
            ORANGE if emergency
            else random.choice(CAR_COLOURS)
        )

        self.passed = False

    def get_coordinates(self):

        p = self.position

        if self.direction == "N":
            x = CX - 55
            y = -CAR_LENGTH + p

        elif self.direction == "S":
            x = CX + 25
            y = HEIGHT - p

        elif self.direction == "W":
            x = -CAR_LENGTH + p
            y = CY + 25

        else:  # EAST
            x = WIDTH - p
            y = CY - 55

        return int(x), int(y)

    def draw(self, surface):

        x, y = self.get_coordinates()

        if self.direction in ("N", "S"):

            rect = pygame.Rect(
                x, y, CAR_WIDTH, CAR_LENGTH
            )

        else:

            rect = pygame.Rect(
                x, y, CAR_LENGTH, CAR_WIDTH
            )

        pygame.draw.rect(
            surface,
            self.colour,
            rect,
            border_radius=4
        )

        if self.emergency:

            pygame.draw.rect(
                surface,
                WHITE,
                rect,
                width=2,
                border_radius=4
            )

            # Emergency warning light
            pygame.draw.circle(
                surface,
                RED,
                rect.center,
                4
            )

    def is_off_screen(self):

        x, y = self.get_coordinates()

        return (
            x < -60
            or x > WIDTH + 60
            or y < -60
            or y > HEIGHT + 60
        )


# ============================================================
# SMARTFLOW TRAFFIC CONTROLLER
# ============================================================

class SmartFlow:

    def __init__(self):

        self.vehicles = []

        self.mode = "ADAPTIVE"

        self.phase = "GREEN"

        self.green_axis = "NS"
        self.target_axis = "NS"

        self.phase_time = 0.0
        self.green_duration = GREEN_TIME

        self.spawn_timer = 0.0

        self.emergency_queue = []

        self.total_passed = 0
        self.emergency_passed = 0

        self.elapsed = 0.0

        self.peak_traffic = False

        self.reset()

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    def reset(self):

        self.vehicles.clear()
        self.emergency_queue.clear()

        self.phase = "GREEN"

        self.green_axis = "NS"
        self.target_axis = "NS"

        self.phase_time = 0.0
        self.green_duration = GREEN_TIME

        self.spawn_timer = 0.0

        self.total_passed = 0
        self.emergency_passed = 0

        self.elapsed = 0.0

    # --------------------------------------------------------
    # QUEUE COUNT
    # --------------------------------------------------------

    def queue_count(self, axis):

        count = 0

        for vehicle in self.vehicles:

            if AXIS[vehicle.direction] != axis:
                continue

            if vehicle.emergency:
                continue

            # Count vehicles approaching the stop line.
            if vehicle.position <= STOP_DISTANCE[vehicle.direction]:
                count += 1

        return count

    # --------------------------------------------------------
    # EMERGENCY REQUEST
    # --------------------------------------------------------

    def request_emergency(self):

        # Select a random approach.
        direction = random.choice(DIRECTIONS)

        # Emergency vehicle gets priority in the request list.
        self.emergency_queue.append(direction)

        # Spawn behind existing vehicles without overlapping.
        same_direction = [
            v for v in self.vehicles
            if v.direction == direction
        ]

        if same_direction:

            rear_position = min(
                v.position for v in same_direction
            )

            spawn_position = rear_position - CAR_LENGTH - CAR_GAP

        else:

            spawn_position = 0.0

        emergency_vehicle = Vehicle(
            direction,
            emergency=True,
            position=spawn_position
        )

        self.vehicles.append(emergency_vehicle)

        emergency_axis = AXIS[direction]

        # If its direction is already green, it can proceed.
        # Otherwise, begin a safe signal transition.
        if (
            self.phase == "GREEN"
            and emergency_axis != self.green_axis
        ):

            self.target_axis = emergency_axis
            self.phase = "YELLOW"
            self.phase_time = 0.0

    # --------------------------------------------------------
    # SELECT NEXT SIGNAL
    # --------------------------------------------------------

    def choose_next_axis(self):

        # Emergency requests always have priority.
        if self.emergency_queue:

            direction = self.emergency_queue[0]

            return AXIS[direction]

        # Fixed mode alternates between the two road axes.
        if self.mode == "FIXED":

            if self.green_axis == "NS":
                return "EW"

            return "NS"

        # Adaptive mode considers the queue lengths.
        ns_queue = self.queue_count("NS")
        ew_queue = self.queue_count("EW")

        if ns_queue > ew_queue:
            return "NS"

        if ew_queue > ns_queue:
            return "EW"

        # Alternate if queue lengths are equal.
        return "EW" if self.green_axis == "NS" else "NS"

    # --------------------------------------------------------
    # GREEN DURATION
    # --------------------------------------------------------

    def calculate_green_time(self, axis):

        # Both modes use a 30-second green phase.
        # Adaptive mode selects which axis gets the next phase.
        return GREEN_TIME

    # --------------------------------------------------------
    # SIGNAL UPDATE
    # --------------------------------------------------------

    def update_signals(self, dt):

        self.phase_time += dt

        if self.phase == "GREEN":

            # Emergency request may interrupt the current green.
            if self.emergency_queue:

                emergency_axis = AXIS[
                    self.emergency_queue[0]
                ]

                if emergency_axis != self.green_axis:

                    self.target_axis = emergency_axis

                    self.phase = "YELLOW"
                    self.phase_time = 0.0

                    return

            # Normal green phase lasts 30 seconds.
            if self.phase_time >= self.green_duration:

                self.target_axis = self.choose_next_axis()

                self.phase = "YELLOW"
                self.phase_time = 0.0

        elif self.phase == "YELLOW":

            # Yellow phase: vehicles must not enter the junction.
            if self.phase_time >= YELLOW_TIME:

                self.phase = "ALL_RED"
                self.phase_time = 0.0

        elif self.phase == "ALL_RED":

            # Brief safety clearance before the next green.
            if self.phase_time >= ALL_RED_TIME:

                self.green_axis = self.target_axis

                self.phase = "GREEN"
                self.phase_time = 0.0

                self.green_duration = (
                    self.calculate_green_time(
                        self.green_axis
                    )
                )

    # --------------------------------------------------------
    # SPAWN NORMAL TRAFFIC
    # --------------------------------------------------------

    def spawn_traffic(self):

        for direction in DIRECTIONS:

            probability = 0.48

            if self.peak_traffic:
                probability = 0.80

            if random.random() > probability:
                continue

            same_direction = [
                v for v in self.vehicles
                if v.direction == direction
            ]

            # Leave enough room behind the last vehicle.
            if same_direction:

                rear_position = min(
                    v.position for v in same_direction
                )

                if rear_position < CAR_LENGTH + CAR_GAP:
                    continue

            self.vehicles.append(
                Vehicle(
                    direction,
                    emergency=False,
                    position=0.0
                )
            )

    # --------------------------------------------------------
    # VEHICLE MOVEMENT AND SPACING
    # --------------------------------------------------------

    def move_vehicles(self, dt):

        for direction in DIRECTIONS:

            lane_vehicles = [
                v for v in self.vehicles
                if v.direction == direction
            ]

            # Front vehicle first; following vehicles maintain
            # the required distance from the vehicle ahead.
            lane_vehicles.sort(
                key=lambda v: v.position,
                reverse=True
            )

            stop_distance = STOP_DISTANCE[direction]

            signal_green = (
                self.phase == "GREEN"
                and self.green_axis == AXIS[direction]
            )

            previous_position = None

            for vehicle in lane_vehicles:

                old_position = vehicle.position

                new_position = (
                    old_position + vehicle.speed * dt
                )

                # A red or yellow signal prevents vehicles
                # that have not crossed the stop line from entering.
                if not signal_green:

                    if old_position < stop_distance:

                        new_position = min(
                            new_position,
                            stop_distance - 1
                        )

                # Keep a safe distance behind the vehicle ahead.
                if previous_position is not None:

                    maximum_position = (
                        previous_position
                        - CAR_LENGTH
                        - CAR_GAP
                    )

                    new_position = min(
                        new_position,
                        maximum_position
                    )

                # Never reverse a vehicle accidentally.
                new_position = max(
                    old_position,
                    new_position
                )

                vehicle.position = new_position

                previous_position = vehicle.position

    # --------------------------------------------------------
    # MAIN UPDATE
    # --------------------------------------------------------

    def update(self, dt):

        self.elapsed += dt

        self.spawn_timer += dt

        interval = (
            0.55 if self.peak_traffic
            else SPAWN_INTERVAL
        )

        if self.spawn_timer >= interval:

            self.spawn_timer = 0.0

            self.spawn_traffic()

        self.update_signals(dt)

        self.move_vehicles(dt)

        # Remove vehicles that have completely left the screen.
        for vehicle in self.vehicles[:]:

            if vehicle.is_off_screen():

                self.total_passed += 1

                if vehicle.emergency:

                    self.emergency_passed += 1

                    if vehicle.direction in self.emergency_queue:

                        self.emergency_queue.remove(
                            vehicle.direction
                        )

                self.vehicles.remove(vehicle)

    # --------------------------------------------------------
    # DRAW ROADS
    # --------------------------------------------------------

    def draw_road(self):

        screen.fill(BG)

        # Vertical road.
        pygame.draw.rect(
            screen,
            ROAD,
            (
                CX - ROAD_W // 2,
                0,
                ROAD_W,
                HEIGHT
            )
        )

        # Horizontal road.
        pygame.draw.rect(
            screen,
            ROAD,
            (
                0,
                CY - ROAD_W // 2,
                WIDTH,
                ROAD_W
            )
        )

        # Lane markings.
        for y in range(0, HEIGHT, 40):

            pygame.draw.line(
                screen,
                WHITE,
                (CX, y),
                (CX, y + 20),
                2
            )

        for x in range(0, WIDTH, 40):

            pygame.draw.line(
                screen,
                WHITE,
                (x, CY),
                (x + 20, CY),
                2
            )

        # Stop lines.
        pygame.draw.line(
            screen,
            WHITE,
            (
                CX - ROAD_W // 2,
                CY - ROAD_W // 2
            ),
            (
                CX + ROAD_W // 2,
                CY - ROAD_W // 2
            ),
            4
        )

        pygame.draw.line(
            screen,
            WHITE,
            (
                CX - ROAD_W // 2,
                CY + ROAD_W // 2
            ),
            (
                CX + ROAD_W // 2,
                CY + ROAD_W // 2
            ),
            4
        )

        pygame.draw.line(
            screen,
            WHITE,
            (
                CX - ROAD_W // 2,
                CY - ROAD_W // 2
            ),
            (
                CX - ROAD_W // 2,
                CY + ROAD_W // 2
            ),
            4
        )

        pygame.draw.line(
            screen,
            WHITE,
            (
                CX + ROAD_W // 2,
                CY - ROAD_W // 2
            ),
            (
                CX + ROAD_W // 2,
                CY + ROAD_W // 2
            ),
            4
        )

    # --------------------------------------------------------
    # DRAW SIGNALS
    # --------------------------------------------------------

    def draw_signal(self, x, y, axis):

        box = pygame.Rect(x, y, 45, 105)

        pygame.draw.rect(
            screen,
            BLACK,
            box,
            border_radius=7
        )

        if self.phase == "GREEN":

            if self.green_axis == axis:
                active_colour = GREEN
            else:
                active_colour = RED

        elif self.phase == "YELLOW":

            if self.green_axis == axis:
                active_colour = YELLOW
            else:
                active_colour = RED

        else:

            active_colour = RED

        colours = [RED, YELLOW, GREEN]

        for i, colour in enumerate(colours):

            draw_colour = (
                colour
                if colour == active_colour
                else (65, 65, 65)
            )

            pygame.draw.circle(
                screen,
                draw_colour,
                (x + 22, y + 18 + i * 34),
                11
            )

    # --------------------------------------------------------
    # DRAW SCREEN
    # --------------------------------------------------------

    def draw(self):

        self.draw_road()

        for vehicle in self.vehicles:
            vehicle.draw(screen)

        # Signal heads.
        self.draw_signal(
            CX - 110,
            CY - 175,
            "NS"
        )

        self.draw_signal(
            CX + 65,
            CY - 175,
            "EW"
        )

        font = pygame.font.SysFont(
            "Arial",
            20,
            bold=True
        )

        small = pygame.font.SysFont(
            "Arial",
            16
        )

        def label(
            text,
            x,
            y,
            colour=WHITE,
            selected_font=None
        ):

            selected_font = selected_font or font

            surface = selected_font.render(
                text,
                True,
                colour
            )

            screen.blit(surface, (x, y))

        # Information panel.
        label("SMARTFLOW AI", 20, 15)

        label(
            f"Mode: {self.mode}",
            20,
            48,
            YELLOW
        )

        label(
            f"Signal: {self.phase}",
            20,
            78
        )

        label(
            f"Green direction: {self.green_axis}",
            20,
            108,
            GREEN
        )

        label(
            f"NS queue: {self.queue_count('NS')}",
            20,
            145
        )

        label(
            f"EW queue: {self.queue_count('EW')}",
            20,
            175
        )

        label(
            f"Vehicles passed: {self.total_passed}",
            20,
            215
        )

        label(
            f"Emergency passed: {self.emergency_passed}",
            20,
            245
        )

        if self.phase == "GREEN":

            remaining = max(
                0,
                self.green_duration - self.phase_time
            )

            label(
                f"Green remaining: {remaining:.1f} s",
                20,
                280,
                GREEN
            )

        elif self.phase == "YELLOW":

            remaining = max(
                0,
                YELLOW_TIME - self.phase_time
            )

            label(
                f"Yellow remaining: {remaining:.1f} s",
                20,
                280,
                YELLOW
            )

        else:

            remaining = max(
                0,
                ALL_RED_TIME - self.phase_time
            )

            label(
                f"All-red remaining: {remaining:.1f} s",
                20,
                280,
                RED
            )

        if self.emergency_queue:

            label(
                "EMERGENCY PRIORITY: "
                + ", ".join(self.emergency_queue),
                20,
                315,
                ORANGE
            )

        else:

            label(
                "Emergency: None",
                20,
                315
            )

        label(
            "A = Adaptive | F = Fixed | E = Emergency",
            20,
            HEIGHT - 65,
            WHITE,
            small
        )

        label(
            "P = Peak Traffic | R = Reset | ESC = Exit",
            20,
            HEIGHT - 38,
            WHITE,
            small
        )

        pygame.display.flip()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    simulation = SmartFlow()

    running = True

    while running:

        dt = min(
            clock.tick(FPS) / 1000.0,
            0.05
        )

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    running = False

                elif event.key == pygame.K_a:

                    simulation.mode = "ADAPTIVE"

                elif event.key == pygame.K_f:

                    simulation.mode = "FIXED"

                elif event.key == pygame.K_e:

                    simulation.request_emergency()

                elif event.key == pygame.K_p:

                    simulation.peak_traffic = (
                        not simulation.peak_traffic
                    )

                elif event.key == pygame.K_r:

                    simulation.reset()

        simulation.update(dt)

        simulation.draw()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()