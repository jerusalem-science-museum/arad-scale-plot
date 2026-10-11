#!/usr/bin/python3
import time
import serial
import pygame
import numpy as np
import platform
from collections import deque

import constants

# Global data structure using deque for O(1) appending and automatic popping of old items
# This replaces standard lists to eliminate memory shift overhead and improve performance
y_data = deque(maxlen=constants.NUM_OF_PLOT_POINTS)

# UI Globals
images = []
current_image = 0
mean_y = 100.0
tara = 0.0


def fill_images():
    """Load animation frames from the resources directory into memory."""
    global images
    images.clear()
    for j in range(constants.NUMBER_OF_IMAGES):
        img_path = f"{constants.RES_PATH}/image_{j}.png"
        try:
            images.append(pygame.image.load(img_path))
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")


def clear_screen(color):
    """Fill the main display background and draw the initial label."""
    main_screen.fill(color)
    text_rect = label.get_rect(center=(main_screen.get_width() // 2, main_screen.get_height() // 2))
    main_screen.blit(label, text_rect)
    pygame.display.flip()


def update_plot_area():
    """Redraw the static background and frame for the plot area."""
    x1 = constants.P_A_X
    y1 = constants.P_A_Y
    x2 = x1 + constants.P_A_W
    y2 = y1 + constants.P_A_H

    plot_surface.fill(constants.P_A_C)
    main_screen.blit(plot_surface, (x1, y1))
    
    # Draw plot area outer frame border
    pygame.draw.lines(
        main_screen, 
        constants.P_A_F_C, 
        True, 
        [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], 
        constants.P_A_F_T
    )


def update_image(image_number, x, y):
    """Blit the current animation frame onto the screen."""
    if 0 <= image_number < len(images):
        image_surface.fill(constants.IMAGE_BK_COLOR)
        main_screen.blit(image_surface, constants.IMAGE_X_Y)
        main_screen.blit(images[image_number], (x, y))


def fill_data(arduino):
    """
    Initial data collection and baseline calibration.
    Fills the deque with baseline data points from the serial interface safely.
    """
    global tara, mean_y
    y_data.clear()
    
    print("Collecting initial calibration samples...")
    # Flush existing buffer to ensure fresh reads
    if arduino and arduino.is_open:
        arduino.reset_input_buffer()

    samples_collected = 0
    t_start = time.time()
    
    while samples_collected < constants.NUM_OF_PLOT_POINTS:
        if arduino and arduino.in_waiting > 0:
            try:
                raw_line = arduino.readline().decode('utf-8', errors='ignore').strip()
                if raw_line:
                    val = float(raw_line)
                    y_data.append(val)
                    samples_collected += 1
            except ValueError:
                continue

    elapsed_time = time.time() - t_start
    time_per_sample = elapsed_time / constants.NUM_OF_PLOT_POINTS
    print(f"Time per sample: {time_per_sample:.6f}s")
    
    if len(y_data) > 0:
        tara = np.mean(y_data)
        mean_y = tara
        print(f"Baseline (Tara): {tara}")


def read_serial_data(arduino):
    """
    Non-blocking serial read helper to prevent UI freezing and handle corrupt strings.
    """
    if arduino and arduino.in_waiting > 0:
        try:
            line = arduino.readline().decode('utf-8', errors='ignore').strip()
            if line:
                return float(line)
        except (ValueError, UnicodeDecodeError):
            # Ignore malformed or incomplete serial packets
            pass
    return None


def update_plot():
    """
    Renders the waveform plot using vector line rendering (draw.lines) 
    and updates the dynamic animation image based on signal scaling.
    """
    global current_image, mean_y

    if len(y_data) < 2:
        return

    # Calculate dynamic plot parameters
    y_list = list(y_data)
    mean_y = np.mean(y_list)
    
    x_l = constants.P_A_X
    dx = constants.P_A_W / (constants.NUM_OF_PLOT_POINTS - 1)
    y_up = constants.P_A_Y
    y_dn = y_up + constants.P_A_H
    
    y_range = mean_y * (constants.SCALE_FACTOR_UP + constants.SCALE_FACTOR_DN)
    if y_range == 0:
        y_range = 100.0  # Prevent division by zero
        
    ymin = mean_y * (1 - constants.SCALE_FACTOR_UP)
    scale = constants.P_A_H / y_range

    # Build point list for batch rendering (O(N) single draw call instead of individual line calls)
    points = []
    for i, val in enumerate(y_list):
        px = x_l + i * dx
        py = y_up + (val - ymin) * scale
        
        # Clamp Y coordinates within plot bounds
        py = max(y_up, min(py, y_dn))
        points.append((px, py))

    # Redraw plot background and line plot
    update_plot_area()
    if len(points) > 1:
        pygame.draw.lines(main_screen, constants.LINE_COLOR, False, points, constants.LINE_WIDTH)

    # Compute animation image frame index according to latest signal value
    latest_val = y_list[-1]
    current_image = int(constants.NUMBER_OF_IMAGES * ((latest_val - ymin) / y_range))
    current_image = max(0, min(current_image, constants.NUMBER_OF_IMAGES - 1))

    # Update animation display
    update_image(
        current_image, 
        constants.PICTURE_X, 
        constants.PICTURE_Y - current_image * constants.DH
    )
    
    # Single unified frame update
    pygame.display.flip()

# =============================================================================
# PROGRAM ENTRY POINT
# =============================================================================

# עוטפים את כל הרצת התוכנית ב-try...except כדי לתפוס שגיאות ולא לסגור את הטרמינל
try:
    # Load animation resources
    fill_images()

    # Initialize Pygame subsystems
    pygame.init()
    clock = pygame.time.Clock()
    infoObject = pygame.display.Info()

    pygame.display.set_caption('In case of problem call amir') 

    main_screen = pygame.display.set_mode((infoObject.current_w, infoObject.current_h))
    screen_surface = pygame.Surface((constants.SCREEN_W, constants.SCREEN_H))
    image_surface = pygame.Surface((constants.IMAGE_W, constants.IMAGE_H))
    plot_surface = pygame.Surface((constants.P_A_W, constants.P_A_H))

    myfont = pygame.font.SysFont(constants.FONT_TYPE, constants.FONT_SIZE)
    label = myfont.render(constants.LABEL, True, constants.FONT_COLOR)

    if constants.FULL_SCREEN:
        pygame.display.toggle_fullscreen()

    # Configure Serial Connection
    port_name = 'COM14' if platform.system() == "Windows" else '/dev/ttyUSB0'
    arduinoData = None
    is_UART_connect = False

    try:
        arduinoData = serial.Serial(port_name, constants.BOUDRATE, timeout=0.1)
        print(f"Port {port_name} opened successfully at {constants.BOUDRATE} baud.")
        is_UART_connect = True
    except Exception as e:
        print(f"Serial connection failed: {e}")
        pygame.quit()
        raise SystemExit()

    # Display calibration screen and load initial sensor data
    clear_screen(constants.SCREEN_COLOR)
    main_screen.blit(label, constants.LABEL_X_Y)
    pygame.display.flip()

    fill_data(arduinoData)
    update_plot()

    clear_screen(constants.SCREEN_COLOR)
    pygame.display.flip()

    # Hide mouse cursor in exhibit mode
    pygame.mouse.set_cursor((8, 8), (0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0))

    # Main Application Loop
    running = True

    while running:
        # 1. Process Serial incoming data without blocking the UI execution loop
        new_sample = read_serial_data(arduinoData)
        if new_sample is not None:
            y_data.append(new_sample)

        # 2. Render plot at controlled FPS rate
        update_plot()
        clock.tick(30)  # Target 30 FPS

        # 3. Handle System & User Input Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_t:
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_f or event.key == pygame.K_d:
                    update_plot_area()
                elif event.key == pygame.K_r:
                    fill_data(arduinoData)
                elif event.key == pygame.K_c:
                    clear_screen(constants.SCREEN_COLOR)
                elif event.key == pygame.K_p:
                    update_plot()

    # Clean Up Resources upon Normal Exit
    if arduinoData and arduinoData.is_open:
        arduinoData.close()

    pygame.quit()
    print("Program exited cleanly.")

except Exception as e:
    # מקטע זה יופעל רק אם התרחשה שגיאה שלא נתפסה במהלך הריצה
    import traceback
    print("\n" + "="*50)
    print("CRASH DETECTED! ERROR DETAILS:")
    print("="*50)
    traceback.print_exc()
    print("="*50)
    input("\nPress ENTER to close the terminal...")