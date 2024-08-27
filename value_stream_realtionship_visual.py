import tkinter as tk
from tkinter import filedialog
from typing import List, Dict
import dash
from dash import dcc, html
import plotly.graph_objects as go
from data_processing import load_data, process_data

# Initialize Dash application
app = dash.Dash(__name__)

# Global variable to store the processed graphics data
graphics_data: Dict = None

def create_layout():
    # Directly generate the figure without using a callback
    fig = create_value_stream_figure(graphics_data)

    app.layout = html.Div([
        dcc.Graph(
            id='value-stream-graph',
            figure=fig,
            style={'height': '100%', 'width': '100%'},
            config={'responsive': True}
        )
    ], style={'backgroundColor': '#515151', 'height': '100vh', 'display': 'flex', 'flexDirection': 'column', 'overflowY': 'scroll'})

    return app.layout

def calculate_text_width(text: str, font_size: int, figure_width: int) -> float:
    """Estimate the normalized width of the text based on character count and font size."""
    # A rough estimate assuming each character is about 0.6 times the font size in width
    character_width = font_size * 0.6 / figure_width
    return len(text) * character_width

def create_value_stream_figure(graphics_data: dict):
    fig = go.Figure()

    # Get process positions and practice positions from graphics_data
    process_positions = graphics_data['process_positions']
    practice_positions = graphics_data['practice_top']

    value_stream_order = ['IT4ITVS01', 'IT4ITVS02', 'IT4ITVS03', 'IT4ITVS04', 'IT4ITVS05', 'IT4ITVS06', 'IT4ITVS07', 'MOZVS01']

    # Set the Y-axis to a fixed range to prevent auto-scaling
    fig.update_yaxes(range=[0, 1], fixedrange=True)
    fig.update_xaxes(range=[0,100], fixedrange=True)
    # Initialize positioning variables
    x_position = 1  # Starting X position
    y_position = 0.01  # Fixed Y position near the top
    x_spacing = 15  # Spacing between items
    max_x_position = 95  # Maximum X position before wrapping to the next line
    font_size = 14  # Size of the text font
    figure_width = 100.0  # The width of the figure in normalized coordinates
    text_width=0
    for practice_id, practice_data in practice_positions.items():
        practice_name = practice_data['name']
        practice_color = practice_data['color']


        # Check if the next item will overflow the figure width
        if x_position + text_width > max_x_position:
            x_position = 1  # Wrap to the next line
            y_position += 0.025  # Move down to the next row
            text_width = 0
        print(f"Text: {practice_name}, x={x_position}, y={y_position}")
        # Add the text element
        fig.add_trace(go.Scatter(
            x=[x_position + text_width],  # Center the text horizontally
            y=[y_position],  # Place text at the current Y position
            text=[practice_name],
            mode='text',
            textposition='top right',
            textfont=dict(color=practice_color, size=font_size),
            hoverinfo='skip',  # No need for hover info
            showlegend=False
        ))

        # Calculate the exact width of the text
        #text_width = 15 #calculate_text_width(practice_name, font_size, figure_width) + 2
        # Update X position for the next item
        x_position += x_spacing

    # Sort processes into their respective value streams
    value_stream_tables = {vs: [] for vs in value_stream_order}
    for pos in process_positions:
        # Append process name and its color
        value_stream_tables[pos['value_stream_id']].append((pos['name'], pos['color']))

    # Create tables for each value stream in the specified order
    for i, vs_id in enumerate(value_stream_order):
        processes = value_stream_tables.get(vs_id, [])

        if processes:
            # Extract process names and their corresponding text colors
            process_names = [p[0] for p in processes]
            text_colors = [p[1] for p in processes]  # Use the color from the process

            fig.add_trace(go.Table(
                header=dict(
                    values=[vs_id],
                    fill_color='black',
                    align='left',
                    font=dict(color='lime', size=12)
                ),
                cells=dict(
                    values=[process_names],
                    fill_color=[['darkslategray'] * len(process_names)],  # Consistent row background color
                    align='left',
                    font=dict(color=[text_colors], size=10),  # Set text color for each process
                ),
                domain=dict(x=[i / len(value_stream_order), (i + 1) / len(value_stream_order)], y=[0, 1])
            ))

    # Adjust the layout to display the tables horizontally
    fig.update_layout(
        title="Processes Grouped by Value Stream",
        plot_bgcolor='#515151',
        paper_bgcolor='#515151',
        height=700,  # Adjust height as necessary to accommodate the key
        margin=dict(l=20, r=20, t=120, b=40),  # Adjust top margin to fit the key
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig

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
