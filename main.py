import pygame
import math
from Robot import Robot  # Make sure your Robot class is in a file named Robot.py
from Map import Map  # Make sure your Map class is in a file named Map.py

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
FPS = 60  # Frames per second

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robot Simulation")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Initialize Map and Robot
map_instance = Map()
map_instance.add_square_walls(100, 100, 600)  # You can adjust these values as needed
robot = Robot(WIDTH // 2, HEIGHT // 2, 100)  # Start the robot in the middle of the screen

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    # Limit frame rate of the game loop
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_KP4:
                robot.left_motor(True, True)  # Turn on v_left FORWARD
            if event.key == pygame.K_KP1:
                robot.left_motor(True, False)  # Turn on v_left BACKWARD
            if event.key == pygame.K_KP6:
                robot.right_motor(True, True)  # Turn on v_right FORWARD
            if event.key == pygame.K_KP3:
                robot.right_motor(True, False)  # Turn on v_right BACKWARD
        elif event.type == pygame.KEYUP:
            if event.key in [pygame.K_KP4, pygame.K_KP1]:
                robot.left_motor(False, True)  # Turn off v_left
            if event.key in [pygame.K_KP6, pygame.K_KP3]:
                robot.right_motor(False, True)  # Turn off v_right


    # Update robot
    robot.update(dt)

    # Render
    screen.fill(WHITE)

    # Draw walls
    for wall in map_instance.walls:
        pygame.draw.line(screen, BLACK, (wall[0], wall[1]), (wall[2], wall[3]), 2)

    # Draw robot
    pygame.draw.circle(screen, RED, (int(robot.x), HEIGHT - int(robot.y)), robot.radius)
    end_x = robot.x + robot.radius * math.cos(robot.orientation)
    end_y = HEIGHT - (robot.y + robot.radius * math.sin(robot.orientation))
    pygame.draw.line(screen, BLACK, (int(robot.x), HEIGHT - int(robot.y)), (int(end_x), int(end_y)), 2)

    # Flip the display
    pygame.display.flip()

# Done! Time to quit.
pygame.quit()
