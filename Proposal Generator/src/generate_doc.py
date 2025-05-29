# Importing necessary libraries for document generation and manipulation
import json
from docxtpl import DocxTemplate
import jinja2
import os

# Custom filter to convert integers to their word representation
def intword(value):
    number_words = {
        0: "Zero", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
        6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
        11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen",
        15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen",
        20: "Twenty"
    }
    try:
        num = int(value)
        return number_words.get(num, str(num))
    except:
        return str(value)

# Function to generate a proposal document using a template and context data
def generate_proposal_doc(context, template_path="template.docx", output_path="output/proposal.docx"):
    # Filter out materials with no description or 'N/A' description
    if "materials" in context:
        filtered_materials = []
        for material in context["materials"]:
            if material.get("Description") and material["Description"] != "N/A":
                filtered_materials.append(material)
        
        # Create a new context with filtered materials
        new_context = context.copy()
        new_context["materials"] = filtered_materials
    else:
        new_context = context

    # Set up a Jinja2 environment and add the custom filter
    env = jinja2.Environment()
    env.filters["intword"] = intword

    # Load the Word document template
    doc = DocxTemplate(template_path)

    # Render the template with the provided context
    doc.render(new_context, env)

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the generated document to the specified output path
    doc.save(output_path)
    print(f"Proposal generated at {output_path}")
