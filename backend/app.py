from flask import (
    Flask, request, jsonify, send_file, 
    send_from_directory, Response
)
import os
import json
import pandas as pd
import logging
import time
from pathlib import Path
from src.excel_parser.excel_parser import ExcelParser
from src.ai.ollama_handler import parse_description_with_ollama, create_empty_fields 
import uuid
from flask_cors import CORS
from threading import Event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)
app.secret_key = os.urandom(24)

# Global variables
stop_processing = Event()
current_output_file = None
progress_data = {"current": 0, "total": 0}

app.config.update({
    'UPLOAD_FOLDER': 'temp/',
    'MAX_CONTENT_LENGTH': 50 * 1024 * 1024,
    'OLLAMA_MODEL': 'mistral'
})
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Serve React App
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/stop', methods=['POST'])
def stop_processing_route():
    global stop_processing, current_output_file, progress_data
    try:
        logger.info("Stop request received")
        stop_processing.set()
        
        # Get current progress for the response
        current_progress = progress_data.copy()
        
        # Wait for the file to be ready
        wait_time = 0
        max_wait = 10  # Maximum 10 seconds wait
        while wait_time < max_wait:
            if current_output_file and current_output_file.exists():
                logger.info(f"File ready at: {current_output_file}")
                return jsonify({
                    'message': 'Processing stopped',
                    'success': True,
                    'filePath': str(current_output_file),
                    'progress': current_progress
                })
            time.sleep(1)
            wait_time += 1
            logger.info(f"Waiting for file... ({wait_time}s)")
        
        # If we get here, the file wasn't ready
        logger.error("Timeout waiting for file")
        return jsonify({
            'message': 'Processing stopped but file not ready',
            'success': True,  # Still return success as processing was stopped
            'progress': current_progress
        })
            
    except Exception as e:
        logger.error(f"Stop processing error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/download', methods=['POST'])
def download():
    global current_output_file
    try:
        if not current_output_file:
            logger.error("No output file path set")
            return jsonify({'error': 'No file path available'}), 404
            
        if not current_output_file.exists():
            logger.error(f"File not found at: {current_output_file}")
            return jsonify({'error': 'File not found'}), 404
            
        logger.info(f"Sending file: {current_output_file}")
        return send_file(
            current_output_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='processed_results.xlsx'
        )
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/progress')
def progress():
    def generate():
        while True:
            yield f"data: {json.dumps(progress_data)}\n\n"
            time.sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
            
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.xlsx'):
        # Generate unique ID for this upload
        upload_id = str(uuid.uuid4())
        temp_path = Path(app.config['UPLOAD_FOLDER']) / f"{upload_id}.xlsx"
        file.save(temp_path)
        
        # Get sheet names
        sheet_names = ExcelParser.get_sheet_names(str(temp_path))
        
        return jsonify({
            'upload_id': upload_id,
            'sheet_names': sheet_names
        })

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/process', methods=['POST'])
def process():
    global progress_data, stop_processing, current_output_file
    temp_excel = None
    output_excel = None
    try:
        logger.info("Starting process")
        logger.info(f"Form data: {request.form}")
        
        # Reset stop signal and progress
        stop_processing.clear()
        progress_data = {"current": 0, "total": 0}
        
        upload_id = request.form['upload_id']
        logger.info(f"Upload ID: {upload_id}")
        
        temp_excel = Path(app.config['UPLOAD_FOLDER']) / f"{upload_id}.xlsx"
        logger.info(f"Temp Excel path: {temp_excel}")
        
        if not temp_excel.exists():
            logger.error(f"Excel file not found at {temp_excel}")
            return jsonify({'error': 'Invalid file session'}), 400

        # Create file paths
        output_excel = temp_excel.with_name(f"{upload_id}_processed.xlsx")
        current_output_file = output_excel
        logger.info(f"Output Excel path: {output_excel}")

        logger.info("Starting Excel to JSON conversion...")
        # Excel to JSON conversion
        parser = ExcelParser(str(temp_excel))
        
        sheet_name = request.form['sheet_name']
        logger.info(f"Loading sheet: {sheet_name}")
        
        if not parser.load_file(sheet_name=sheet_name):
            logger.error(f"Invalid sheet name: {sheet_name}")
            return jsonify({'error': 'Invalid sheet name'}), 400
        
        # Get basic data
        part_cell = request.form['part_cell']
        desc_cell = request.form['desc_cell']
        logger.info(f"Extracting data from cells - Part: {part_cell}, Desc: {desc_cell}")
        
        extracted_data = parser.extract_data(part_cell, desc_cell)
        
        if not extracted_data:
            logger.error("No data extracted from Excel")
            return jsonify({'error': 'No data found in specified cells'}), 400
            
        total_rows = len(extracted_data)
        progress_data["total"] = total_rows
        logger.info(f"Processing {total_rows} rows")
        
        # Process data through AI with progress tracking
        processed_data = []
        # In your process route
        for idx, record in enumerate(extracted_data, 1):
            try:
                if stop_processing.is_set():
                    logger.info("Processing stopped by user")
                    break
                    
                progress_data["current"] = idx
                logger.info(f"Processing record {idx}/{total_rows} ({(idx/total_rows)*100:.1f}%)")
                
                # Get AI extraction for the description
                extracted = parse_description_with_ollama(
                    record.get('description', ''),
                    app.config.get('OLLAMA_MODEL', 'mistral')
                )
                
                # Create new record
                new_record = {
                    "part_number": record.get("part_number"),
                    "description": record.get("description", "")
                }
                new_record.update(extracted)
                processed_data.append(new_record)
                
            except Exception as e:
                logger.error(f"Error processing record {idx}: {str(e)}")
                # Continue with empty fields rather than failing
                new_record = {
                    "part_number": record.get("part_number"),
                    "description": record.get("description", "")
                }
                new_record.update(create_empty_fields())
                processed_data.append(new_record)
        
        logger.info("AI processing complete. Saving results...")
        
        # Convert processed data to Excel
        df = pd.DataFrame(processed_data)
        
        # Define columns order
        columns = [
            'part_number',
            'description',
            'Size',
            'Length',
            'Height',
            'Flange Class',
            'Pipe Class',
            'Manufacturer',
            'Connection Type 1',
            'Connection Type 2',
            'Product Type',
            'Body Material',
            'Trim Material',
            'Seat/Elastomer material',
            'NACE (Y/N)',
            'Fireproof (Y/N)',
            'API (Y/N)',
            'ASME (Y/N)',
            'Operation',
            'Mfr Model Number',
            'Vendor Material Number',
            'Meter Type',
            'Perforation Size',
            'Orifice Diameter',
            'Pump Type',
            'Horsepower',
            'RPM',
            'Phase',
            'Voltage',
            'Hertz',
            'Class 1 Division',
            'NEMA',
            'Specific Gravity',
            'Pressure',
            'Flow Rate',
            'Temperature',
            'Other'
        ]
        
        # Reorder columns and fill missing columns with empty strings
        for col in columns:
            if col not in df.columns:
                df[col] = ''
                
        # Select only the columns we want in the order we want
        df = df[columns]
        
        logger.info("Generating Excel file...")
        
        try:
            df.to_excel(
                output_excel,
                index=False,
                engine='openpyxl',
                sheet_name='Processed Data'
            )
            logger.info(f"Generated Excel file at {output_excel}")
        except Exception as excel_error:
            logger.error(f"Excel creation error: {str(excel_error)}")
            raise

        # Check if processing was stopped early
        was_stopped = stop_processing.is_set()
        if was_stopped:
            logger.info("Processing was stopped by user. Sending partial results.")

        # Verify file exists and is not empty
        if not output_excel.exists():
            raise Exception("Output file was not created")
        
        if output_excel.stat().st_size == 0:
            raise Exception("Output file is empty")

        # Send the Excel file
        return send_file(
            output_excel,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='processed_results.xlsx'
        )

    except Exception as e:
        logger.exception("Detailed process error:") 
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Reset progress and stop signal
        progress_data = {"current": 0, "total": 0}
        stop_processing.clear()
        
        # Clean up temporary files
        for file in [temp_excel, output_excel]:
            if file and file.exists():
                try:
                    file.unlink()
                    logger.info(f"Cleaned up {file.name}")
                except Exception as e:
                    logger.error(f"Error cleaning up {file.name}: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)