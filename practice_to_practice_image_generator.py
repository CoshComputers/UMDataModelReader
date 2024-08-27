import os
import textwrap
import tkinter as tk
from tkinter import filedialog
from typing import List, Dict, Tuple

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from data_processing import load_data, process_data, find_processes_with_no_destination, find_artifacts_with_no_source
from drawing_visuals import create_boxes, create_bezier_curve, create_text_element, wrap_text

BOX_HEIGHT = 100
PRACTICE_Y_TOP = 0.9
PROCESS_Y_TOP = 0.65
PROCESS_Y_BOTTOM = 0.2
PRACTICE_Y_BOTTOM = 0.05

'''********************************** Filter Functions ******************************************'''
def filter_bottom_practices(selected_practices: List[str]) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    # Filter destination practices
    filtered_practices_bottom = {pid: pdata for pid, pdata in graphics_data['practice_bottom'].items() if pid in selected_practices}

    # Analyze relationships to find corresponding Top Practices
    filtered_practices_top = analyze_reverse_practice_relationships(filtered_practices_bottom)

    return filtered_practices_top, filtered_practices_bottom

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

'''**** Reverse (Dest to source) analysis logic *****'''
def analyze_reverse_practice_relationships(filtered_practices_bottom: Dict[str, Dict]) -> Dict[str, Dict]:
    process_to_artifacts = graphics_data.get('process_to_artifacts', {})
    filtered_practices_top = {}

    for (source_pid, dest_pid), artifacts in process_to_artifacts.items():
        dest_practice_id = graphics_data['process_bottom'][dest_pid]['practice_id']
        if dest_practice_id in filtered_practices_bottom:
            source_practice_id = graphics_data['process_top'][source_pid]['practice_id']
            filtered_practices_top[source_practice_id] = graphics_data['practice_top'][source_practice_id]

    return filtered_practices_top

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

'''************************************************************************************************
   * MAIN DRAWING FUNCTION                                                                        *
   ************************************************************************************************'''
def create_practice_only_figure(selected_practices: List[str], filter_destination: bool = False, save_dir: str = ".") -> go.Figure:
    fig = go.Figure()

    # Filter practices only and identify relationships
    if filter_destination:
        # New logic: Filtering based on destination practices
        filtered_practices_top, filtered_practices_bottom = filter_bottom_practices(selected_practices)
    else:
        # Original logic: Filtering based on source practices
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

    '''print("*** Practice TOP ***")
    print(centered_practice_top)
    print("*** Practice Bottom ***")
    print(centered_practice_bottom)

    print("*** Process Top ***")
    print(filtered_processes_top)
    print("*** Process Bottom ***")
    print(filtered_processes_bottom)'''

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

    # Add boxes for practices
    shapes.extend(create_boxes(centered_practice_top + centered_practice_bottom, x_spacing))

    # Add text labels for practices
    for data in centered_practice_top:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))
    for data in centered_practice_bottom:
        traces.append(create_text_element(data['x'], data['y'], data['draw_height'], data['name']))

    fig.update_layout(shapes=shapes)
    fig.add_traces(traces)

    # Determine whether this is for source or destination
    role = "dest" if filter_destination else "src"
    role_str = "Destination" if role == "dest" else "Source"
    # Set the title dynamically based on practice name and role
    practice_name = filtered_practices_top[selected_practices[0]]['name'] if not filter_destination else filtered_practices_bottom[selected_practices[0]]['name']
    title_text = f"{practice_name} - AS - {role_str}"

    # Final layout update
    fig.update_layout(
        title=title_text,
        plot_bgcolor='black',
        paper_bgcolor='black',
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
        height=800,  # Adjust this as needed for your layout
        width=1200,  # Adjust this as needed for your layout
        showlegend=False,
        dragmode='zoom',
        font=dict(color='#00FF00')
    )


    # Save the figure as a PNG file in the selected directory
    save_path = os.path.join(save_dir, f"{selected_practices[0]}_{role}.png")
    fig.write_image(save_path, scale=2)
   #fig.show()
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

    # Ask the user to select a directory for saving the PNG files
    save_dir = filedialog.askdirectory(
        title="Select Directory to Save PNG Files"
    )

    if not save_dir:
        print("No directory selected. Exiting.")
        return


    # Open a text file to write the output
    output_file = open("process_and_artifact_analysis.txt", "w")

    # Load and process the data
    print("1 - Loading Data")
    practices_df, processes_df, artifacts_df, artifact_interactions_df = load_data(file_name)

    # Find and print processes with no destination
    print("2 - Identifying Processes with No Destination")
    output_file.write("Processes with No Destination:\n")
    processes_no_destination = find_processes_with_no_destination(processes_df, artifact_interactions_df)
    for process in processes_no_destination:
        print(process)
        output_file.write(process + "\n")

    # Find and print artifacts with no source
    print("3 - Identifying Artifacts with No Source")
    output_file.write("\nArtifacts with No Source:\n")
    artifacts_no_source = find_artifacts_with_no_source(artifact_interactions_df, artifacts_df)
    for artifact in artifacts_no_source:
        print(artifact)
        output_file.write(artifact + "\n")

    # Close the file after writing
    output_file.close()

    print("4 - Processing Data")
    graphics_data = process_data(practices_df, processes_df, artifact_interactions_df, artifacts_df)

    print("5 - Drawing Practice to Practice Images")
    # Loop through each practice
    # Modify the loop to only process the first practice
    '''first_practice_id = next(iter(graphics_data['practice_top']))  # Get the first practice ID
    print(f"Processing practice ID: {first_practice_id}")
    create_practice_only_figure([first_practice_id], filter_destination=False, save_dir=save_dir)
    print("\n")  # Add some spacing between outputs for readability
    create_practice_only_figure([first_practice_id], filter_destination=True, save_dir=save_dir)'''

    for practice_id in graphics_data['practice_top']:
        print(f"***Processing practice ID: {practice_id}")
        create_practice_only_figure([practice_id], filter_destination=False, save_dir=save_dir)
        print("\n")  # Add some spacing between outputs for readability
        create_practice_only_figure([practice_id], filter_destination=True, save_dir=save_dir)
        print("\n")  # Add some spacing between outputs for readability



if __name__ == "__main__":
    main()
