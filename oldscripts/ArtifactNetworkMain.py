import pandas as pd
from ArtifactNetworkStatic import plot_static
from ArtifactNetworkInteractive import create_interactive_dashboard
from ArtifactNetworkVisualisation import calculate_box_details

def load_data_model(file_path):
    """Load the data model tables from the Excel file into individual DataFrames."""
    xls = pd.ExcelFile(file_path)

    practices_df = pd.read_excel(xls, sheet_name='Practices')
    processes_df = pd.read_excel(xls, sheet_name='Processes')
    artifacts_df = pd.read_excel(xls, sheet_name='Artifacts')
    process_interactions_df = pd.read_excel(xls, sheet_name='Process Interactions')

    return practices_df, processes_df, artifacts_df, process_interactions_df



def main():
    file_path = '../UnifiedModel.xlsx'
    print("Loading Data")
    practices_df, processes_df, artifacts_df, process_interactions_df = load_data_model(file_path)

    # Print column names for debugging
    print("Practices DF Columns:", practices_df.columns)
    print("Processes DF Columns:", processes_df.columns)
    print("Artifacts DF Columns:", artifacts_df.columns)
    print("Process Interactions DF Columns:", process_interactions_df.columns)

    print("Calculating Box Details")
    box_details, total_width, total_height_required = calculate_box_details(practices_df, processes_df)

    print("Creating Static Image")
    plot_static(box_details, total_width, process_interactions_df, artifacts_df, total_height_required)

    #print("Creating Interactive Dashboard")
    #create_interactive_dashboard(practices_df, processes_df, artifacts_df, process_interactions_df, box_details, total_width, circle_details)

if __name__ == "__main__":
    main()
