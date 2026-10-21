import heapq
from itertools import count


def astar(graph, start, goal, heuristic):
    sequence = count()

    frontier = [
        (heuristic(start, goal), next(sequence), start)
    ]

    came_from = {}
    cost_so_far = {start: 0}

    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()
            return path, cost_so_far[goal]

        for neighbour, road_cost in graph.get(current, {}).items():
            if road_cost < 0:
                raise ValueError("Road costs must be non-negative")

            new_cost = cost_so_far[current] + road_cost

            if (
                neighbour not in cost_so_far
                or new_cost < cost_so_far[neighbour]
            ):
                cost_so_far[neighbour] = new_cost
                came_from[neighbour] = current

                priority = new_cost + heuristic(neighbour, goal)

                heapq.heappush(
                    frontier,
                    (priority, next(sequence), neighbour)
                )

    return None, float("inf")


def run_visualization(graph, route, cost):
    try:
        import pygame
    except ImportError as error:
        raise RuntimeError(
            "Pygame is required for the route simulation. "
            "Install it with: python -m pip install pygame"
        ) from error

    pygame.init()

    width, height = 800, 560
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Emergency Route Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)

    node_positions = {
        "A": (100, 400),
        "B": (300, 150),
        "C": (300, 450),
        "D": (520, 300),
        "E": (700, 150),
    }
    background = (245, 247, 250)
    road_colour = (165, 175, 185)
    route_colour = (35, 130, 230)
    node_colour = (255, 255, 255)
    text_colour = (35, 40, 45)
    vehicle_colour = (225, 55, 55)
    node_radius = 25
    route_segments = list(zip(route, route[1:]))
    paused = False
    elapsed = 0.0
    running = True

    def vehicle_position(simulation_time):
        remaining = simulation_time

        for start, end in route_segments:
            segment_cost = graph[start][end]
            if remaining <= segment_cost:
                fraction = remaining / segment_cost
                start_x, start_y = node_positions[start]
                end_x, end_y = node_positions[end]
                return (
                    start_x + (end_x - start_x) * fraction,
                    start_y + (end_y - start_y) * fraction,
                )
            remaining -= segment_cost

        return node_positions[route[-1]]

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    elapsed = 0.0

        if not paused:
            elapsed = min(elapsed + dt, cost)

        screen.fill(background)

        drawn_roads = set()
        for start, neighbours in graph.items():
            for end, road_cost in neighbours.items():
                road = frozenset((start, end))
                if road in drawn_roads:
                    continue
                drawn_roads.add(road)

                start_pos = node_positions[start]
                end_pos = node_positions[end]
                pygame.draw.line(screen, road_colour, start_pos, end_pos, 8)
                midpoint = (
                    (start_pos[0] + end_pos[0]) // 2,
                    (start_pos[1] + end_pos[1]) // 2,
                )
                label = small_font.render(
                    f"{road_cost} sec", True, text_colour
                )
                screen.blit(label, (midpoint[0] + 5, midpoint[1] - 22))

        for start, end in route_segments:
            pygame.draw.line(
                screen,
                route_colour,
                node_positions[start],
                node_positions[end],
                8,
            )

        for node, position in node_positions.items():
            pygame.draw.circle(screen, node_colour, position, node_radius)
            pygame.draw.circle(screen, route_colour, position, node_radius, 3)
            label = font.render(node, True, text_colour)
            screen.blit(label, label.get_rect(center=position))

        vehicle = vehicle_position(elapsed)
        pygame.draw.circle(
            screen,
            vehicle_colour,
            (round(vehicle[0]), round(vehicle[1])),
            14,
        )
        pygame.draw.circle(
            screen,
            node_colour,
            (round(vehicle[0]), round(vehicle[1])),
            5,
        )

        route_text = " -> ".join(route)
        screen.blit(
            font.render(f"Emergency route: {route_text}", True, text_colour),
            (20, 20),
        )
        screen.blit(
            small_font.render(
                f"Travel time: {elapsed:.1f} / {cost} seconds",
                True,
                text_colour,
            ),
            (20, 55),
        )
        controls = "SPACE: pause/resume    R: restart    ESC: close"
        screen.blit(small_font.render(controls, True, text_colour), (20, 525))

        if elapsed >= cost:
            arrived = small_font.render(
                "Emergency vehicle has arrived.", True, (20, 125, 60)
            )
            screen.blit(arrived, (20, 85))

        if paused:
            paused_text = font.render("PAUSED", True, vehicle_colour)
            screen.blit(paused_text, (width - 110, 20))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    road_network = {
        "A": {"B": 4, "C": 2},
        "B": {"A": 4, "D": 5, "E": 10},
        "C": {"A": 2, "D": 3},
        "D": {"B": 5, "C": 3, "E": 2},
        "E": {"B": 10, "D": 2},
    }

    # Zero heuristic provides a Dijkstra-style correctness check.
    def heuristic(node, goal):
        return 0

    route, cost = astar(
        road_network,
        "A",
        "E",
        heuristic
    )

    print("Selected route:", route)
    print("Estimated cost:", cost, "seconds")

    if route is not None:
        run_visualization(road_network, route, cost)