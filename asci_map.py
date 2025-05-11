import json
import re
import sys

def parse_coordinate(coord_str):
    """
    Parse a coordinate string like '15N, 22W' into numerical x and y positions.
    """
    x = 0
    y = 0
    parts = coord_str.split(',')
    for part in parts:
        part = part.strip()
        match = re.match(r'(\d+)([NSEW])', part, re.I)
        if match:
            value = int(match.group(1))
            direction = match.group(2).upper()
            if direction == 'N':
                y += value
            elif direction == 'S':
                y -= value
            elif direction == 'E':
                x += value
            elif direction == 'W':
                x -= value
    return x, y

def read_locations(data):
    """
    Read locations from JSON data and parse their coordinates.
    """
    locations = data['locations']
    loc_positions = {}
    loc_data = {}
    for loc in locations:
        name = loc['name']
        coord_str = loc['coordinates']
        x, y = parse_coordinate(coord_str)
        loc_positions[name] = (x, y)
        loc_data[name] = loc
    return loc_positions, loc_data

def build_grid(loc_positions):
    """
    Build a grid based on the min and max coordinates of the locations.
    """
    xs = [pos[0] for pos in loc_positions.values()]
    ys = [pos[1] for pos in loc_positions.values()]
    min_x = min(xs) - 2
    max_x = max(xs) + 2
    min_y = min(ys) - 2
    max_y = max(ys) + 2
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    return grid, min_x, min_y

def place_rooms(grid, loc_positions, min_x, min_y):
    """
    Place rooms on the grid based on their coordinates.
    """
    loc_grid_positions = {}
    for name, (x, y) in loc_positions.items():
        grid_x = x - min_x
        grid_y = y - min_y
        loc_grid_positions[name] = (grid_x, grid_y)
        grid[grid_y][grid_x] = 'R'  # Use 'R' to represent a room
    return loc_grid_positions

def draw_connections(grid, loc_data, loc_grid_positions):
    """
    Draw connections (corridors) between rooms based on connectivity information.
    """
    for name, loc in loc_data.items():
        x1, y1 = loc_grid_positions[name]
        for connected_name in loc['connectivity']:
            if connected_name in loc_grid_positions:
                x2, y2 = loc_grid_positions[connected_name]
                draw_line(grid, x1, y1, x2, y2)

def draw_line(grid, x1, y1, x2, y2):
    """
    Draw a line (corridor) between two points on the grid using Bresenham's algorithm.
    """
    dx = x2 - x1
    dy = y2 - y1
    x, y = x1, y1

    sx = 1 if dx > 0 else -1 if dx < 0 else 0
    sy = 1 if dy > 0 else -1 if dy < 0 else 0

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        err = dx / 2.0
        while x != x2:
            x += sx
            err -= dy
            if err < 0:
                y += sy
                err += dx
            if grid[y][x] == ' ':
                grid[y][x] = '.'
    else:
        err = dy / 2.0
        while y != y2:
            y += sy
            err -= dx
            if err < 0:
                x += sx
                err += dy
            if grid[y][x] == ' ':
                grid[y][x] = '.'

def print_grid(grid):
    """
    Print the grid to display the ASCII dungeon map.
    """
    for row in grid[::-1]:  # Reverse to print from top to bottom
        print(''.join(row))

def main():
    # Set default filename
    default_filename = 'gnomengarde.json'

    # Check if a filename was provided as a command-line argument
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = default_filename

    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file '{filename}': {e}")
        sys.exit(1)

    loc_positions, loc_data = read_locations(data)
    grid, min_x, min_y = build_grid(loc_positions)
    loc_grid_positions = place_rooms(grid, loc_positions, min_x, min_y)
    draw_connections(grid, loc_data, loc_grid_positions)
    print_grid(grid)

if __name__ == "__main__":
    main()
