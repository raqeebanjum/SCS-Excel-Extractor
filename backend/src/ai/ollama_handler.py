import os
import json
import logging
import time
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



def parse_description_with_ollama(description: str, model_name: str) -> Dict[str, Any]:
    if not description or description.strip() in ("???", ""):
        return create_empty_fields()
    
    try:
        # Get base URL and log connection attempt
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
        logger.info(f"Processing description: {description[:100]}...")  # Log first 100 chars

        # Create Ollama client with custom host
        client = ollama.Client(host=base_url)
        
        # Add explicit formatting instructions to the prompt
        prompt = f"""
As an industrial equipment expert, extract the following fields from this description.
Return them as strings exactly. Use empty string if not present.
IMPORTANT: Return ONLY valid JSON with these exact fields, nothing else.
Ensure all property names are in double quotes and all values are strings.

Description:
{description}

Required JSON structure:
{json.dumps(create_empty_fields(), indent=2)}

Remember: Return ONLY the JSON object, no additional text.
"""

        # Make the API call with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat(
                    model=model_name,
                    messages=[{
                        "role": "user", 
                        "content": prompt
                    }],
                    options={'temperature': 0.1}  # Lower temperature for more consistent output
                )
                
                response_text = response["message"]["content"].strip()
                
                # Clean the response text
                response_text = response_text.replace('\n', ' ').replace('\r', '')
                response_text = ' '.join(response_text.split())  # Normalize whitespace
                
                # Extract JSON from response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                
                if 0 <= start < end:
                    json_text = response_text[start:end]
                    
                    # Validate JSON structure before parsing
                    try:
                        extracted_fields = json.loads(json_text)
                        
                        # Ensure all values are strings
                        extracted_fields = {k: str(v) if v is not None else "" for k, v in extracted_fields.items()}
                        
                        # Ensure all required fields exist
                        fields = create_empty_fields()
                        fields.update(extracted_fields)
                        
                        logger.info("Successfully extracted fields")
                        return fields
                        
                    except json.JSONDecodeError as json_error:
                        logger.error(f"JSON parsing error on attempt {attempt + 1}: {str(json_error)}")
                        if attempt == max_retries - 1:
                            raise
                        continue
                
                logger.warning(f"No valid JSON found in response on attempt {attempt + 1}")
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)  # Wait before retrying
        
        return create_empty_fields()
        
    except Exception as e:
        logger.error(f"Error processing with Ollama: {str(e)}")
        logger.exception("Full error trace:")
        return create_empty_fields()

def process_data(data: List[Dict]) -> List[Dict]:
    """Process a list of records and return updated records with AI extraction"""
    try:
        total_records = len(data)
        updated_data = []
        
        for idx, record in enumerate(data, 1):
            # Log progress
            progress = {
                'current': idx,
                'total': total_records,
                'percentage': round((idx/total_records)*100, 1)
            }
            logger.info(f"Processing record {progress['current']}/{progress['total']} ({progress['percentage']}%)")
            
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