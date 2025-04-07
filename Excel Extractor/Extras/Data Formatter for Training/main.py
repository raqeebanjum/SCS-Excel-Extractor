import csv
import json
import re

input_file = 'input.csv'
output_file = 'output.jsonl'

target_columns = [
    "Size", "Length", "Height", "Flange Class", "Pipe Class", "Manufacturer", "Connection Type 1", 
    "Connection Type 2", "Product Type", "Body Material", "Trim Material", "Seat/Elastomer material", 
    "NACE (Y/N)", "Fireproof (Y/N)", "API (Y/N)", "ASME (Y/N)", "Operation", "Mfr Model Number", 
    "Vendor Material Number", "Perforation Size", "Orifice Diameter", "Horsepower", "RPM", "Phase", "Voltage", 
    "Hertz", "Class 1 Division", "NEMA", "Specific Gravity", "Pressure", "Flow Rate", "Temperature", "Other"
]

def clean_text(text):
    # Replace problematic unicode characters
    text = text.replace('\u0094', '"').replace('\u0093', '"').replace('\u0092', "'")
    # Remove other unwanted non-printable characters
    text = re.sub(r'[^\x20-\x7E]', '', text)
    return text.strip()

with open(input_file, mode='r', encoding='latin1') as csvfile, open(output_file, mode='w', encoding='utf-8') as jsonlfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        input_text = clean_text(row.get("Description", ""))
        output_data = {col: clean_text(row.get(col, "")) for col in target_columns}

        json_entry = {
            "input": input_text,
            "output": output_data
        }

        jsonlfile.write(json.dumps(json_entry) + '\n')

print(f"Conversion complete! Cleaned data saved to '{output_file}'")