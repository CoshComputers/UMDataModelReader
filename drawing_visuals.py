import textwrap
import plotly.graph_objects as go

from typing import List, Dict, Tuple


def wrap_text(text: str, max_line_length: int) -> str:
    wrapped_lines = textwrap.wrap(text, width=max_line_length)
    return '<br>'.join(wrapped_lines)

def create_text_element(x: float, y: float, height: float, text: str, text_color: str = '#000000') -> go.Scatter:
    """Utility function to create a text element."""

    new_y = y + (height / 2)
    return go.Scatter(
        x=[x], y=[new_y],
        mode="text",
        text=wrap_text(text, 15),
        textposition="middle center",
        textfont=dict(color=text_color, size=12, family="Arial", weight="bold"),
        hoverinfo="skip",
        showlegend=False,
    )

def create_artifact_table(process_to_artifacts, centered_process_top, centered_process_bottom):
    """Create a table of artifact names, source processes, and destination processes with customized styles."""
    # Lists to hold the table data
    artifact_names = []
    source_processes = []
    destination_processes = []

    for (source_id, destination_id), artifacts in process_to_artifacts.items():
        source_process = next((p for p in centered_process_top if p['id'] == source_id), None)
        destination_process = next((p for p in centered_process_bottom if p['id'] == destination_id), None)

        if source_process and destination_process:
            for artifact in artifacts:
                artifact_names.append(wrap_text(artifact['artifact_name'],20))
                source_processes.append(wrap_text(source_process['name'],20))
                destination_processes.append(wrap_text(destination_process['name'], 20))

    # Create the table trace with customized styles
    table_trace = go.Table(
        domain=dict(x=[0.8, 1], y=[0.5, 1]),
        header=dict(
            values=['<b>Artifact Name</b>', '<b>Source Process</b>', '<b>Destination Process</b>'],
            fill_color='black',
            align='left',
            font=dict(color='#00FF00', size=10),
            line_color='darkslategray'
        ),
        cells=dict(
            values=[artifact_names, source_processes, destination_processes],
            fill_color='darkslategray',  # Dark background for content rows
            align='left',
            font=dict(color='limegreen', size=9),
            line_color='darkslategray',
            height=25,
        )
    )

    return table_trace

def create_bezier_curve(start: Tuple[float, float], end: Tuple[float, float], color: str) -> Dict:
    """Return a Bezier curve shape between start and end points with a specified color."""
    control_point_1 = (start[0], start[1] + (end[1] - start[1]) * 0.5)
    control_point_2 = (end[0], start[1] + (end[1] - start[1]) * 0.5)

    path = f'M {start[0]},{start[1]} C {control_point_1[0]},{control_point_1[1]} {control_point_2[0]},{control_point_2[1]} {end[0]},{end[1]}'

    return dict(
        type="path",
        path=path,
        line=dict(color=color, width=2),
        layer='below'
    )

def create_artifact_connections(process_to_artifacts: dict,
                                centered_process_top: list[dict],
                                centered_process_bottom: list[dict],
                                show_artifact_names: bool) -> tuple[list[go.Scatter], list[dict]]:
    """Create connections between top and bottom processes based on artifact relationships."""
    connections = []
    annotations = []
    toggle_position = True
    for (source_id, destination_id), artifacts in process_to_artifacts.items():
        source_process = next((p for p in centered_process_top if p['id'] == source_id), None)
        destination_process = next((p for p in centered_process_bottom if p['id'] == destination_id), None)

        if source_process and destination_process:

            artifact_names = ', '.join([artifact['artifact_name'] for artifact in artifacts])
            hover_text = f"Artifacts: {artifact_names}"

            connection = go.Scatter(
                x=[source_process['x'], destination_process['x']],
                y=[source_process['y'], destination_process['y'] + destination_process['draw_height']],
                mode='lines',
                line=dict(color=destination_process['color'], width=2),
                hovertext=hover_text,
                hoverinfo='text'
            )
            connections.append(connection)

    return connections, annotations

def create_text_element(x: float, y: float, height: float, text: str, text_color: str = '#000000') -> go.Scatter:
    """Utility function to create a text element."""
    new_y = y + (height / 2)
    return go.Scatter(
        x=[x], y=[new_y],
        mode="text",
        text=wrap_text(text, 15),
        textposition="middle center",
        textfont=dict(color=text_color, size=12, family="Arial", weight="bold"),
        hoverinfo="skip",
        showlegend=False,
    )

def create_boxes(centered_data: List[Dict], x_spacing: float) -> List[Dict]:
    """Utility function to create box shapes."""
    shapes: List[Dict] = []
    for data in centered_data:
        shapes.append(dict(
            type="rect",
            x0=data['x'] - x_spacing / 2, x1=data['x'] + x_spacing / 2,
            y0=data['y'], y1=data['y'] + data['draw_height'],
            line=dict(color='#f5f5f5', width=2),
            fillcolor=data['color'],
            layer='below'
        ))
    return shapes
