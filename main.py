import cv2
import numpy as np
import pyautogui
import time

def find_grid_location(image):
    # Define the lower and upper bounds for the blue color
    lower_blue = np.array([102, 149, 247])
    upper_blue = np.array([104, 158, 255])

    # Create a binary mask for the blue color
    mask = cv2.inRange(image, lower_blue, upper_blue)

    # Find contours in the binary mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out erroneous contours based on shape and area compared to the median contour
    valid_contours = []

    if len(contours) > 0:
        # Calculate the median contour
        median_contour = sorted(contours, key=cv2.contourArea)[len(contours) // 2]

        for contour in contours:
            # Calculate the absolute difference in area and shape between the current contour and the median contour
            area_difference = abs(cv2.contourArea(contour) - cv2.contourArea(median_contour))
            shape_difference = cv2.matchShapes(median_contour, contour, cv2.CONTOURS_MATCH_I2, 0)

            # Adjust these thresholds based on your specific case
            if area_difference < 20 or shape_difference < 1:
                valid_contours.append(contour)

    # Sort valid contours by their x-coordinate
    valid_contours.sort(key=lambda c: cv2.boundingRect(c)[0])

    # Group contours into columns based on their x-coordinate
    grouped_contours_x = group_contours(valid_contours, 'x', 5)

    # Sort valid contours by their y-coordinate
    valid_contours.sort(key=lambda c: cv2.boundingRect(c)[1])

    # Group contours into rows based on their y-coordinate
    grouped_contours_y = group_contours(valid_contours, 'y', 5)

    # Get the center locations of valid contours in each column and row
    x_centers = [(int)(sum(cv2.boundingRect(contour)[0] + cv2.boundingRect(contour)[2] / 2 for contour in group)) // len(group) for group in grouped_contours_x]
    y_centers = [(int)(sum(cv2.boundingRect(contour)[1] + cv2.boundingRect(contour)[3] / 2 for contour in group)) // len(group) for group in grouped_contours_y]


    return x_centers, y_centers

def group_contours(contours, axis, threshold):
    # Group contours into columns or rows based on their x or y coordinate
    grouped_contours = []
    current_group = [contours[0]]

    for i in range(1, len(contours)):
        current_val = cv2.boundingRect(contours[i])[0] if axis == 'x' else cv2.boundingRect(contours[i])[1]
        prev_val = cv2.boundingRect(contours[i - 1])[0] if axis == 'x' else cv2.boundingRect(contours[i - 1])[1]

        if abs(current_val - prev_val) < threshold:
            current_group.append(contours[i])
        else:
            grouped_contours.append(current_group)
            current_group = [contours[i]]

    grouped_contours.append(current_group)
    return grouped_contours

def read_board(x_centers, y_centers, image):
    color_grid = []

    for y in y_centers:
        row = []

        for x in x_centers:
            # Ensure x and y are integers
            x, y = int(x), int(y)

            # Extract color at the center pixel
            color = image[y, x]

            # Determine the color category
            category = get_color_category(color)

            # Append the category to the row
            row.append(category)

        # Append the row to the color grid
        color_grid.append(row)

    return color_grid

def get_color_category(color):
    # Define color ranges for categories
    cover_range = ((120, 211, 253), (127, 217, 255))
    blank_range = ((253, 253, 253), (255, 255, 255))
    one_range = ((15, 170, 206), (30, 190, 220))
    two_range = ((190, 200, 140), (254, 254, 254))
    three_range = ((210, 20, 90), (240, 90, 150))

    # Check the color against predefined ranges
    if is_in_range(color, cover_range):
        return 'cover'
    elif is_in_range(color, blank_range):
        return 'blank'
    elif is_in_range(color, one_range):
        return 'one'
    elif is_in_range(color, two_range):
        return 'two'
    elif is_in_range(color, three_range):
        return 'three'
    else:
        return 'Unknown'

def is_in_range(color, color_range):
    # Check if the color is in the specified range
    return all(color_range[0] <= color) and all(color <= color_range[1])

    
def main():
    # Capture the screen using pyautogui
    screen = np.array(pyautogui.screenshot())

    # Convert the image from BGR to RGB (OpenCV uses BGR)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2HSV)

    # Find the grid location
    x_grid, y_grid = find_grid_location(screen)

    pyautogui.moveTo(x_grid[2], y_grid[2])
    pyautogui.click()
    time.sleep(1)
    screen = np.array(pyautogui.screenshot())

    read_board(x_grid, y_grid, screen)

if __name__ == "__main__":
    main()
