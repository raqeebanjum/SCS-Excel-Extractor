import pandas as pd
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from flask import current_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExcelParser:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.df = None
        
    @staticmethod
    def cell_to_indices(cell: str) -> Tuple[int, int]:
        col_str = ''.join(filter(str.isalpha, cell.upper()))
        row_str = ''.join(filter(str.isdigit, cell))
        
        if not col_str or not row_str:
            raise ValueError(f"Invalid cell format: {cell}")
        
        col_num = sum((ord(c) - 64) * (26 ** i) for i, c in enumerate(reversed(col_str))) - 1
        row_num = int(row_str) - 1
        return row_num, col_num
    
    def load_file(self, sheet_name: Optional[str] = None) -> bool:
        try:
            self.df = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name,
                engine='openpyxl'
            )
            return True
        except Exception as e:
            logger.error(f"Load Error: {str(e)}")
            return False
        
    
    @classmethod
    def get_sheet_names(cls, file_path: str) -> list:
        """Get list of sheet names from Excel file"""
        try:
            with pd.ExcelFile(file_path) as xls:
                return xls.sheet_names
        except Exception as e:
            logger.error(f"Error reading sheets: {str(e)}")
            return []

    @staticmethod
    def cell_to_indices(cell: str) -> Tuple[int, int]:
        col_str = ''.join(filter(str.isalpha, cell.upper()))
        row_str = ''.join(filter(str.isdigit, cell))
        
        if not col_str or not row_str:
            raise ValueError(f"Invalid cell format: {cell}")
        
        col_num = sum((ord(c) - 64) * (26 ** i) for i, c in enumerate(reversed(col_str))) - 1
        row_num = int(row_str) - 1
        return row_num, col_num

    def load_file(self, sheet_name: Optional[str] = None) -> bool:
        try:
            self.df = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name,
                engine='openpyxl'
            )
            return True
        except Exception as e:
            logger.error(f"Load Error: {str(e)}")
            return False

    def extract_data(self, part_cell: str, desc_cell: str) -> List[Dict]:
        try:
            pn_row, pn_col = self.cell_to_indices(part_cell)
            desc_row, desc_col = self.cell_to_indices(desc_cell)
            
            if pn_row != desc_row:
                raise ValueError("Start cells must be on same row")
            
            data = []
            for idx in range(pn_row, len(self.df)):
                part = self._clean_value(self.df.iloc[idx, pn_col])
                desc = self._clean_value(self.df.iloc[idx, desc_col])
                
                # Include excel_row, part_number and description
                if part or desc:  # Only add if either field has content
                    data.append({
                        "excel_row": idx + 1,
                        "part_number": part,
                        "description": desc
                    })
            
            return data
        except Exception as e:
            logger.error(f"Extraction Error: {str(e)}")
            return []

    def _clean_value(self, value) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip().replace('\\"', '"')

    def save_to_json(self, data: List[Dict], output_path: Path) -> bool:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Save Error: {str(e)}")
            return False

def get_sheet_selection(sheets: List[str]) -> str:
    return sheets[0]  # Simplified for web integration

