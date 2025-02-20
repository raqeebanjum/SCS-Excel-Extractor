import pandas as pd
import json
from pathlib import Path
import logging
import requests
from typing import List, Dict, Set
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.model = "mistral"
        self.api_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434') + '/api/generate'
        
    def _call_ollama(self, prompt: str) -> str:
        """Make a call to Ollama API"""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return ""
    
    def process_for_categories(self, descriptions: List[str], existing_categories: List[str]) -> List[str]:
        """Process descriptions to identify categories"""
        prompt = f"""Analyze these technical product descriptions and identify the main product categories.
        
        Existing categories: {', '.join(existing_categories)}
        Either match to existing categories or create new ones only if truly different.
        
        Descriptions:
        {' | '.join(descriptions)}
        
        Return ONLY a list of category names, one per line, nothing else.
        Be specific and consistent."""
        
        try:
            response = self._call_ollama(prompt)
            # Split response into lines and clean
            categories = [
                cat.strip() for cat in response.split('\n')
                if cat.strip() and not cat.startswith('-')
            ]
            return categories
        except Exception as e:
            logger.error(f"Error processing categories: {e}")
            return []
    
    def process_for_subcategories(self, category: str, descriptions: List[str], existing_subcategories: List[str]) -> List[str]:
        """Process descriptions to identify subcategories for a given category"""
        prompt = f"""For the product category '{category}', analyze these descriptions and identify specific subcategories.
        
        Existing subcategories: {', '.join(existing_subcategories)}
        Either match to existing subcategories or create new ones only if truly different.
        
        Descriptions:
        {' | '.join(descriptions)}
        
        Return ONLY a list of subcategory names for {category}, one per line, nothing else.
        Be specific and consistent."""
        
        try:
            response = self._call_ollama(prompt)
            # Split response into lines and clean
            subcategories = [
                subcat.strip() for subcat in response.split('\n')
                if subcat.strip() and not subcat.startswith('-')
            ]
            return subcategories
        except Exception as e:
            logger.error(f"Error processing subcategories: {e}")
            return []
        
class CategoryManager:
    def __init__(self):
        self.categories = {}
        
    def add_category(self, category: str) -> bool:
        category = category.strip().title()
        if category not in self.categories:
            self.categories[category] = {"subcategories": set()}
            return True
        return False
    
    def add_subcategory(self, category: str, subcategory: str) -> bool:
        category = category.strip().title()
        subcategory = subcategory.strip().title()
        
        if category in self.categories:
            self.categories[category]["subcategories"].add(subcategory)
            return True
        return False
    
    def get_existing_categories(self) -> List[str]:
        return list(self.categories.keys())
    
    def get_existing_subcategories(self, category: str) -> List[str]:
        category = category.strip().title()
        return list(self.categories.get(category, {}).get("subcategories", set()))
    
    def save_to_json(self, filename: str = "categories.json"):
        output_dict = {
            category: {
                "subcategories": list(data["subcategories"])
            }
            for category, data in self.categories.items()
        }
        
        with open(filename, 'w') as f:
            json.dump(output_dict, f, indent=2)
        logger.info(f"Categories saved to {filename}")

class ExcelReader:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def get_sheets(self) -> List[str]:
        return pd.ExcelFile(self.file_path).sheet_names
    
    def read_descriptions(self, sheet_name: str, desc_column: str) -> List[str]:
        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        if desc_column not in df.columns:
            raise ValueError(f"Column {desc_column} not found in sheet")
        return df[desc_column].dropna().tolist()

class AIProcessor:
    def __init__(self):
        self.model = "mistral"
        self.api_url = "http://localhost:11434/api/generate"

    def _call_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                logger.error(f"Ollama API error: Status code {response.status_code}")
                return ''
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return ''

    def process_for_categories(self, descriptions: List[str], existing_categories: List[str]) -> List[str]:
        prompt = f"""Analyze these technical product descriptions and identify the main product categories.
        
        Existing categories: {', '.join(existing_categories)}
        Either match to existing categories or create new ones only if truly different.
        
        Descriptions:
        {' | '.join(descriptions)}
        
        Return ONLY a list of category names, one per line, nothing else.
        Be specific and consistent."""
        
        response = self._call_ollama(prompt)
        if not response:
            return []
            
        categories = [
            cat.strip() for cat in response.split('\n')
            if cat.strip() and not cat.startswith('-')
        ]
        return categories or []  # Return empty list if no categories found

    def process_for_subcategories(self, category: str, descriptions: List[str], existing_subcategories: List[str]) -> List[str]:
        prompt = f"""For the product category '{category}', analyze these descriptions and identify specific subcategories.
        
        Existing subcategories: {', '.join(existing_subcategories)}
        Either match to existing subcategories or create new ones only if truly different.
        
        Descriptions:
        {' | '.join(descriptions)}
        
        Return ONLY a list of subcategory names for {category}, one per line, nothing else.
        Be specific and consistent."""
        
        response = self._call_ollama(prompt)
        if not response:
            return []
            
        subcategories = [
            subcat.strip() for subcat in response.split('\n')
            if subcat.strip() and not subcat.startswith('-')
        ]
        return subcategories or []  # Return empty list if no subcategories found

def main():
    excel_reader = ExcelReader("input.xlsx")
    category_manager = CategoryManager()
    ai_processor = AIProcessor()
    
    try:
        # Get available sheets
        sheets = excel_reader.get_sheets()
        print("\nAvailable sheets:")
        for idx, sheet in enumerate(sheets, 1):
            print(f"{idx}. {sheet}")
            
        # Get sheet selection by number
        while True:
            try:
                sheet_num = int(input("\nEnter sheet number: "))
                if 1 <= sheet_num <= len(sheets):
                    sheet_name = sheets[sheet_num - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(sheets)}")
            except ValueError:
                print("Please enter a valid number")

        # Get description column
        df = pd.read_excel("input.xlsx", sheet_name=sheet_name)
        columns = df.columns.tolist()
        
        print("\nAvailable columns:")
        for idx, column in enumerate(columns, 1):
            print(f"{idx}. {column}")
            
        while True:
            try:
                column_num = int(input("\nEnter column number: "))
                if 1 <= column_num <= len(columns):
                    desc_column = columns[column_num - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(columns)}")
            except ValueError:
                print("Please enter a valid number")
        
        # Read descriptions
        descriptions = excel_reader.read_descriptions(sheet_name, desc_column)
        logger.info(f"Processing {len(descriptions)} descriptions")
        
        # Process in batches
        batch_size = 5
        for i in range(0, len(descriptions), batch_size):
            batch = descriptions[i:i + batch_size]
            
            # Get categories
            existing_cats = category_manager.get_existing_categories()
            new_categories = ai_processor.process_for_categories(batch, existing_cats)
            
            if new_categories:  # Only process if categories were found
                # Process each category
                for category in new_categories:
                    category_manager.add_category(category)
                    
                    # Get subcategories
                    existing_subcats = category_manager.get_existing_subcategories(category)
                    new_subcategories = ai_processor.process_for_subcategories(
                        category, batch, existing_subcats
                    )
                    
                    # Add subcategories
                    for subcategory in new_subcategories:
                        category_manager.add_subcategory(category, subcategory)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(descriptions) + batch_size - 1)//batch_size}")
        
        # Save results
        category_manager.save_to_json()
        logger.info("Processing complete")
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise

if __name__ == "__main__":
    main()