import colorsys
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

import pandas as pd

# Constants for layout
BOX_WIDTH: int = 200
BOX_HEIGHT: int = 100
PRACTICE_Y_TOP: int = 100
PROCESS_Y_TOP: int = 300
PROCESS_Y_BOTTOM: int = 500
PRACTICE_Y_BOTTOM: int = 700
PRACTICE_SPACING: int = 300
PROCESS_SPACING: int = 200


# Define 38 neon colors
PREDEFINED_COLORS = [
    "#FF00FF", "#39FF14", "#FF073A", "#FFAA1D", "#00FFFF", "#FF00CC", "#CCFF00", "#FF33FF",
    "#FF6700", "#FFFF66", "#66FF66", "#66FFFF", "#FF66FF", "#FF6666", "#FF3399", "#FF6633",
    "#CCFF33", "#00FF66", "#00FFCC", "#33FF33", "#FF3399", "#CC33FF", "#FF33CC", "#33FFFF",
    "#FF9933", "#33FF66", "#FF0033", "#00FF99", "#FF00FF", "#99FF00", "#00FF00", "#99FF33",
    "#FF3366", "#33FF99", "#FF99FF", "#99FFFF", "#FF6699", "#FFCC00"
]


def assign_practice_colors(practices_df: pd.DataFrame) -> dict[str, str]:
    """Assign predefined colors to each practice for visualization."""
    unique_practices = practices_df.set_index('id')
    practice_colors = {}

    for i, practice_id in enumerate(unique_practices.index):
        color = PREDEFINED_COLORS[i % len(PREDEFINED_COLORS)]  # Assign colors in a round-robin fashion if more practices than colors
        practice_colors[practice_id] = color

    return practice_colors


def generate_random_pastel_color() -> str:
    """Generate a random pastel color."""
    h = random.random()
    s = 0.5 + random.random() * 0.5  # Saturation between 0.5 and 1
    l = 0.6 + random.random() * 0.4  # Lightness between 0.6 and 1
    rgb = colorsys.hls_to_rgb(h, l, s)
    rgb = [int(x * 255) for x in rgb]
    return f'rgb({rgb[0]},{rgb[1]},{rgb[2]})'

import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def load_data(file_name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data from the Excel file."""
    with pd.ExcelFile(file_name) as xls:  # Use a context manager to ensure the file is closed
        with ThreadPoolExecutor() as executor:
            practices_df = executor.submit(pd.read_excel, xls, 'Practices').result()[['id', 'name']]
            processes_df = executor.submit(pd.read_excel, xls, 'Processes').result()[['id', 'name', 'practice_id', 'value_stream_id']]
            artifacts_df = executor.submit(pd.read_excel, xls, 'Artifacts').result()[['id', 'artifact_name']]
            artifact_interactions_df = executor.submit(pd.read_excel, xls, 'Process Interactions').result()[['artifact_id', 'source_process_id', 'destination_process_id']]

    # The file will be closed here when the context manager exits
    return practices_df, processes_df, artifacts_df, artifact_interactions_df



def map_practices_to_processes(processes_df: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    """Map practices to their corresponding processes."""
    practice_to_processes = processes_df.groupby('practice_id').agg(list)
    practice_to_processes = practice_to_processes[['id', 'name']].to_dict(orient='index')
    practice_to_processes = {k: [{'id': id_, 'name': name_} for id_, name_ in zip(v['id'], v['name'])] for k, v in practice_to_processes.items()}
    return practice_to_processes

def map_processes_to_artifacts(artifact_interactions_df: pd.DataFrame, artifacts_df: pd.DataFrame) -> dict[tuple[str, str], list[dict[str, str]]]:
    """Map processes to artifacts based on source and destination process IDs, including artifact names."""
    # Merge artifact interactions with artifacts to get the artifact names
    artifact_interactions_with_names = pd.merge(
        artifact_interactions_df,
        artifacts_df,
        left_on='artifact_id',
        right_on='id',
        how='left'
    )

    # Group by source and destination process IDs and aggregate artifact details
    process_to_artifacts = artifact_interactions_with_names.groupby(['source_process_id', 'destination_process_id']).agg(list)
    process_to_artifacts = process_to_artifacts[['artifact_id', 'artifact_name']].to_dict(orient='index')

    # Structure the dictionary to include both artifact_id and artifact_name
    process_to_artifacts = {
        k: [{'artifact_id': art_id, 'artifact_name': art_name}
            for art_id, art_name in zip(v['artifact_id'], v['artifact_name'])]
        for k, v in process_to_artifacts.items()
    }
    return process_to_artifacts

def assign_r_practice_colors(practices_df: pd.DataFrame) -> dict[str, str]:
    """Assign unique colors to each practice for visualization."""
    unique_practices = practices_df.set_index('id')
    used_colors = set()  # Keep track of used colors
    practice_colors = {}

    for practice_id in unique_practices.index:
        while True:
            color = generate_random_pastel_color()
            if color not in used_colors:
                used_colors.add(color)
                practice_colors[practice_id] = color
                break

    return practice_colors

def calculate_practice_positions(practice_to_processes: dict[str, list[dict[str, str]]], practice_colors: dict[str, str], unique_practices: pd.DataFrame) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Calculate the positions for practice boxes on the top and bottom rows."""
    practice_graphics_top = {}
    practice_graphics_bottom = {}
    for index, practice_id in enumerate(practice_to_processes):
        x_position = index * PRACTICE_SPACING
        # Top row (Row 1)
        practice_graphics_top[practice_id] = {
            'x': x_position,
            'y': PRACTICE_Y_TOP,
            'width': BOX_WIDTH,
            'height': BOX_HEIGHT - 10,
            'color': practice_colors.get(practice_id, 'rgb(255, 255, 255)'),
            'name': unique_practices.loc[practice_id, 'name']
        }
        # Bottom row (Row 4)
        practice_graphics_bottom[practice_id] = {
            'x': x_position,
            'y': PRACTICE_Y_BOTTOM,
            'width': BOX_WIDTH,
            'height': BOX_HEIGHT - 10,
            'color': practice_colors.get(practice_id, 'rgb(255, 255, 255)'),
            'name': unique_practices.loc[practice_id, 'name']
        }
    return practice_graphics_top, practice_graphics_bottom

def calculate_process_positions(practice_to_processes: dict[str, list[dict[str, str]]], practice_colors: dict[str, str]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Calculate the positions for process boxes on the top and bottom rows."""
    process_graphics_top = {}
    process_graphics_bottom = {}
    for practice_id, processes in practice_to_processes.items():
        for i, process in enumerate(processes):
            x_position = i * PROCESS_SPACING
            # Top row (Row 2)
            process_graphics_top[process['id']] = {
                'x': x_position,
                'y': PROCESS_Y_TOP,
                'width': BOX_WIDTH,
                'height': BOX_HEIGHT + 85,
                'color': practice_colors.get(practice_id, 'rgb(255, 255, 255)'),
                'name': process['name'],
                'practice_id': practice_id  # Include practice_id for easier filtering
            }
            # Bottom row (Row 3)
            process_graphics_bottom[process['id']] = {
                'x': x_position,
                'y': PROCESS_Y_BOTTOM,
                'width': BOX_WIDTH,
                'height': BOX_HEIGHT + 85,
                'color': practice_colors.get(practice_id, 'rgb(255, 255, 255)'),
                'name': process['name'],
                'practice_id': practice_id  # Include practice_id for easier filtering
            }
    return process_graphics_top, process_graphics_bottom

def calculate_value_stream_positions(processes_df: pd.DataFrame, practice_colors: dict[str, str]) -> List[Dict[str, Any]]:
    """Calculate positions for processes grouped by value streams, allowing for multiple columns."""
    value_stream_order = ['IT4ITVS01', 'IT4ITVS02', 'IT4ITVS03', 'IT4ITVS04', 'IT4ITVS05', 'IT4ITVS06', 'IT4ITVS07', 'MOZVS01']
    x_spacing = 0.2
    y_spacing = 0.4
    max_columns = 1
    positions = []

    for value_stream_id in value_stream_order:
        value_stream_processes = processes_df[processes_df['value_stream_id'] == value_stream_id]
        num_processes = len(value_stream_processes)
        num_columns = min(max_columns, num_processes)
        num_rows = (num_processes + num_columns - 1) // num_columns

        x_base = 0.15 * (value_stream_order.index(value_stream_id) + 1)
        y_base = 0.95

        #if value_stream_id in ['IT4ITVS07', 'MOZVS01']:
        #    y_base -= 0.3

        for i, (_, process) in enumerate(value_stream_processes.iterrows()):
            column = i % num_columns
            row = i // num_columns

            x_position = x_base + column * x_spacing
            y_position = y_base - row * y_spacing

            positions.append({
                'id': process['id'],
                'name': process['name'],
                'practice_id': process['practice_id'],
                'value_stream_id': value_stream_id,  # Include value_stream_id here
                'x': x_position,
                'y': y_position,
                'draw_height': 0.5,
                'color': practice_colors.get(process['practice_id'], '#FFFFFF')
            })

    return positions



def process_data(practices_df: pd.DataFrame, processes_df: pd.DataFrame, artifact_interactions_df: pd.DataFrame, artifacts_df: pd.DataFrame) -> dict:
    """Process all data to prepare for visualization, including value stream positions."""
    # Original processing
    practice_to_processes = map_practices_to_processes(processes_df)
    process_to_artifacts = map_processes_to_artifacts(artifact_interactions_df, artifacts_df)
    practice_colors = assign_practice_colors(practices_df)

    # Existing practice and process positions (for other visuals)
    practice_graphics_top, practice_graphics_bottom = calculate_practice_positions(practice_to_processes, practice_colors, practices_df.set_index('id'))
    process_graphics_top, process_graphics_bottom = calculate_process_positions(practice_to_processes, practice_colors)

    # New value stream position calculation
    process_positions = calculate_value_stream_positions(processes_df, practice_colors)

    graphics_data = {
        'practice_top': practice_graphics_top,
        'practice_bottom': practice_graphics_bottom,
        'process_top': process_graphics_top,
        'process_bottom': process_graphics_bottom,
        'process_to_artifacts': process_to_artifacts,
        'process_positions': process_positions  # New data for the value stream visualization
    }
    return graphics_data

def find_processes_with_no_destination(processes_df: pd.DataFrame, process_interactions_df: pd.DataFrame) -> List[str]:
    """Identify processes that do not act as a destination in any artifact interaction."""
    destination_processes = set(process_interactions_df['destination_process_id'])
    no_destination_processes = []

    for _, process in processes_df.iterrows():
        if process['id'] not in destination_processes:
            no_destination_processes.append(f"Practice: {process['practice_id']}, Process: {process['name']}")

    return no_destination_processes

def find_artifacts_with_no_source(process_interactions_df: pd.DataFrame, artifacts_df: pd.DataFrame) -> List[str]:
    """Identify artifacts that have no source process in any artifact interaction."""
    source_artifacts = set(process_interactions_df['artifact_id'])
    no_source_artifacts = []

    for _, artifact in artifacts_df.iterrows():
        if artifact['id'] not in source_artifacts:
            no_source_artifacts.append(f"Artifact: {artifact['artifact_name']}")

    return no_source_artifacts


if __name__ == "__main__":
    file_name = 'UnifiedModel.xlsx'
    practices_df, processes_df, artifacts_df, artifact_interactions_df = load_data(file_name)
    graphics_data = process_data(practices_df, processes_df, artifact_interactions_df, artifacts_df)
    # The processed data (graphics_data) can now be used in the visualization script
