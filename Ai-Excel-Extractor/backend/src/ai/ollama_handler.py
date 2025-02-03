import os
import json
import logging
import ollama
import requests 
from flask import current_app
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TARGET_COLUMNS = [
    "Size", "Length", "Height", "Flange Class", "Pipe Class",
    "Manufacturer", "Connection Type 1", "Connection Type 2",
    "Product Type", "Body Material", "Trim Material",
    "Seat/Elastomer material", "NACE (Y/N)", "Fireproof (Y/N)",
    "API (Y/N)", "ASME (Y/N)", "Operation", "Mfr Model Number",
    "Vendor Material Number", "Meter Type", "Perforation Size",
    "Orifice Diameter", "Pump Type", "Horsepower", "RPM", "Phase",
    "Voltage", "Hertz", "Class 1 Division", "NEMA", "Specific Gravity",
    "Pressure", "Flow Rate", "Temperature", "Other"
]

def create_empty_fields() -> Dict[str, str]:
    return {field: "" for field in TARGET_COLUMNS}

def build_prompt(description: str) -> str:
    fields_json = create_empty_fields()
    json_structure = json.dumps(fields_json, indent=2)
    
    return f"""
As an industrial equipment expert, extract the following fields from this description.
Return them as strings exactly. Use empty string if not present. Keep part numbers identical.
Return only valid JSON with these exact fields:

Description:
{description}

Required JSON structure:
{json_structure}

Only include the JSON object with no extra text.
"""


def parse_description_with_ollama(description: str, model_name: str) -> Dict[str, Any]:
    if not description or description.strip() in ("???", ""):
        return create_empty_fields()
    
    try:
        # Get base URL and log connection attempt
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
        logger.info(f"Connecting to Ollama at: {base_url}")

        # Test connection to Ollama
        try:
            test_response = requests.get(f"{base_url}/api/tags")
            logger.info(f"Ollama connection test successful. Status: {test_response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise

        # Create Ollama client with custom host
        client = ollama.Client(host=base_url)
        
        # Make the API call
        response = client.chat(
            model=model_name,
            messages=[{
                "role": "user", 
                "content": build_prompt(description)
            }],
            options={'temperature': 0.1}
        )
        
        logger.info("Got response from Ollama")
        response_text = response["message"]["content"].strip()
        
        # Extract JSON from response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if 0 <= start < end:
            extracted_fields = json.loads(response_text[start:end])
            fields = create_empty_fields()
            fields.update(extracted_fields)
            logger.info("Successfully extracted fields from response")
            return fields
        
        logger.warning("No valid JSON found in response")
        return create_empty_fields()
    
    except Exception as e:
        logger.error(f"Error processing with Ollama: {str(e)}")
        logger.exception("Full error trace:")
        return create_empty_fields()
def process_data(data: List[Dict]) -> List[Dict]:
    """Process a list of records and return updated records with AI extraction"""
    try:
        updated_data = []
        for record in data:
            # Get AI extraction for the description
            extracted = parse_description_with_ollama(
                record.get('description', ''),
                current_app.config.get('OLLAMA_MODEL', 'mistral')
            )
            
            # Create new record with original fields plus AI extraction
            new_record = {
                "excel_row": record.get("excel_row"),
                "part_number": record.get("part_number"),
                "description": record.get("description", "")
            }
            new_record.update(extracted)
            updated_data.append(new_record)
        
        return updated_data
            
    except Exception as e:
        logger.error(f"Processing Failed: {str(e)}")
        raise