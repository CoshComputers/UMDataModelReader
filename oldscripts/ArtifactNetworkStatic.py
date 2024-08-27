import matplotlib.pyplot as plt
import matplotlib.patches as patches
import textwrap

def draw_center_circle(ax, total_width, total_height):
    """Draw a black circle at the center of the graphic."""
    center_x = total_width / 2
    center_y = total_height / 2
    circle_radius = 3  # Adjust the radius size as needed

    circle = patches.Circle((center_x, center_y), circle_radius, color='black')
    ax.add_patch(circle)

    return center_x, center_y



def plot_practice_boxes(ax, practices):
    """Plot practice boxes and return a dictionary of their details."""
    practice_boxes = {}
    for box in practices:
        prefix = "DEST_" if box['is_destination'] else "SRC_"
        rect = patches.Rectangle((box['x'], box['y']), box['width'], (box['height'] + 1), linewidth=1, edgecolor='black', facecolor=box['color'])
        ax.add_patch(rect)
        wrapped_text = textwrap.fill(box['name'], width=15)  # Adjust width for wrapping
        ax.text(box['x'] + box['width'] / 2, box['y'] + (box['height'] + 1) / 2, wrapped_text,
                ha='center', va='center', fontsize=10)
        practice_boxes[prefix + box['id']] = box
    return practice_boxes

def plot_process_boxes(ax, processes):
    """Plot process boxes and return a dictionary of their details."""
    process_boxes = {}
    for box in processes:
        prefix = "DEST_" if box['is_destination'] else "SRC_"
        rect = patches.Rectangle((box['x'], box['y']), box['width'], box['height'] + 1, linewidth=1, edgecolor='black', facecolor=box['color'])
        ax.add_patch(rect)
        wrapped_text = textwrap.fill(box['name'], width=15)  # Adjust width for wrapping
        ax.text(box['x'] + box['width'] / 2, box['y'] + (box['height'] + 1) / 2, wrapped_text,
                ha='center', va='center', fontsize=8)
        process_boxes[prefix + box['id']] = box
    return process_boxes

def draw_bezier_curves(ax, process_boxes, practice_boxes):
    """Draw Bezier curves connecting source and destination Practice boxes to Process boxes."""

    # First loop: Connect source process boxes to source practice boxes
    for process_id, process_box in process_boxes.items():
        # Determine if it's a source or destination process box by checking the prefix
        if process_id.startswith("SRC_"):
            practice_id = process_box.get('practice_id', None)
            if practice_id is None:
                print(f"Warning: 'practice_id' not found in process_box: {process_box}")
                continue  # Skip this process box if 'practice_id' is missing
            source_practice_box = practice_boxes.get(f"SRC_{practice_id}", None)
            if source_practice_box:
                practice_center = (source_practice_box['x'] + source_practice_box['width'] / 2, source_practice_box['y'] + source_practice_box['height'] / 2)
                process_center = (process_box['x'] + process_box['width'] / 2, process_box['y'] + process_box['height'] / 2)
                verts = [practice_center, ((practice_center[0] + process_center[0]) / 2, practice_center[1] - 2), process_center]
                codes = [1, 3, 3]
                path = patches.Path(verts, codes)
                patch = patches.PathPatch(path, edgecolor=process_box['color'], linestyle='solid', linewidth=1, facecolor='none', zorder=-1)
                ax.add_patch(patch)

    # Second loop: Connect destination process boxes to destination practice boxes
    for process_id, process_box in process_boxes.items():
        # Determine if it's a destination process box by checking the prefix
        if process_id.startswith("DEST_"):
            practice_id = process_box.get('practice_id', None)
            if practice_id is None:
                print(f"Warning: 'practice_id' not found in process_box: {process_box}")
                continue  # Skip this process box if 'practice_id' is missing
            dest_practice_box = practice_boxes.get(f"DEST_{practice_id}", None)
            if dest_practice_box:
                process_center = (process_box['x'] + process_box['width'] / 2, process_box['y'] + process_box['height'] / 2)
                practice_center = (dest_practice_box['x'] + dest_practice_box['width'] / 2, dest_practice_box['y'] + dest_practice_box['height'] / 2)
                verts = [process_center, ((process_center[0] + practice_center[0]) / 2, process_center[1] - 2), practice_center]
                codes = [1, 3, 3]
                path = patches.Path(verts, codes)
                patch = patches.PathPatch(path, edgecolor=process_box['color'], linestyle='solid', linewidth=1, facecolor='none', zorder=-1)
                ax.add_patch(patch)

def draw_artifact_relationships(ax, process_interactions_df, process_boxes, center_x, center_y):
    """Draw Bezier curves connecting source processes to destination processes based on artifact relationships."""
    for index, row in process_interactions_df.iterrows():
        source_id = f"SRC_{row['source_process_id']}"
        dest_id = f"DEST_{row['destination_process_id']}"

        if source_id in process_boxes:
            source_box = process_boxes[source_id]
            source_center = (source_box['x'] + source_box['width'] / 2, source_box['y'] + source_box['height'] / 2)

            if dest_id in process_boxes:
                # Draw a line to the destination process box
                dest_box = process_boxes[dest_id]
                dest_center = (dest_box['x'] + dest_box['width'] / 2, dest_box['y'] + dest_box['height'] / 2)
                verts = [source_center, ((source_center[0] + dest_center[0]) / 2, source_center[1] - 2), dest_center]
                codes = [1, 3, 3]
                path = patches.Path(verts, codes)
                patch = patches.PathPatch(path, edgecolor=dest_box['color'], linestyle='solid', linewidth=2, facecolor='none', zorder=-1)
                ax.add_patch(patch)
            else:
                # Draw a line to the center circle
                verts = [source_center, ((source_center[0] + center_x) / 2, source_center[1] - 2), (center_x, center_y)]
                codes = [1, 3, 3]
                path = patches.Path(verts, codes)
                patch = patches.PathPatch(path, edgecolor='gray', linestyle='dotted', linewidth=1, facecolor='none', zorder=-1)
                ax.add_patch(patch)


def plot_static(box_details, total_width, process_interactions_df, artifacts_df, total_height):
    """Plot the boxes for Practices and Processes."""
    fig, ax = plt.subplots(figsize=(total_width / 5, 15))  # Adjust figure size based on total width
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height)

    print("Drawing Practice Boxes")
    practice_boxes = plot_practice_boxes(ax, box_details['Practices'])
    print("Drawing Process Boxes")
    process_boxes = plot_process_boxes(ax, box_details['Processes'])
    print("Drawing Center Circle")
    center_x, center_y = draw_center_circle(ax, total_width, total_height)
    print("Drawing Practice to Process Connections")
    draw_bezier_curves(ax, process_boxes, practice_boxes)

    print("Drawing Artifact Connections")
    draw_artifact_relationships(ax, process_interactions_df, process_boxes, center_x, center_y)

    plt.axis('off')  # Turn off the axis

    plt.savefig('artifact_network.png')
    plt.show()
