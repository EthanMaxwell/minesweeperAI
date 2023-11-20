import cv2
import numpy as np
import pyautogui
import time

def find_grid_location(image):
    # Define the lower and upper bounds for the blue color
    lower_blue = np.array([100, 148, 246])
    upper_blue = np.array([107, 160, 255])

    # Create a binary mask for the blue color
    mask = cv2.inRange(image, lower_blue, upper_blue)

    # Find contours in the binary mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out erroneous contours based on shape and area compared to the median contour
    valid_contours = []

    if len(contours) > 0:
        # Calculate the median contour
        median_contour = sorted(contours, key=cv2.contourArea)[-50]

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

    line_len = (int) ((y_centers[-1] - y_centers[0]) / (len(y_centers) - 1) / 5)

    for y in y_centers:
        row = []

        for x in x_centers:
            # Calculate the coordinates for the line above and below the center pixel
            y_top = int(y - line_len)
            y_bottom = int(y + line_len)

            # Extract colors along the vertical line
            colors = image[y_top:y_bottom, x]

            # Exclude white pixels from the averaging process
            non_white_colors = [color for color in colors if not all(color >= 250)]

            if non_white_colors:
                # Average the non-white colors
                avg_color = np.mean(non_white_colors, axis=0)
            else:
                # Set the average color to white if all colors are white
                avg_color = np.array([255, 255, 255], dtype=np.uint8)

            # Determine the color category
            category = get_color_category(avg_color)

            # Append the category to the row
            row.append(category)

        # Append the row to the color grid
        color_grid.append(row)

    return color_grid

def get_color_category(color):
    # Define color ranges for categories
    cover_range = ((90, 180, 240), (130, 220, 255))
    blank_range = ((253, 253, 253), (255, 255, 255))
    one_range = ((20, 170, 200), (40, 200, 230))
    two_range = ((100, 130, 20), (170, 190, 110))
    three_range = ((180, 50, 100), (230, 110, 160))

    # Check the color against predefined ranges
    if is_in_range(color, cover_range):
        return 'c'
    elif is_in_range(color, blank_range):
        return "b"
    elif is_in_range(color, one_range):
        return 1
    elif is_in_range(color, two_range):
        return 2
    elif is_in_range(color, three_range):
        return 3
    else:
        raise Exception(f"Unknown square {color}")


def is_in_range(color, color_range):
    # Check if the color is in the specified range
    return all(color_range[0] <= color) and all(color <= color_range[1])

def start_ai(x_grid, y_grid, board_state):
    cols = len(x_grid)
    rows = len(y_grid)

    # Modify the board state to show mines and free squares
    swept_board = run_ai(rows, cols, board_state)

    # Display the free spaces and the mines
    for row in range(rows):
        for col in range(cols):
            if swept_board[row][col] == "s":  
                # The square is not a mine
                pyautogui.moveTo(x_grid[col], y_grid[row])
                pyautogui.click()
            elif swept_board[row][col] == "m":  # The square is a mine
                # The square is a mine
                pass

def run_ai(rows, cols, board_state):
    changed = False  # Record if any values in the array were changed
    for row in range(rows):
        for col in range(cols):
            # If it's a numbers square check it for relevant info
            if isinstance(board_state[row][col], int):
                pot_mine_num = 0  # The number of mine or unknowns around the square
                mine_num = 0  # The number of mine around the square

                # Check the squares around the square to find the above two values
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if (0 <= row + i < rows and 0 <= col + j < cols):
                            if board_state[row + i][col + j] == "c":  # Unknown square found
                                pot_mine_num += 1
                            elif board_state[row + i][col + j] == "m":  # Mine found
                                mine_num += 1
                                pot_mine_num += 1

                # Check if the square's value is the same as the total potential mines or the total known mines
                if pot_mine_num == board_state[row][col] or mine_num == board_state[row][col]:
                    # Find all unknown squares around the square and change them accordingly
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            if (
                                0 <= row + i < rows and 0 <= col + j < cols
                                and board_state[row + i][col + j] == 'c'
                            ):
                                if pot_mine_num == board_state[row][col]:  # The square is a mine
                                    board_state[row + i][col + j] = "m"
                                else:  # the square is not a mine
                                    board_state[row + i][col + j] = "s"
                                changed = True  # Record that the board state changed
    if changed:  # If the board state changed run this check again
        return run_ai(rows, cols, board_state)
    return board_state


    
def main():
    # Capture the screen using pyautogui
    screen = np.array(pyautogui.screenshot())

    # Convert the image from BGR to RGB (OpenCV uses BGR)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2HSV)

    # Find the grid location
    x_grid, y_grid = find_grid_location(screen)

    pyautogui.moveTo(x_grid[2], y_grid[2], 0.5)
    #pyautogui.click()
    
    while True:
        screen = np.array(pyautogui.screenshot())

        board = read_board(x_grid, y_grid, screen)

        start_ai(x_grid, y_grid, board)


if __name__ == "__main__":
    main()
