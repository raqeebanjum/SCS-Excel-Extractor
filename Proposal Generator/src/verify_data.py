# Importing functions to extract project information and materials data
from extract_data import extract_project_info, extract_materials

# Function to verify the costs in the project data
def verify_costs(file_path):
    # Extract project information and materials data from the Excel file
    project_info = extract_project_info(file_path)
    materials = extract_materials(file_path)

    # Extract the proposal price from the project information
    proposal_price = project_info.get("Proposal Price", 0)
    total_cost = 0

    # Calculate the total cost of materials
    for item in materials:
        cost = item.get("Total Cost", 0)
        try:
            total_cost += float(cost)
        except ValueError:
            continue  # Ignore non-numeric entries

    # Round the proposal price and total cost to two decimal places
    proposal_price = round(float(proposal_price), 2)
    total_cost = round(total_cost, 2)

    # Return a dictionary containing the verified costs
    return {
        "Proposal Price": proposal_price,
        "Total Material Cost": total_cost
    }