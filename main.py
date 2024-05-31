import pygame
import math
import numpy as np
import random

from KalmanFilter import KalmanFilter
from Robot import Robot
from Map import Map

GUI = True


def run(nn=None, seed=0, sim=False):
    if GUI:
        pygame.init()

    FPS = 60

    dt = 1 / FPS
    # ========= CONFIGURATION CONSTANTS =========
    TILE_SIZE = 80  #size of one square tile in pixels
    MAP_SIZE = (3, 3)  #size of the map in tiles (horizontal, vertical)
    DUST_PER_TILE = 100  #amount of dust particles covering one tile

    START_TILE = (1, 3)  #robot's starting tile in grid (horizontal, vertical) - (1, 1) = bottom left

    MAP_COMPLEXITY = 3  # degree of complexity of the randomly generated map (should be adjusted based on map size)

    SEED = random.randint(0,9999)  # <--- change this for different map generation (!!!)

    # ======== MISC CONSTANTS ========
    WIDTH = (MAP_SIZE[0] + 2) * TILE_SIZE
    HEIGHT = (MAP_SIZE[1] + 2) * TILE_SIZE
    TOTAL_DUST = MAP_SIZE[0] * MAP_SIZE[1] * DUST_PER_TILE

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    PURPLE_ALPHA = (160, 32, 240, 75)
    YELLOW = (255, 255, 0)
    DUST_COLOUR = (210, 170, 109, 50)

    # ======== Visualization Flags ========
    force_vector_visible = False
    sensor_lines_visible = False
    sensor_values_always_visible = False
    feature_distance_visible = True
    feature_bearing_visible = True
    robot_orientation_visible = True
    exact_path_visible = False
    estimated_path_visible = False
    covariance_ellipse_visible = False

    # Boilerplate pygame code
    if GUI:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Robot Simulation")

        font = pygame.font.SysFont(None, 16)

    running = True
    clock = pygame.time.Clock()

    random.seed(SEED)

    # Initialize map and robot
    map = Map(WIDTH, HEIGHT, MAP_SIZE, TILE_SIZE, MAP_COMPLEXITY)
    map.generate()

    start_position = map.calculate_initial_position(START_TILE)
    robot = Robot(start_position[0], start_position[1], 200)

    map.simulate_dust(TOTAL_DUST, robot)

    # Initialize Kalman Filter
    initial_state = [robot.x, robot.y, robot.orientation]  # Assuming the robot's initial x, y, and orientation are set
    initial_state = [random.randrange(WIDTH), random.randrange(HEIGHT), random.uniform(0, 2 * math.pi)]
    initial_covariance = np.eye(3) * 0.1  # Small initial uncertainty
    process_noise = np.diag([0.02, 0.02, np.deg2rad(0.5)])  # Process noise covariance matrix
    measurement_noise = np.diag([0.1, np.deg2rad(5)])  # Measurement noise covariance matrix

    kf = KalmanFilter(initial_state, initial_covariance, process_noise, measurement_noise, robot, map)

    def engine_control():
        if nn == None:
            global running
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Control engine using NUMPAD: we can go forward and backward for each motor so take 4,1 as forward/backward for left motor and 6,3 for right motor
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_KP4:
                        robot.left_motor(True, True)  # Turn on left motor FORWARD
                    if event.key == pygame.K_KP1:
                        robot.left_motor(True, False)  # Turn on left motor BACKWARD
                    if event.key == pygame.K_KP6:
                        robot.right_motor(True, True)  # Turn on right motor FORWARD
                    if event.key == pygame.K_KP3:
                        robot.right_motor(True, False)  # Turn on right motor BACKWARD

                elif event.type == pygame.KEYUP:
                    if event.key in [pygame.K_KP4, pygame.K_KP1]:
                        robot.left_motor(False, True)  # Turn off left_motor
                    if event.key in [pygame.K_KP6, pygame.K_KP3]:
                        robot.right_motor(False, True)  # Turn off right motor
        else:
            #This runs when we use NN
            #The input to the forward method is basically: x, y, 12*sensor distances
            values = nn.forward(np.concatenate((kf.state[:2], robot.wall_sensor_distances)))[0]

            #This gives values for both motors, which are interpreted through the same logic as normally
            value_left = values[0]
            value_right = values[1]
            if value_left >= 0.5:
                robot.left_motor(True, True)  # Turn on left motor FORWARD
            elif value_left <= -0.5:
                robot.left_motor(True, False)  # Turn on left motor BACKWARD
            else:
                robot.left_motor(False, True)  # Turn off left motor

            if value_right >= 0.5:
                robot.right_motor(True, True)  # Turn on right motor FORWARD
            elif value_right <= -0.5:
                robot.right_motor(True, False)  # Turn on right motor BACKWARD
            else:
                robot.right_motor(False, True)  # Turn off right motor

    def draw_walls():
        # Redraw map
        for wall in map.walls:
            pygame.draw.line(screen, BLACK, (wall.x1, HEIGHT - wall.y1), (wall.x2, HEIGHT - wall.y2), 2)

    def draw_features():
        # Draw small black circle on each feature position
        for feature in map.features:
            pygame.draw.circle(screen, BLACK, (feature.x, HEIGHT - feature.y), feature.radius, 0)

    def draw_robot():
        # Draw robot + line indicating forward
        pygame.draw.circle(screen, RED, (int(robot.x), HEIGHT - int(robot.y)), robot.radius)
        end_x = robot.x + robot.radius * math.cos(robot.orientation)
        end_y = HEIGHT - (robot.y + robot.radius * math.sin(robot.orientation))
        pygame.draw.line(screen, BLACK, (int(robot.x), HEIGHT - int(robot.y)), (int(end_x), int(end_y)), 2)

        # Draw robot orientation [debugging]
        if robot_orientation_visible:
            orientation_text = font.render(str(int(math.degrees(robot.orientation))) + "°", True, YELLOW)
            text_rect = orientation_text.get_rect(
                center=(int((robot.x + end_x) / 2), int(((HEIGHT - robot.y) + end_y) / 2)))
            screen.blit(orientation_text, text_rect)

    def draw_sensors():
        for sensor in robot.wall_sensors:
            # Draw wall sensor lines [debugging]
            if sensor_lines_visible:
                pygame.draw.line(screen, GREEN, (int(sensor.start_coord[0]), HEIGHT - int(sensor.start_coord[1])),
                                 (int(sensor.end_coord[0]), int(HEIGHT - sensor.end_coord[1])), 1)
            # Draw wall sensor distances (always [debugging] or only when inside sensor range)
            if sensor_values_always_visible or int(sensor.distance < sensor.init_distance):
                distance_text = font.render(str(int(sensor.distance)), True, BLUE)
                text_rect = distance_text.get_rect(
                    center=(int(sensor.text_coord[0]), HEIGHT - int(sensor.text_coord[1])))
                screen.blit(distance_text, text_rect)

    def draw_motor_values():
        motor_text_scale = robot.radius * 0.5
        left_motor_text_x = robot.x - motor_text_scale * math.sin(robot.orientation)
        left_motor_text_y = robot.y + motor_text_scale * math.cos(robot.orientation)
        right_motor_text_x = robot.x + motor_text_scale * math.sin(robot.orientation)
        right_motor_text_y = robot.y - motor_text_scale * math.cos(robot.orientation)
        left_motor_text = font.render(str(robot.v_left), True, BLACK)
        right_motor_text = font.render(str(robot.v_right), True, BLACK)
        left_text_rect = left_motor_text.get_rect(center=(int(left_motor_text_x), HEIGHT - int(left_motor_text_y)))
        right_text_rect = right_motor_text.get_rect(center=(int(right_motor_text_x), HEIGHT - int(right_motor_text_y)))
        screen.blit(left_motor_text, left_text_rect)
        screen.blit(right_motor_text, right_text_rect)

    def draw_force_vector():
        # Draw force vector [debugging]
        if force_vector_visible:
            force_scale = 1
            force_end_x = robot.x + robot.velocity_vector[0] * force_scale
            force_end_y = HEIGHT - (robot.y + robot.velocity_vector[1] * force_scale)
            pygame.draw.line(screen, BLUE, (int(robot.x), HEIGHT - int(robot.y)), (int(force_end_x), int(force_end_y)),
                             2)

    def draw_feature_lines(detected_features):
        # Draw lines between feature and robot when inside sensor range
        for feature in detected_features:
            pygame.draw.line(screen, GREEN, (int(feature[2].x), HEIGHT - int(feature[2].y)),
                             ((int(robot.x), int(HEIGHT - robot.y))), 1)
            # Draw feature distance [debugging]
            if feature_distance_visible:
                distance_text = font.render(str(int(feature[0])), True, BLACK)
                distance_text_rect = distance_text.get_rect(
                    midbottom=(int((feature[2].x + robot.x) / 2), HEIGHT - int((feature[2].y + robot.y) / 2)))
                screen.blit(distance_text, distance_text_rect)
            # Draw relative feature bearing [debugging]
            if feature_bearing_visible:
                bearing_text = font.render(str(int(math.degrees(feature[1]))) + "°", True, RED)
                bearing_text_rect = bearing_text.get_rect(
                    midtop=(int((feature[2].x + robot.x) / 2), HEIGHT - int((feature[2].y + robot.y) / 2)))
                screen.blit(bearing_text, bearing_text_rect)

    def draw_path(path, color):
        if len(path) > 1:
            for i in range(len(path) - 1):
                start_point = path[i]
                end_point = path[i + 1]
                pygame.draw.line(screen, color, (start_point[0], HEIGHT - start_point[1]),
                                 (end_point[0], HEIGHT - end_point[1]), 2)

    # draws intermediate estimates of position and covariance
    def draw_covariance_ellipse(covariance_history, scale_factor):
        if len(covariance_history) > 0:
            for ellipse in covariance_history:
                x_axis = ellipse[1][0] * scale_factor
                y_axis = ellipse[1][1] * scale_factor

                ellipse_rect = pygame.Rect(0, 0, x_axis, y_axis)
                ellipse_surface = pygame.Surface(ellipse_rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(ellipse_surface, PURPLE_ALPHA, ellipse_rect)
                rotated_surface = pygame.transform.rotate(ellipse_surface, ellipse[1][2])  # rotate ellipse using angle
                blit_position = (
                    ellipse[0][0] - x_axis / 2, HEIGHT - ellipse[0][1] - x_axis / 2)  # get center position of ellipse
                screen.blit(rotated_surface, blit_position)

    def draw_dust_particles(dust_particles):
        for particle in dust_particles:
            if not particle.collected:
                pygame.draw.circle(screen, DUST_COLOUR, (particle.x, HEIGHT - particle.y), particle.size, 0)

    # shows amount of dust collected
    def draw_dust_collection(collected_dust, position):
        text = font.render("Dust collected: {} / {}".format(collected_dust, TOTAL_DUST), True, BLACK)
        text_rect = text.get_rect(midleft=(int(position[0]), HEIGHT - int(position[1])))
        screen.blit(text, text_rect)

    time = 0
    while running:

        time += 1
        if time > 400:
            running = False
        if not sim:
            dt = clock.tick(FPS) / 1000
        engine_control()

        control_input = np.array([robot.v, robot.omega])

        kf.predict(control_input, dt)

        robot.update(dt, map.walls)
        robot.update_sensors(map.walls)
        robot.update_feature_sensors(map.walls, map.features)
        robot.collect_dust(map.dust_particles)

        measurements = [(f[0], f[1], (f[2].x, f[2].y)) for f in robot.detected_features]

        kf.update(measurements)

        if GUI:
            screen.fill(WHITE)
            draw_walls()
            draw_features()
            draw_dust_particles(map.dust_particles)
            draw_dust_collection(robot.dust_collected, ((WIDTH / 2), ((HEIGHT * 0.1) / 2)))
            draw_feature_lines(robot.detected_features)
            draw_robot()
            draw_sensors()
            draw_motor_values()
            draw_force_vector()
            if exact_path_visible:
                draw_path(robot.path, BLUE)
            if estimated_path_visible:
                draw_path(kf.path, RED)
            if covariance_ellipse_visible:
                draw_covariance_ellipse(kf.covariance_history, 20)

            pygame.display.flip()
            pygame.display.update()
    if GUI:
        pygame.quit()
    return max(0, (robot.dust_collected / len(map.dust_particles)) * (1 - 0.001 * robot.collisions_detected))


def runset(nn=None, sim=False):
    total = 0
    for i in range(10):
        total += run(nn, i, sim)
    return total / 10
