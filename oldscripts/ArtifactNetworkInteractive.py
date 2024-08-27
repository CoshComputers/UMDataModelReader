import textwrap

import dash
import dash_core_components as dcc
import pandas as pd
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from ArtifactNetworkVisualisation import calculate_box_details

VP_HEIGHT = 800
BOX_HEIGHT_ADJUSTMENT = 8
BOX_MARGIN = 2

def create_interactive_dashboard(practices_df, processes_df, artifacts_df, process_interactions_df, box_details, total_width, circle_details):
    app = dash.Dash(__name__)

    # Map IDs to labels and add an "All Practices" option
    practice_options = [{'label': 'All Practices', 'value': 'all'}] + \
                       [{'label': row['name'], 'value': row['id']} for _, row in practices_df.iterrows()]
    process_options = [{'label': row['name'], 'value': row['id']} for _, row in processes_df.iterrows()]

    # Updated layout with dropdowns and top menu
    app.layout = html.Div([
        html.Div([
            html.Label("Select Practice", style={'margin-right': '10px', 'color': 'white'}),
            dcc.Dropdown(
                id='practice-selector',
                options=practice_options,
                value='all',  # Default to "All Practices"
                style={'width': '300px', 'display': 'inline-block', 'verticalAlign': 'middle'}
            ),
            html.Label("Select Processes", style={'margin-left': '20px', 'margin-right': '10px', 'color': 'white'}),
            dcc.Dropdown(
                id='process-selector',
                options=process_options,
                multi=True,
                placeholder="Select Processes",
                style={'width': '400px', 'display': 'inline-block', 'verticalAlign': 'middle'}
            ),
        ], style={'width': '100%', 'display': 'flex', 'justify-content': 'center', 'padding': '10px', 'background-color': '#333', 'box-sizing': 'border-box'}),

        # The plot area takes up the full remaining space and full width
        html.Div(id='graph-container',children=[
            dcc.Graph(
                id='interactive-plot',
                figure = go.Figure(),
                config={'responsive': True},
                style={'width': '100%', 'height': '100%'}  # Ensure the graph takes full width and height
            )
        ], style={'width': '100%', 'height': '90%', 'padding': '0', 'margin': '0', 'box-sizing': 'border-box'})
    ], style={'width': '100vw', 'height': '100vh', 'margin': '0', 'padding': '0', 'box-sizing': 'border-box'})

    @app.callback(
        Output('graph-container', 'children'),
        [Input('practice-selector', 'value')]
    )
    def update_plot(selected_practice):
        fig = update_plot_figure(selected_practice, practices_df, processes_df, process_interactions_df)
        fig.show()
        return dcc.Graph(
            id='interactive-plot',
            figure=fig,
            config={'responsive': True},
            style={'width': '100%', 'height': '100%'}
        )

    app.run_server(debug=True)


def update_plot_figure(selected_practice, practices_df, processes_df, process_interactions_df):
    print(f"Selected Practice ID: {selected_practice}")

    # Step 1: Filter practices and processes based on the selected practice
    if selected_practice == 'all':
        filtered_practices_df = practices_df
        filtered_processes_df = processes_df
    else:
        filtered_practices_df = practices_df[practices_df['id'] == selected_practice]
        filtered_processes_df = processes_df[processes_df['practice_id'] == selected_practice]

    # Get the IDs of the filtered processes
    related_process_ids = filtered_processes_df['id'].tolist()

    # Step 2: Filter interactions based on the related process IDs
    filtered_interactions_df = process_interactions_df[
        (process_interactions_df['source_process_id'].isin(related_process_ids)) |
        (process_interactions_df['destination_process_id'].isin(related_process_ids))
        ]

    # Step 3: Combine all related data
    final_processes = processes_df[processes_df['id'].isin(related_process_ids)]
    final_practices = practices_df[practices_df['id'].isin([selected_practice])]

    # If "all" is selected, use the full practices DataFrame
    if selected_practice == 'all':
        final_practices = practices_df

    # Calculate box details and circle location using the filtered practices and processes
    box_details, total_width = calculate_box_details(final_practices, final_processes, 800)

    # Create the interactive plot
    fig = create_interactive_plot(box_details, filtered_interactions_df, total_width, 800)

    return fig





# Color Conversion Functions
def to_rgb(color):
    return 'rgb({}, {}, {})'.format(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))

def to_neon(color):
    r, g, b = color
    neon_r = min(1, r * 1.5)
    neon_g = min(1, g * 1.5)
    neon_b = min(1, b * 1.5)
    return 'rgb({}, {}, {})'.format(int(neon_r * 255), int(neon_g * 255), int(neon_b * 255))

def wrap_text(text, max_line_length):
    """
    Inserts <br> tags into the text to simulate text wrapping.

    Parameters:
    - text (str): The original text string.
    - max_line_length (int): The maximum number of characters per line.

    Returns:
    - str: The text string with <br> tags inserted.
    """
    wrapped_lines = textwrap.wrap(text, width=max_line_length)
    return '<br>'.join(wrapped_lines)

def add_practice_shapes(fig, practices, plot_height, plot_width):
    print("ADDING PRACTICES")
    for practice in practices:
        # Dynamically calculate height based on the plot's height
        dynamic_height = (practice['height'] + BOX_HEIGHT_ADJUSTMENT) * (plot_height / 100)  # Adjust the denominator based on the scale
        dynamic_width = (practice['width']) * (plot_width / 100)  # Similarly for width if needed

        practice_color = to_neon(practice['color'])
        fig.add_shape(
            type="rect",
            x0=practice['x'],
            y0=practice['y'],
            x1=practice['x'] + dynamic_width,
            y1=practice['y'] + dynamic_height,
            line=dict(color='black'),
            fillcolor=practice_color,
            opacity=0.8,
            layer="below"
        )

        # Wrap the text
        wrapped_text = wrap_text(practice['name'], max_line_length=15)  # Adjust max_line_length as needed


        fig.add_trace(go.Scatter(
            x=[practice['x'] + dynamic_width / 2],
            y=[practice['y'] + dynamic_height / 2],
            text=[wrapped_text],
            mode='text',
            textposition='middle center',
            hoverinfo='none',
            showlegend=False,
            textfont=dict(size=12, color='darkgray')
        ))

def add_process_shapes(fig, processes, plot_height, plot_width):

    for process in processes:
        # Dynamically calculate height based on the plot's height
        dynamic_height = (process['height'] + BOX_HEIGHT_ADJUSTMENT) * (plot_height / 100)  # Adjust the denominator based on the scale
        dynamic_width = (process['width']) * (plot_width / 100)  # Similarly for width if needed

        process_color = to_neon(process['color'])
        fig.add_shape(
            type="rect",
            x0=process['x'],
            y0=process['y'],
            x1=process['x'] + dynamic_width,
            y1=process['y'] + dynamic_height,
            line=dict(color='black'),
            fillcolor=process_color,
            opacity=0.8,
            layer="below"
        )

        # Wrap the text
        wrapped_text = wrap_text(process['name'], max_line_length=15)  # Adjust max_line_length as needed


        fig.add_trace(go.Scatter(
            x=[process['x'] + dynamic_width / 2],
            y=[process['y'] + dynamic_height / 2],
            text=[wrapped_text],
            mode='text',
            textposition='middle center',
            hoverinfo='none',
            showlegend=False,
            textfont=dict(size=12, color='darkgray')
        ))

def add_artifact_lines_with_scatter(fig, process_interactions_df, process_boxes, circle_details):
    """
    Draw elbow jointed lines for artifacts from source process boxes and add hover labels using Scatter traces.
    """
    for index, row in process_interactions_df.iterrows():
        source_id = row['source_process_id']
        if source_id in process_boxes:
            source_box = process_boxes[source_id]
            num_lines = len(process_interactions_df[process_interactions_df['source_process_id'] == source_id])
            line_index = list(process_interactions_df[process_interactions_df['source_process_id'] == source_id].index).index(index)

            horizontal_offset = line_index * 0.8 - (num_lines - 1) * 0.8 / 2
            line_start_x = source_box['x'] + source_box['width'] / 2 + horizontal_offset
            line_start_y = source_box['y']
            elbow_point_x = line_start_x
            elbow_point_y = circle_details['y'] + circle_details['radius'] + 1
            line_end_x = circle_details['x']
            line_end_y = circle_details['y'] + circle_details['radius']

            # Use a Scatter trace to draw the line and add hover text
            fig.add_trace(go.Scatter(
                x=[line_start_x, elbow_point_x, line_end_x],
                y=[line_start_y, elbow_point_y, line_end_y],
                mode='lines+markers',  # Add markers to the line
                line=dict(color=to_neon(source_box['color']), width=2),
                marker=dict(color=to_neon(source_box['color']), size=8),
                hoverinfo='text',
                text=row['artifact'],  # Set the hover text
                showlegend=False
            ))

    return fig

def add_artifact_lines_batch(fig, process_interactions_df, process_boxes, circle_details, line_offset=0.8):
    line_shapes = []
    line_traces = []

    annotations = []

    for index, row in process_interactions_df.iterrows():
        source_id = row['source_process_id']
        if source_id in process_boxes:
            source_box = process_boxes[source_id]

            # Calculate the number of lines originating from this source
            num_lines = len(process_interactions_df[process_interactions_df['source_process_id'] == source_id])
            line_index = list(process_interactions_df[process_interactions_df['source_process_id'] == source_id].index).index(index)

            # Calculate the horizontal offset for this line
            horizontal_offset = line_index * line_offset - (num_lines - 1) * line_offset / 2

            line_start_x = source_box['x'] + source_box['width'] / 2 + horizontal_offset
            line_start_y = source_box['y']
            elbow_point_x = line_start_x
            elbow_point_y = circle_details['y'] + circle_details['radius'] + 1  # Adjust the vertical position of the elbow point
            line_end_x = circle_details['x']
            line_end_y = circle_details['y'] + circle_details['radius']

            # Draw the first segment (vertical line)
            line_traces.append(go.Scatter(
                x=[line_start_x, elbow_point_x],
                y=[line_start_y, elbow_point_y],
                mode='lines',
                line=dict(color=to_neon(source_box['color']), width=2),
                hoverinfo='text',
                text=row['artifact'],  # This will display the artifact name on hover
                showlegend=False
            ))

            # Draw the second segment (horizontal line)
            line_traces.append(go.Scatter(
                x=[elbow_point_x, line_end_x],
                y=[elbow_point_y, line_end_y],
                mode='lines',
                line=dict(color=to_neon(source_box['color']), width=1),
                hoverinfo='text',
                text=row['artifact'],  # This will display the artifact name on hover
                showlegend=False
            ))


    # Add all lines to the figure
    fig.add_traces(line_traces)


# Adding Bezier Curves
def add_bezier_curves(fig, processes, practice_boxes):
    for process in processes:
        practice_id = process['practice_id']
        if practice_id in practice_boxes:
            practice = practice_boxes[practice_id]
            practice_center = (practice['x'] + practice['width'] / 2, practice['y'] + practice['height'] / 2)
            process_center = (process['x'] + process['width'] / 2, process['y'] + process['height'] / 2)
            verts = [practice_center, ((practice_center[0] + process_center[0]) / 2, practice_center[1] - 2), process_center]
            fig.add_shape(
                type='path',
                path=f'M {verts[0][0]},{verts[0][1]} Q {verts[1][0]},{verts[1][1]} {verts[2][0]},{verts[2][1]}',
                line=dict(color=to_neon(practice['color']), width=3),
                layer='below'
            )

# Adding Black Circle
def add_circle(fig, circle_details):
    fig.add_shape(
        type="circle",
        xref="x",
        yref="y",
        x0=circle_details['x'] - circle_details['radius'],
        y0=circle_details['y'] - circle_details['radius'],
        x1=circle_details['x'] + circle_details['radius'],
        y1=circle_details['y'] + circle_details['radius'],
        line_color="lime",
        fillcolor="lime"
    )

# Creating the Interactive Plot
def create_interactive_plot(box_details, process_interactions_df, total_width, total_height):
    fig = go.Figure()

    practice_boxes = {practice['id']: practice for practice in box_details['Practices']}
    process_boxes = {process['id']: process for process in box_details['Processes']}

    add_bezier_curves(fig, box_details['Processes'], practice_boxes)
    #add_artifact_lines_with_scatter(fig, process_interactions_df, process_boxes)
    #add_artifact_lines_batch(fig, process_interactions_df, process_boxes, circle_details)
    add_practice_shapes(fig, box_details['Practices'],total_height,total_width)
    add_process_shapes(fig, box_details['Processes'],total_height,total_width)

    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            range=[0, total_width]
        ),
        yaxis=dict(
            fixedrange=True
        ),
        paper_bgcolor='black',
        plot_bgcolor='black',
    )

    fig.update_shapes(dict(opacity=0.3))
    fig.update_layout(
        hovermode='closest',
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        font=dict(color='lime')
    )

    return fig



