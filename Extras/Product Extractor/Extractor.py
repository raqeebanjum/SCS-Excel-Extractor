import pandas as pd
import json
import logging
from pathlib import Path
import re
from typing import List, Dict, Set
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextNormalizer:
    def __init__(self):
        self.abbreviations = {
            'ss': 'stainless steel',
            'mnpt': 'male npt',
            'fnpt': 'female npt',
            'w/': 'with',
            'w/o': 'without',
            'wo': 'without',
            'w ': 'with ',
        }
        
    def normalize(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
            
        text = text.lower()
        text = re.sub(r'[-_]', ' ', text)
        text = re.sub(r'[^a-z\s]', '', text)
        
        for abbr, full in self.abbreviations.items():
            text = re.sub(rf'\b{abbr}\b', full, text)
        
        return ' '.join(text.split())

    def get_base_product_name(self, text: str) -> str:
        normalized = self.normalize(text)
        
        specs_to_remove = [
            'with valve', 'without valve', 'with', 'without',
            'stainless steel', 'male npt', 'female npt',
        ]
        
        for spec in specs_to_remove:
            normalized = normalized.replace(spec, '').strip()
        
        return normalized

class CategoryAnalyzer:
    def __init__(self, excel_file: str):
        self.excel_file = Path(excel_file)
        self.df = None
        self.categories = {}
        self.normalizer = TextNormalizer()
        self.similarity_threshold = 0.8

    def load_excel(self) -> bool:
        try:
            self.df = pd.read_excel(self.excel_file)
            return True
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            return False

    def find_similar_groups(self, items: List[str]) -> Dict[str, List[str]]:
        groups = {}
        processed = set()

        normalized_items = [(item, self.normalizer.get_base_product_name(item)) for item in items]

        for original_item, norm_item1 in normalized_items:
            if original_item in processed or not norm_item1:
                continue

            similar_items = [original_item]
            processed.add(original_item)

            for other_item, norm_item2 in normalized_items:
                if other_item not in processed:
                    similarity = SequenceMatcher(None, norm_item1, norm_item2).ratio()
                    if similarity >= self.similarity_threshold:
                        similar_items.append(other_item)
                        processed.add(other_item)

            if similar_items:
                base_category = min(similar_items, key=lambda x: len(self.normalizer.get_base_product_name(x)))
                groups[base_category] = similar_items

        return groups

    def analyze_categories(self):
        try:
            product_types = self.df['Product Type'].dropna().unique()
            grouped_products = self.find_similar_groups(product_types)

            for base_category, similar_items in grouped_products.items():
                base_name = self.normalizer.get_base_product_name(base_category)
                if not base_name:
                    continue

                if len(similar_items) > 1:
                    if base_name not in self.categories:
                        self.categories[base_name] = {"subcategories": set()}

                    for item in similar_items:
                        if item != base_category:
                            self.categories[base_name]["subcategories"].add(item)

            self.categories = {
                category: data 
                for category, data in self.categories.items() 
                if len(data["subcategories"]) > 0
            }

            self.save_categories()

            # Count total subcategories
            total_subcategories = sum(len(data["subcategories"]) for data in self.categories.values())
            
            # Print final counts
            print(f"\nProcessing complete:")
            print(f"Total Categories: {len(self.categories)}")
            print(f"Total Subcategories: {total_subcategories}")

        except Exception as e:
            logger.error(f"Error analyzing categories: {e}")
            raise

    def save_categories(self, filename: str = "categories.json"):
        try:
            output_dict = {
                category: {
                    "subcategories": sorted(list(data["subcategories"]))
                }
                for category, data in self.categories.items()
            }
            
            with open(filename, 'w') as f:
                json.dump(output_dict, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving categories: {e}")

def main():
    try:
        analyzer = CategoryAnalyzer("input.xlsx")
        if analyzer.load_excel():
            analyzer.analyze_categories()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()