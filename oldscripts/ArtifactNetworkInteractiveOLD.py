import colorsys

import plotly.graph_objects as go
from matplotlib import pyplot as plt


def to_rgb(color):
    """Convert a matplotlib color to an rgb string."""
    return 'rgb({}, {}, {})'.format(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))

def to_neon(color):
    """Convert a pastel color to a neon color."""
    r, g, b = color

    # Amplify the RGB values to create a neon effect
    neon_r = min(1, r * 1.5)
    neon_g = min(1, g * 1.5)
    neon_b = min(1, b * 1.5)

    return 'rgb({}, {}, {})'.format(int(neon_r * 255), int(neon_g * 255), int(neon_b * 255))


def add_practice_shapes(fig, practices, practice_shape_indices, practice_buttons):
    """Add practice shapes and text to the figure."""
    for practice_index, practice in enumerate(practices):
        practice_id = practice['id']
        practice_name = practice['name']
        practice_color = to_neon(practice['color'])

        visibility = [True for _ in practices]
        process_visibility = [True for _ in practices]

        button = {
            'label': practice_name,
            'method': 'update',
            'args': [{'visible': visibility + process_visibility}]
        }

        practice_buttons.append(button)

        fig.add_trace(go.Scatter(
            x=[practice['x'] + practice['width'] / 2],
            y=[practice['y'] + practice['height'] / 2],
            text=[practice['name']],
            mode='text',
            textposition='middle center',
            visible=True,  # Initially visible
            hoverinfo='none',
            showlegend=False,
            marker=dict(size=0),
            textfont=dict(size=12)
        ))

        fig.add_shape(
            type='rect',
            x0=practice['x'],
            y0=practice['y'],
            x1=practice['x'] + practice['width'],
            y1=practice['y'] + practice['height'],
            line=dict(color='black'),
            fillcolor=practice_color,  # Use the converted color
            visible=True,  # Initially visible
            layer='above'
        )
        practice_shape_indices.append(len(fig['data']) - 1)

def add_process_shapes(fig, processes, process_shape_indices):
    """Add process shapes and text to the figure."""
    for process_index, process in enumerate(processes):
        process_color = to_neon(process['color'])

        fig.add_trace(go.Scatter(
            x=[process['x'] + process['width'] / 2],
            y=[process['y'] + process['height'] / 2],
            text=[process['name']],
            mode='text',
            textposition='middle center',
            visible=True,  # Initially visible
            hoverinfo='none',
            showlegend=False,
            marker=dict(size=0),
            textfont=dict(size=12)
        ))

        fig.add_shape(
            type='rect',
            x0=process['x'],
            y0=process['y'],
            x1=process['x'] + process['width'],
            y1=process['y'] + process['height'],
            line=dict(color='black'),
            fillcolor=process_color,  # Use the converted color
            visible=True,  # Initially visible
            layer='above'
        )
        process_shape_indices.append(len(fig['data']) - 1)

def add_artifact_lines(fig, process_interactions_df, process_boxes, circle_details, line_offset=0.8, line_length=10):
    """Draw elbow jointed lines for artifacts from source process boxes and add labels."""
    for index, row in process_interactions_df.iterrows():
        source_id = row['source_process_id']
        if source_id in process_boxes:
            source_box = process_boxes[source_id]
            num_lines = len(process_interactions_df[process_interactions_df['source_process_id'] == source_id])
            line_index = list(process_interactions_df[process_interactions_df['source_process_id'] == source_id].index).index(index)

            horizontal_offset = line_index * line_offset - (num_lines - 1) * line_offset / 2
            line_start_x = source_box['x'] + source_box['width'] / 2 + horizontal_offset
            line_start_y = source_box['y']
            elbow_point_x = line_start_x
            elbow_point_y = circle_details['y'] + circle_details['radius'] + 1  # Add some margin above the circle
            line_end_x = circle_details['x']
            line_end_y = circle_details['y'] + circle_details['radius']

            # Draw the first segment (vertical line)
            fig.add_shape(
                type='line',
                x0=line_start_x,
                y0=line_start_y,
                x1=elbow_point_x,
                y1=elbow_point_y,
                line=dict(color=to_neon(source_box['color']), width=1),
                layer='below'  # Ensure lines are below the boxes
            )

            # Draw the second segment (horizontal line)
            fig.add_shape(
                type='line',
                x0=elbow_point_x,
                y0=elbow_point_y,
                x1=line_end_x,
                y1=line_end_y,
                line=dict(color=to_neon(source_box['color']), width=4),
                layer='below'  # Ensure lines are below the boxes
            )

            # Create a temporary figure to measure text length
            temp_fig, temp_ax = plt.subplots()
            text_artist = temp_ax.text(0, 0, row['artifact'], fontsize=8)
            temp_fig.canvas.draw()
            text_length = text_artist.get_window_extent(renderer=temp_fig.canvas.get_renderer()).width / temp_fig.dpi  # Convert pixels to inches
            plt.close(temp_fig)  # Close the temporary figure

            # Adjust the text position
            text_x = elbow_point_x + 0.2 # - text_length
            text_y = elbow_point_y+ text_length * 2.5 #- 0.5  # Adjust to position the text below the elbow point


            fig.add_annotation(
                x=text_x,
                y=text_y,
                text=row['artifact'],
                showarrow=False,
                font=dict(color=to_neon(source_box['color']), size=10),
                yshift=0,  # Adjust this to move the text closer to the end of the line
                textangle=90,
                visible=True  # Initially visible
            )


def add_bezier_curves(fig, processes, practice_boxes):
    """Draw Bezier curves from Practice boxes to Process boxes."""
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
                line=dict(color=to_rgb(practice['color']), width=3),
                layer='below'
            )

def add_circle(fig, circle_details):
    """Add a black circle at the specified location in the interactive plot."""
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


def add_practice_buttons(fig, practices, processes, process_interactions_df):
    """Add buttons to select practices and filter the view."""
    buttons = []
    visibility = [True] * (len(practices) + len(processes) + len(process_interactions_df))

    # Prepare visibility masks for each practice and its sub-processes and arrows
    visibility_masks = []
    for practice in practices:
        practice_id = practice['id']
        practice_name = practice['name']

        # Determine which processes belong to this practice
        practice_process_indices = [i + len(practices) for i, p in enumerate(processes) if p['practice_id'] == practice_id]

        # Determine which arrows originate from this practice's processes
        practice_arrow_indices = [i + len(practices) + len(processes) for i, p in enumerate(process_interactions_df['source_process_id']) if p in [pr['id'] for pr in processes if pr['practice_id'] == practice_id]]

        # Create a visibility mask for this practice, its processes, and its arrows
        mask = [i < len(practices) and i == practices.index(practice) for i in range(len(visibility))]
        mask += [i in practice_process_indices for i in range(len(practices), len(practices) + len(processes))]
        mask += [i in practice_arrow_indices for i in range(len(practices) + len(processes), len(visibility))]
        visibility_masks.append(mask)

        # Create button for this practice
        button = {
            'label': practice_name,
            'method': 'update',
            'args': [{'visible': mask}]
        }
        buttons.append(button)

    # Add button to show all practices and processes
    all_visible = [True] * len(visibility)
    buttons.append({
        'label': 'All',
        'method': 'update',
        'args': [{'visible': all_visible}]
    })

    # Update layout with buttons
    fig.update_layout(
        updatemenus=[{
            'type': 'buttons',
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.17,
            'xanchor': 'left',
            'y': 1.15,
            'yanchor': 'top'
        }]
    )

def create_interactive_plot(box_details, process_interactions_df, total_width, circle_details):
    """Create an interactive plot using Plotly."""
    fig = go.Figure()

    practice_buttons = []
    practice_shape_indices = []
    process_shape_indices = []

    practice_boxes = {practice['id']: practice for practice in box_details['Practices']}
    process_boxes = {process['id']: process for process in box_details['Processes']}

    print("Adding Connections to interactive Visualisation")
    add_bezier_curves(fig, box_details['Processes'], practice_boxes)

    print("Adding Arrows to interactive Visualisation")
    add_artifact_lines(fig, process_interactions_df, process_boxes, circle_details)

    print("Adding Practices to interactive Visualisation")
    add_practice_shapes(fig, box_details['Practices'], practice_shape_indices, practice_buttons)

    print("Adding Processes to interactive Visualisation")
    add_process_shapes(fig, box_details['Processes'], process_shape_indices)

    print("Adding Black Whole Circle")
    add_circle(fig,circle_details)
    #print("Adding Practice Selection Buttons")
    #add_practice_buttons(fig, box_details['Practices'], box_details['Processes'], process_interactions_df)

    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),
            range=[0, total_width]  # Ensure the full width is shown initially
        ),
        yaxis=dict(
            fixedrange=True  # Disable vertical scrolling
        ),
        paper_bgcolor='black',  # Change the background color to black
        plot_bgcolor='black',   # Change the plot area background to black
    )

    fig.update_shapes(dict(opacity=0.3))
    fig.update_layout(
        hovermode=False,
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        font=dict(color='lime')  # Change the font color to bright green
    )
    print("DRAWING Interactive Visual")
    fig.show()
