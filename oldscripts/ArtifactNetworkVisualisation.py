import numpy as np

TOTAL_HEIGHT = 80
# Constants for separation
SEPARATION_GAP = 20     #Seperation between the Parent / child practice process boxes
SEPARATION_PRACTICE = TOTAL_HEIGHT - SEPARATION_GAP + 10  # Separation between source and destination practice boxes

PRACTICE_BOX_HEIGHT = 2
PROCESS_BOX_HEIGHT = 4
PRACTICE_BOX_WIDTH = 10
PROCESS_BOX_WIDTH = 12
Y_MARGIN = 10
X_MARGIN = 1
MIN_TOTAL_WIDTH = 200  # Minimum width to ensure proper centering


def generate_pastel_colors(n):
    """Generate n random pastel colors."""
    colors = []
    for i in range(n):
        base_color = np.random.rand(3)
        pastel_color = (base_color + np.ones(3)) / 2
        colors.append(pastel_color)
    return colors


def calculate_box_details(practices_df, processes_df):
    """Main function to calculate box details and total dimensions."""
    practice_colors = generate_pastel_colors(len(practices_df))
    practice_color_map = {row['id']: practice_colors[i] for i, (index, row) in enumerate(practices_df.iterrows())}

    total_width = calculate_total_width(practices_df, processes_df)
    total_height_required = TOTAL_HEIGHT

    box_details = {
        'Practices': [],
        'Processes': []
    }

    practice_start_x = calculate_start_position(total_width, len(practices_df), PRACTICE_BOX_WIDTH)
    practice_source_y = TOTAL_HEIGHT - Y_MARGIN
    practice_dest_y = practice_source_y - SEPARATION_PRACTICE

    process_start_x = calculate_start_position(total_width, len(processes_df), PROCESS_BOX_WIDTH)
    process_source_y = practice_source_y - SEPARATION_GAP
    process_dest_y = practice_dest_y + SEPARATION_GAP
    # Add practice boxes (source and destination)
    add_practice_boxes(box_details, practices_df, practice_start_x, practice_source_y, PRACTICE_BOX_HEIGHT, practice_color_map)
    add_practice_boxes(box_details, practices_df, practice_start_x, practice_dest_y, PRACTICE_BOX_HEIGHT, practice_color_map, is_destination=True)

    # Add process boxes (source and destination)
    add_process_boxes(box_details, processes_df, process_start_x, process_source_y, PROCESS_BOX_HEIGHT, practice_color_map)
    add_process_boxes(box_details, processes_df, process_start_x, process_dest_y, PROCESS_BOX_HEIGHT, practice_color_map, is_destination=True)

    return box_details, total_width, total_height_required

def calculate_total_width(practices_df, processes_df):
    """Calculate the total width needed for the layout."""
    total_practice_width = len(practices_df) * (PRACTICE_BOX_WIDTH + X_MARGIN) - X_MARGIN
    total_process_width = len(processes_df) * (PROCESS_BOX_WIDTH + X_MARGIN) - X_MARGIN
    calculated_total_width = max(total_practice_width, total_process_width)
    return max(MIN_TOTAL_WIDTH, calculated_total_width)

def calculate_start_position(total_width, total_items, box_width):
    """Calculate the starting X position for centering the boxes."""
    total_item_width = total_items * (box_width + X_MARGIN) - X_MARGIN
    return (total_width - total_item_width) / 2 if total_items > 0 else 0

def add_practice_boxes(box_details, practices_df, start_x, start_y, y_offset, practice_color_map, is_destination=False):
    """Add practice boxes to the box details."""
    for i, (index, row) in enumerate(practices_df.iterrows()):
        x = start_x + i * (PRACTICE_BOX_WIDTH + X_MARGIN)
        y = start_y + y_offset
        box_details['Practices'].append({
            'id': row['id'],
            'name': row['name'],
            'x': x,
            'y': y,
            'width': PRACTICE_BOX_WIDTH,
            'height': PRACTICE_BOX_HEIGHT,
            'color': practice_color_map[row['id']],
            'is_destination': is_destination
        })

def add_process_boxes(box_details, processes_df, start_x, start_y, y_offset, practice_color_map, is_destination=False):
    """Add process boxes to the box details."""
    for i, (index, row) in enumerate(processes_df.iterrows()):
        x = start_x + i * (PROCESS_BOX_WIDTH + X_MARGIN)
        y = start_y + y_offset
        color = practice_color_map.get(row['practice_id'], [0.6, 1.0, 0.6])
        box_details['Processes'].append({
            'id': row['id'],
            'name': row['name'],
            'practice_id': row['practice_id'],
            'x': x,
            'y': y,
            'width': PROCESS_BOX_WIDTH,
            'height': PROCESS_BOX_HEIGHT,
            'color': color,
            'is_destination': is_destination
        })
