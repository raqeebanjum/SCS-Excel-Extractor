# Importing the pandas library for data manipulation and analysis
import pandas as pd

# Function to extract project information from the 'Project Details' sheet of an Excel file
def extract_project_info(file_path):
    # Load the 'Project Details' sheet from the Excel file
    df = pd.read_excel(file_path, sheet_name="Project Details", header=1)

    # Extract the first row of data (after skipping the header)
    row = df.iloc[0]

    # Return a dictionary containing key project details
    return {
        "Project": row["Project"],
        "SCS Quote": row["SCS Quote"],
        "Proposal Price": row["Proposal Price"],
        "Mat'l Cost": row["Mat'l Cost"],
        "Handoff Date": row["Handoff Date"],
        "P&ID Due": row["P&ID Due"],
        "GA Due": row["GA Due"],
        "Electrical Due": row["Electrical Due"],
        "Detailed Drawing Due": row["Detailed Drawing Due"],
        "Electrical IFC": row["Electrical IFC"],
    }

# Function to extract materials data from the 'LACT' sheet of an Excel file
def extract_materials(file_path):
    # Define the expected columns to be extracted from the sheet
    expected_columns = [
        "BoM Item", "Section", "Item", "Qty", "Part Number", "Description",
        "Vendor", "Unit Cost", "Total Cost", "Last PO Date", "Last PO Qty",
        "Lead Time", "Comments"
    ]

    # Load the 'LACT' sheet and filter columns based on the expected columns
    df = pd.read_excel(file_path, sheet_name="LACT", usecols=lambda x: x in expected_columns)

    # Stop processing at the row where 'BoM Item' column contains 'Total'
    if "BoM Item" in df.columns:
        stop_index = df[df["BoM Item"] == "Total"].index
        if not stop_index.empty:
            df = df.loc[:stop_index[0] - 1]

    # Drop rows where all elements are NaN
    df = df.dropna(how="all")

    # Replace NaN/NaT values with empty strings
    df = df.fillna("N/A")

    # Convert the DataFrame to a list of dictionaries and return
    return df.to_dict(orient="records")