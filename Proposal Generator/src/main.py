# Importing necessary modules and functions for data extraction, verification, and document generation
from extract_data import extract_project_info, extract_materials
from verify_data import verify_costs
from generate_doc import generate_proposal_doc
import json
import warnings
import os

# Suppress specific warnings from the openpyxl library
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Define file paths for input and output
excel_path = "../uploads/input.xlsx"
output_json_path = "../output/output.json"
output_doc_path = "../output/proposal.docx"
template_path = "../template.docx"

# Extract project information from the Excel file
project_info = extract_project_info(excel_path)

# Round numeric values in the extracted project information
for key, value in project_info.items():
    if isinstance(value, float):
        project_info[key] = round(value, 2)

# Extract materials data from the Excel file
materials = extract_materials(excel_path)

# Combine project information and materials into a single dictionary
output = {
    "project_info": project_info,
    "materials": materials
}

# Ensure the output directory exists
os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

# Write the combined data to a JSON file
with open(output_json_path, "w") as f:
    json.dump(output, f, indent=2, default=str)

print("Data saved to output.json in the output folder.")

# Verify the costs in the extracted data
verification = verify_costs(excel_path)
print("\nCost Verification Result:")
for key, value in verification.items():
    print(f"{key}: {value}")

# Generate a proposal document using the extracted data and template
generate_proposal_doc(output, template_path=template_path, output_path=output_doc_path)