import cv2
import numpy as np
import pyautogui
import time

def find_grid_location(image):
        
    # Define the lower and upper bounds for the blue color
    lower_blue = np.array([56, 142, 245])
    upper_blue = np.array([103, 198, 255])

    # Define the lower and upper bounds for the white color
    lower_white = np.array([140, 140, 140])
    upper_white = np.array([200, 200, 200])

    # Create binary masks for both blue and white colors
    blue_mask = cv2.inRange(image, lower_blue, upper_blue)
    white_mask = cv2.inRange(image, lower_white, upper_white)

    # Combine the binary masks
    combined_mask = cv2.bitwise_or(blue_mask, white_mask)

    # Find contours in the combined binary mask
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
    # Filter out erroneous contours based on shape and area compared to the median contour
    valid_contours = []
    
    colour_sensitivity = 1.2
    
    if len(contours) > 0:
        # Calculate the median contour
        median_contour = sorted(contours, key=cv2.contourArea)[-10]

        for contour in contours:
            # Calculate the absolute difference in area and shape between the current contour and the median contour
            area_difference = cv2.contourArea(contour) / cv2.contourArea(median_contour)
            shape_difference = cv2.matchShapes(median_contour, contour, cv2.CONTOURS_MATCH_I2, 0)

            # Adjust these thresholds based on your specific case
            if area_difference < colour_sensitivity and area_difference > 1/colour_sensitivity and shape_difference < 2:
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

            avg_color = np.min(colors, axis=0)


            # Determine the color category
            category = get_color_category(avg_color)

            # Append the category to the row
            row.append(category)

        # Append the row to the color grid
        color_grid.append(row)

    return color_grid

def get_color_category(color):
    # Define color ranges for categories
    cover_range = ((90, 180, 230), (150, 240, 255))
    blank_range = ((240, 240, 240), (255, 255, 255))
    empty_range = ((20, 20, 20), (60, 60, 90))
    one_range = ((5, 130, 155), (40, 190, 230))
    two_range = ((70, 90, 0), (140, 180, 45))
    three_range = ((120, 10, 50), (220, 70, 130))
    four_range = ((11, 40, 110), (40, 90, 180))
    five_range = ((90, 5, 5), (180, 50, 40))
    six_range = ((0, 91, 90), (10, 120, 109))

    # Check the color against predefined ranges
    if is_in_range(color, cover_range):
        return 'c'
    elif is_in_range(color, blank_range):
        return "b"
    elif is_in_range(color, empty_range):
        return "e"
    elif is_in_range(color, one_range):
        return 1
    elif is_in_range(color, two_range):
        return 2
    elif is_in_range(color, three_range):
        return 3
    elif is_in_range(color, four_range):
        return 4
    elif is_in_range(color, five_range):
        return 5
    elif is_in_range(color, six_range):
        return 6
    else:
        #return "?"
        raise Exception(f"Unknown square {color}")


def is_in_range(color, color_range):
    # Check if the color is in the specified range
    return all(color_range[0] <= color) and all(color <= color_range[1])

def start_ai(x_grid, y_grid, board_state):
    cols = len(x_grid)
    rows = len(y_grid)

    # Modify the board state to show mines and free squares
    simple_check(rows, cols, board_state)
    
    to_click = False
    for row in board_state:
        if "s" in row:
            to_click = True
            break
    
    if not to_click:
        advanced_check(rows, cols, board_state)

    clicked = False
    
    # Display the free spaces and the mines
    for row in range(rows):
        for col in range(cols):
            if board_state[row][col] == "s":  
                # The square is not a mine
                pyautogui.click(x_grid[col], y_grid[row])
                clicked = True
                
            elif board_state[row][col] == "m":  # The square is a mine
                # The square is a mine
                pass
            
    if not clicked:
        raise Exception("Help me Step Bro! I'm stuck!")
        

class InvalidBoardState(Exception):
    pass

def simple_check(rows, cols, board_state):
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

                if pot_mine_num < board_state[row][col] or mine_num > board_state[row][col]:
                    raise InvalidBoardState(board_state)
                
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
        return simple_check(rows, cols, board_state)
    return board_state

def advanced_check(rows, cols, board_state):
    for row in range(rows):
        for col in range(cols):
            if board_state[row][col] == "c":
                m_board = [row[:] for row in board_state]
                
                m_board[row][col] = "m"
                try:
                    simple_check(rows, cols, m_board)
                except InvalidBoardState:
                    board_state[row][col] = "s"
                    continue
                
                s_board = [row[:] for row in board_state]
                s_board[row][col] = "s"
                try:
                    simple_check(rows, cols, s_board)
                except InvalidBoardState:
                    board_state[row][col] = "m"
                    continue
                
    simple_check(rows, cols, board_state)
    
def main():
    # Capture the screen using pyautogui
    screen = np.array(pyautogui.screenshot())

    # Find the grid location
    x_grid, y_grid = find_grid_location(screen)
    mid_x, mid_y = (int)(len(x_grid)/2), (int)(len(y_grid)/2)
    board = read_board(x_grid, y_grid, screen)
    
    # Click window to ensure it is focused
    pyautogui.click(x_grid[mid_x], y_grid[mid_y])
    time.sleep(0.01)
    
    if board[mid_y][mid_x] == "c":
        pyautogui.click()
    elif board[mid_y][mid_x] == "e":
        clicked = False
        for row in range(len(y_grid)):
            for col in range(len(x_grid)):
                if board[row][col] == "b":
                      pyautogui.click(x_grid[col], y_grid[row])
                      pyautogui.click(x_grid[col], y_grid[row])
                      clicked = True
                      
        if not clicked:
            pyautogui.click(x_grid[(int)(len(x_grid)/4)], y_grid[mid_y])
    
    while True:
        pyautogui.moveTo((x_grid[-1] - x_grid[-2]) + x_grid[-1] , y_grid[0])
        screen = np.array(pyautogui.screenshot())

        board = read_board(x_grid, y_grid, screen)

        start_ai(x_grid, y_grid, board)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
