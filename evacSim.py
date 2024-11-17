import pygame
import random
import math
import csv


CSV_FILE = "simulation_results.csv"
def initialize_csv(file_name):
    try:
        with open(file_name, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Simulation", "Use Leaders", "Num Pedestrians", "Total Time (s)"])
    except FileExistsError:
        # File already exists, no need to rewrite the header
        pass

def save_results_to_csv(simulation_num, use_leaders, num_pedestrians, total_time, file_name=CSV_FILE):
    with open(file_name, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([simulation_num, use_leaders,num_pedestrians, total_time])


initialize_csv(CSV_FILE)
# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Leader-Follower Simulation with Exit Timing")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WALL_COLOR = (128, 128, 128)

# Simulation settings
USE_LEADERS = True  # Set to False to test without leaders
NUM_PEDESTRIANS = 100
NUM_LEADERS = 3 if USE_LEADERS else 0
SPEED = 2
FOLLOW_DISTANCE = 75
COLLISION_RADIUS = 10
EXIT_RADIUS = 10

# Define walls and exits
wall_thickness = 10
walls = [
    pygame.Rect(0, 0, WIDTH // 4 - EXIT_RADIUS, wall_thickness),
    pygame.Rect(WIDTH // 4 + EXIT_RADIUS, 0, WIDTH * 3 // 4, wall_thickness),
    pygame.Rect(0, HEIGHT - wall_thickness, WIDTH // 2 - EXIT_RADIUS, wall_thickness),
    pygame.Rect(WIDTH // 2 + EXIT_RADIUS, HEIGHT - wall_thickness, WIDTH // 2, wall_thickness),
    pygame.Rect(0, 0, wall_thickness, HEIGHT // 2 - EXIT_RADIUS),
    pygame.Rect(0, HEIGHT // 2 + EXIT_RADIUS, wall_thickness, HEIGHT // 2),
]
exits = [
    (WIDTH // 4, wall_thickness // 2),
    (WIDTH // 2, HEIGHT - wall_thickness // 2),
    (wall_thickness // 2, HEIGHT // 2),
]


class Entity:
    def __init__(self, x, y, color, speed):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), COLLISION_RADIUS)

    def move_towards(self, target_x, target_y):
        dx, dy = target_x - self.x, target_y - self.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx, dy = dx / distance, dy / distance
            self.x += dx * self.speed
            self.y += dy * self.speed

    def avoid_collisions(self, others):
        for other in others:
            if other != self:
                dx, dy = self.x - other.x, self.y - other.y
                distance = math.hypot(dx, dy)
                if distance < COLLISION_RADIUS * 2 and distance > 0:
                    repulsion_strength = (COLLISION_RADIUS * 2 - distance) / distance
                    self.x += dx * repulsion_strength * 0.1
                    self.y += dy * repulsion_strength * 0.1

    def reached_exit(self):
        for exit_pos in exits:
            if math.hypot(self.x - exit_pos[0], self.y - exit_pos[1]) < EXIT_RADIUS:
                return True
        return False


class Leader(Entity):
    def __init__(self, x, y, target_exit):
        super().__init__(x, y, BLUE, SPEED)
        self.target_exit = target_exit

    def update(self, entities):
        self.move_towards(*self.target_exit)
        self.avoid_collisions(entities)

class Pedestrian(Entity):
    def __init__(self, x, y, initial_exit):
        super().__init__(x, y, GREEN, SPEED)
        self.initial_exit = initial_exit
        self.assigned_exit = initial_exit
        self.leader_influence = 0.3  # Adjust this for softer or stronger following

    def closer_to_exit_than_leader(self, leader):
        if leader:
            distance_to_leader = math.hypot(leader.x - self.x, leader.y - self.y)
            distance_to_exit = math.hypot(self.assigned_exit[0] - self.x, self.assigned_exit[1] - self.y)
            return distance_to_exit < distance_to_leader
        return False

    def update(self, leaders, entities):
        closest_leader = min(leaders, key=lambda l: math.hypot(l.x - self.x, l.y - self.y), default=None)

        # If there's a leader close enough, consider following the leader's exit
        if closest_leader and math.hypot(closest_leader.x - self.x, closest_leader.y - self.y) < FOLLOW_DISTANCE:
            if self.closer_to_exit_than_leader(closest_leader):
                # Move directly towards the assigned exit if closer than to the leader
                target_x, target_y = self.assigned_exit
            else:
                # Blend movement towards the leader's exit and the leader position
                self.assigned_exit = closest_leader.target_exit
                target_x = (self.assigned_exit[0] * (1 - self.leader_influence) + closest_leader.x * self.leader_influence)
                target_y = (self.assigned_exit[1] * (1 - self.leader_influence) + closest_leader.y * self.leader_influence)
        else:
            # If no leader is nearby, move towards the assigned exit directly
            target_x, target_y = self.assigned_exit

        # Move towards the calculated target point (softly following the leader's direction)
        self.move_towards(target_x, target_y)
        self.avoid_collisions(entities)


def assign_exits_to_leaders(leaders, exits):
    # Calculate distances and assign nearest available exit to each leader
    remaining_exits = exits[:]
    for leader in sorted(leaders,
                         key=lambda l: min(math.hypot(l.x - ex[0], l.y - ex[1]) for ex in remaining_exits)):
        # Sort remaining exits by distance to the current leader
        closest_exit = min(remaining_exits, key=lambda ex: math.hypot(leader.x - ex[0], leader.y - ex[1]))
        leader.target_exit = closest_exit
        remaining_exits.remove(closest_exit)

def run_sim(USE_LEADERS=True, num_pedestrians=NUM_PEDESTRIANS, simulation_num = 1):
    leaders = [Leader(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), None) for _ in
               range(NUM_LEADERS)]
    pedestrians = [Pedestrian(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), random.choice(exits))
                   for _ in range(num_pedestrians)]

    if USE_LEADERS:
        assign_exits_to_leaders(leaders, exits)  # Assign nearest exits to leaders
    else:
        leaders = []

    all_entities = leaders + pedestrians
    running = True
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    end_time = None

    while running:
        screen.fill(WHITE)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw walls and exits
        for wall in walls:
            pygame.draw.rect(screen, WALL_COLOR, wall)
        for exit_pos in exits:
            pygame.draw.circle(screen, RED, exit_pos, EXIT_RADIUS)

        # Update leaders and pedestrians
        for leader in leaders[:]:
            if leader.reached_exit():
                leaders.remove(leader)
                all_entities.remove(leader)
            else:
                leader.update(all_entities)
                leader.draw()

        for pedestrian in pedestrians[:]:
            if pedestrian.reached_exit():
                pedestrians.remove(pedestrian)
                all_entities.remove(pedestrian)
            else:
                pedestrian.update(leaders, all_entities)
                pedestrian.draw()

        # Check if all entities have exited
        if not leaders and not pedestrians and end_time is None:
            end_time = pygame.time.get_ticks()

        # Display elapsed time
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
        font = pygame.font.Font(None, 36)
        timer_text = font.render(f"Time: {elapsed_time:.2f} s", True, BLACK)
        screen.blit(timer_text, (10, 10))

        # Display total time when everyone exits
        if end_time:
            total_time = (end_time - start_time) / 1000
            mode_text = "With Leaders" if USE_LEADERS else "Without Leaders"
            final_text = font.render(f"{mode_text} - Total Time: {total_time:.2f} s", True, BLACK)
            screen.blit(final_text, (WIDTH // 2 - 150, HEIGHT // 2))

            save_results_to_csv(simulation_num, USE_LEADERS, num_pedestrians, str(total_time))
            return total_time


        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


wLeadersTimes = []
wOutLeaders = []
pedest_pop = [10, 20, 40, 80, 160]
for i in range(20):
    for k in range(len(pedest_pop)):
        run_sim(True, pedest_pop[k], i + 1)
        run_sim(False, pedest_pop[k], i + 1)
for i in range(1):
    wLeadersTimes.append(run_sim())
print(wLeadersTimes)
avg = sum(wLeadersTimes) / len(wLeadersTimes)
print(avg)
# for i in range(1):
#     wOutLeaders.append(run_sim(False))
# print(wOutLeaders)
# avg = sum(wOutLeaders) / len(wOutLeaders)
# print(avg)