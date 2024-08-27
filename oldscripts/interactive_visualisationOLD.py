import textwrap
import tkinter as tk
from tkinter import filedialog
from typing import List, Dict, Tuple

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from data_processing import load_data, process_data

BOX_HEIGHT = 100
PRACTICE_Y_TOP = 0.9
PROCESS_Y_TOP = 0.65
PROCESS_Y_BOTTOM = 0.2
PRACTICE_Y_BOTTOM = 0.05
# Initialize Dash application
app = dash.Dash(__name__)

# Global variable to store the processed graphics data
graphics_data: Dict = None

def wrap_text(text: str, max_line_length: int) -> str:
    wrapped_lines = textwrap.wrap(text, width=max_line_length)
    return '<br>'.join(wrapped_lines)

def create_layout():
    app.layout = html.Div([
        html.Label("Select Practice", style={'margin-right': '10px', 'color': 'lightblue'}),
        dcc.Dropdown(
            id='practice-dropdown',
            options=[{'label': data['name'], 'value': practice_id} for practice_id, data in graphics_data['practice_top'].items()],
            multi=True,  # Allow multiple selections
            placeholder="Select practices",
            style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'middle'}
        ),
        html.Br(),
        dcc.Checklist(
            id='toggle-artifact-names',
            options=[{'label': 'Show Artifact Name Table', 'value': 'show_names'}],
            value=[],
            style={'color': 'lightblue', 'margin-left': '10px'}
        ),
        html.Br(),
        dcc.Checklist(
            id='toggle-practice-only',  # New checklist for practice-only toggle
            options=[{'label': 'Practice Only View', 'value': 'practice_only'}],
            value=[],
            style={'color': 'lightblue', 'margin-left': '10px'}
        ),
        html.Div(
            dcc.Graph(id='main-graph',
                      figure=go.Figure(),
                      style={'height': '100%', 'width': '100%'},
                      config={'responsive': True}),
            style={'flex': '1 1 auto', 'display': 'flex', 'flexDirection': 'column', 'min-height': '0'}
        )
    ], style={'backgroundColor': '#515151', 'height': '100vh', 'display': 'flex', 'flexDirection': 'column'})
    return app.layout

@app.callback(
    Output('main-graph', 'figure'),
    [Input('practice-dropdown', 'value'),
     Input('toggle-artifact-names', 'value'),
     Input('toggle-practice-only', 'value')]  # New input for practice-only toggle
)
def update_graph(selected_practices, toggle_artifact_names, toggle_practice_only):
    show_artifact_names = 'show_names' in toggle_artifact_names
    practice_only = 'practice_only' in toggle_practice_only
    return create_figure(selected_practices, show_artifact_names, practice_only)

'''***************************** CREATE DRAWING FUNCTIONS *************************************'''
def center_positions(data: Dict[str, Dict], y_position: float, x_spacing: float) -> List[Dict]:
    centered_data: List[Dict] = []

    num_elements = len(data)
    if num_elements == 0:
        return centered_data  # No elements to position

    start_x = 0.5 - ((num_elements - 1) * x_spacing / 2)

    for i, (item_id, item_data) in enumerate(data.items()):
        item_data['x'] = start_x + i * x_spacing
        item_data['y'] = y_position
        item_data['draw_height'] = item_data['height'] / 1000
        item_data['id'] = item_id  # Ensure the ID is preserved
        centered_data.append(item_data)

    return centered_data

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

'''******************************************* FILTER FUNCTIONS *******************************************************'''

def filter_practices_only(selected_practices: List[str]) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """Filter practices based on selected practices, identifying connections between practices."""

    # Step 1: Filter the top practices as usual
    if selected_practices:
        filtered_practices_top = {pid: pdata for pid, pdata in graphics_data['practice_top'].items() if pid in selected_practices}
    else:
        filtered_practices_top = graphics_data['practice_top']

    # Step 2: Identify bottom practices based on relationships from filtered top practices
    filtered_practices_bottom = {}
    process_to_artifacts = graphics_data.get('process_to_artifacts', {})

    for (source_pid, dest_pid), artifacts in process_to_artifacts.items():
        source_practice_id = graphics_data['process_top'][source_pid]['practice_id']
        dest_practice_id = graphics_data['process_bottom'][dest_pid]['practice_id']

        # Only add to filtered bottom practices if source practice is in the filtered top practices
        if source_practice_id in filtered_practices_top:
            if dest_practice_id in graphics_data['practice_bottom']:
                filtered_practices_bottom[dest_practice_id] = graphics_data['practice_bottom'][dest_practice_id]

    return filtered_practices_top, filtered_practices_bottom

def collect_related_processes(filtered_practices_top: dict, filtered_practices_bottom: dict) -> Tuple[List[dict], List[dict]]:
    """Collect processes related to the selected practices for use in the artifact table."""
    related_processes_top = []
    related_processes_bottom = []

    for practice_id in filtered_practices_top.keys():
        # Collect processes associated with the top practices
        related_processes_top.extend([pdata for pid, pdata in graphics_data['process_top'].items() if pdata['practice_id'] == practice_id])

    for practice_id in filtered_practices_bottom.keys():
        # Collect processes associated with the bottom practices
        related_processes_bottom.extend([pdata for pid, pdata in graphics_data['process_bottom'].items() if pdata['practice_id'] == practice_id])

    return related_processes_top, related_processes_bottom



def filter_data(selected_practices: List[str]) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """Function to filter practices and processes based on selected practices."""
    filtered_practices_top = {pid: pdata for pid, pdata in graphics_data['practice_top'].items() if pid in selected_practices}
    filtered_processes_top = {pid: pdata for pid, pdata in graphics_data['process_top'].items() if pdata['practice_id'] in selected_practices}

    return filtered_practices_top, filtered_processes_top


'''********************************** Analyze Relationship Functions **************************************************'''
def analyze_practice_relationships(filtered_practices_top: Dict[str, Dict], filtered_practices_bottom: Dict[str, Dict]) -> List[Tuple[str, str]]:
    """Analyze and capture relationships between top and bottom practices based on process interactions."""

    practice_relationships = []
    process_to_artifacts = graphics_data.get('process_to_artifacts', {})

    for (source_pid, dest_pid), artifacts in process_to_artifacts.items():
        # Identify source and destination practices
        source_practice_id = graphics_data['process_top'][source_pid]['practice_id']
        dest_practice_id = graphics_data['process_bottom'][dest_pid]['practice_id']

        # Ensure both practices are in the filtered sets
        if source_practice_id in filtered_practices_top and dest_practice_id in filtered_practices_bottom:
            practice_relationships.append((source_practice_id, dest_practice_id))

    return practice_relationships


def analyze_relationships(filtered_processes_top):
    """Function to analyze and capture relationships between source and destination processes."""
    process_to_artifacts = graphics_data.get('process_to_artifacts', {})
    relevant_artifacts = []
    # Identify relevant artifacts from the top processes
    for pid in filtered_processes_top:
        for (source_pid, dest_pid), artifacts in process_to_artifacts.items():
            if source_pid == pid:
                relevant_artifacts.extend([rel['artifact_id'] for rel in artifacts])

    # Determine destination processes based on the relevant artifacts
    filtered_processes_bottom = {}
    for (source_pid, dest_pid), artifacts in process_to_artifacts.items():
        if dest_pid in graphics_data['process_bottom'] and source_pid in filtered_processes_top:
            filtered_processes_bottom[dest_pid] = graphics_data['process_bottom'][dest_pid]

    return filtered_processes_bottom

'''************************** MAIN DRAWING FUNCTION ****************************************'''
def create_full_figure(selected_practices: List[str], show_artifact_names: bool) -> go.Figure:
    fig = go.Figure()

    if selected_practices:
        filtered_practices_top, filtered_processes_top = filter_data(selected_practices)
        filtered_processes_bottom = analyze_relationships(filtered_processes_top)
        filtered_practices_bottom: Dict[str, Dict] = {}
        for pdata in filtered_processes_bottom.values():
            practice_id = pdata['practice_id']
            if practice_id in graphics_data['practice_bottom']:
                filtered_practices_bottom[practice_id] = graphics_data['practice_bottom'][practice_id]
        # Set range to full extent if filtered
        x_range = [0, 1]
    else:
        filtered_practices_top = graphics_data['practice_top']
        filtered_practices_bottom = graphics_data['practice_bottom']
        filtered_processes_top = graphics_data['process_top']
        filtered_processes_bottom = graphics_data['process_bottom']
        # Set a centered range for the full view
        x_range = [0.42, 0.58]

    max_elements = max(len(filtered_practices_top), len(filtered_processes_top), len(filtered_processes_bottom), len(filtered_practices_bottom))
    x_spacing = 1 / (max_elements + 1)

    centered_practice_top = center_positions(filtered_practices_top, PRACTICE_Y_TOP, x_spacing)
    centered_process_top = center_positions(filtered_processes_top, PROCESS_Y_TOP, x_spacing)
    centered_process_bottom = center_positions(filtered_processes_bottom, PROCESS_Y_BOTTOM, x_spacing)
    centered_practice_bottom = center_positions(filtered_practices_bottom, PRACTICE_Y_BOTTOM, x_spacing)

    shapes = []
    traces = []

    # Create connections between practices and processes
    for process_data in centered_process_top:
        practice_data = next((p for p in centered_practice_top if p['id'] == process_data['practice_id']), None)
        if practice_data:
            shapes.append(create_bezier_curve(
                (practice_data['x'], practice_data['y']),
                (process_data['x'], process_data['y'] + process_data['draw_height']),
                practice_data['color']
            ))

    for process_data in centered_process_bottom:
        practice_data = next((p for p in centered_practice_bottom if p['id'] == process_data['practice_id']), None)
        if practice_data:
            shapes.append(create_bezier_curve(
                (practice_data['x'], practice_data['y'] + practice_data['draw_height']),
                (process_data['x'], process_data['y']),
                practice_data['color']
            ))

    # Create artifact connections
    artifact_connections, artifact_annotations = create_artifact_connections(
        graphics_data['process_to_artifacts'],
        centered_process_top,
        centered_process_bottom,
        show_artifact_names
    )
    traces.extend(artifact_connections)

    # Add annotations to the figure if show_artifact_names is True
    # Create and add the table if show_artifact_names is True
    if show_artifact_names:
        artifact_table = create_artifact_table(graphics_data['process_to_artifacts'], centered_process_top, centered_process_bottom)
        fig.add_trace(artifact_table)

    # Update the layout to position the table in the top right
    if show_artifact_names:
        fig.update_layout(
            annotations=[dict(
                #text="Artifacts Table",
                x=1,  # Position it on the right
                y=1,  # Position it at the top
                xref="paper",
                yref="paper",
                showarrow=False,
                align="right",
                xanchor="right",
                yanchor="top"
            )]
        )


    # Add boxes for practices and processes
    shapes.extend(create_boxes(centered_practice_top + centered_practice_bottom + centered_process_top + centered_process_bottom, x_spacing))

    # Add text labels for practices and processes
    for data in centered_practice_top:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))
    for data in centered_process_top:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))
    for data in centered_process_bottom:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))
    for data in centered_practice_bottom:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))

    fig.update_layout(shapes=shapes)
    fig.add_traces(traces)

    # Final layout update
    fig.update_layout(
        title="Interactive Process and Practice Visualization",
        plot_bgcolor='#515151',
        paper_bgcolor='#515151',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=x_range,
            rangeslider=dict(
                visible=True,
                thickness=0.05,
                bgcolor='#333333',
                bordercolor="lightblue",
                borderwidth=5,
                yaxis=dict(rangemode="fixed"),
            ),
            rangeselector=dict(visible=True),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[0, 1],
        ),
        hovermode='closest',
        margin=dict(l=40, r=40, t=100, b=40),
        height=800,
        showlegend=False,
        dragmode='zoom',
        font=dict(color='lightblue')
    )

    return fig

def create_practice_only_figure(selected_practices: List[str], show_artifact_names: bool) -> go.Figure:
    fig = go.Figure()

    # Filter practices only and identify relationships
    filtered_practices_top, filtered_practices_bottom = filter_practices_only(selected_practices)
    practice_relationships = analyze_practice_relationships(filtered_practices_top, filtered_practices_bottom)

    # Set range to full extent since it's filtered
    x_range = [0, 1]

    # Calculate x_spacing based on the maximum number of elements in any row
    max_elements = max(len(filtered_practices_top), len(filtered_practices_bottom))
    x_spacing = 1 / (max_elements + 1)

    centered_practice_top = center_positions(filtered_practices_top, PRACTICE_Y_TOP, x_spacing)
    centered_practice_bottom = center_positions(filtered_practices_bottom, PRACTICE_Y_BOTTOM, x_spacing)

    # Collect the process data for the artifact table
    filtered_processes_top, filtered_processes_bottom = collect_related_processes(filtered_practices_top, filtered_practices_bottom)


    shapes = []
    traces = []

    # Create connections between practices based on the relationships
    for (source_practice_id, dest_practice_id) in practice_relationships:
        source_practice = next((p for p in centered_practice_top if p['id'] == source_practice_id), None)
        dest_practice = next((p for p in centered_practice_bottom if p['id'] == dest_practice_id), None)
        if source_practice and dest_practice:
            shapes.append(create_bezier_curve(
                (source_practice['x'], source_practice['y']),
                (dest_practice['x'], dest_practice['y'] + dest_practice['draw_height']),
                source_practice['color']
            ))

    # Add annotations to the figure if show_artifact_names is True
    # Create and add the table if show_artifact_names is True
    if show_artifact_names:
        artifact_table = create_artifact_table(graphics_data['process_to_artifacts'], filtered_processes_top, filtered_processes_bottom)
        fig.add_trace(artifact_table)

    # Update the layout to position the table in the top right
    if show_artifact_names:
        fig.update_layout(
            annotations=[dict(
                #text="Artifacts Table",
                x=1,  # Position it on the right
                y=1,  # Position it at the top
                xref="paper",
                yref="paper",
                showarrow=False,
                align="right",
                xanchor="right",
                yanchor="top"
            )]
        )


    # Add boxes for practices
    shapes.extend(create_boxes(centered_practice_top + centered_practice_bottom, x_spacing))

    # Add text labels for practices
    for data in centered_practice_top:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))
    for data in centered_practice_bottom:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))

    fig.update_layout(shapes=shapes)
    fig.add_traces(traces)

    # Final layout update
    fig.update_layout(
        title="Practice Relationship Visualization",
        plot_bgcolor='#515151',
        paper_bgcolor='#515151',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=x_range,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[0, 1],
        ),
        hovermode='closest',
        margin=dict(l=40, r=40, t=100, b=40),
        height=800,
        showlegend=False,
        dragmode='zoom',
        font=dict(color='lightblue')
    )

    return fig


def create_figure(selected_practices: List[str] = None, show_artifact_names: bool = False, practice_only: bool = False) -> go.Figure:
    if practice_only:
        return  create_practice_only_figure(selected_practices,show_artifact_names)
    else:
        return create_full_figure(selected_practices, show_artifact_names)



def main() -> None:
    global graphics_data

    # Create a Tk root widget, which will act as the file dialog's parent
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open the file dialog to select an Excel file
    file_name = filedialog.askopenfilename(
        title="Select the Excel file",
        filetypes=[("Excel files", "*.xlsx *.xls")]  # Allow only Excel files
    )

    if not file_name:
        print("No file selected. Exiting.")
        return

    # Load and process the data
    print("1 - Loading Data")
    practices_df, processes_df, artifacts_df, artifact_interactions_df = load_data(file_name)
    print("2 - Processing Data")
    graphics_data = process_data(practices_df, processes_df, artifact_interactions_df, artifacts_df)
    print("3 - Drawing Graphic")
    app.layout = create_layout()

    # Run the Dash app
    app.run_server(debug=True)

if __name__ == "__main__":
    main()

