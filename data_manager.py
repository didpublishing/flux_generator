import csv
import os
import uuid
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import re

class PromptDataManager:
    def __init__(self, csv_file='prompts/prompts.csv'):
        from pathlib import Path
        import os
        import logging

        self.logger = logging.getLogger("flux_prompt")

        # Resolve CSV path relative to this file's directory
        base_dir = Path(__file__).parent.resolve()
        if not os.path.isabs(csv_file):
            csv_file = str((base_dir / csv_file).resolve())
        self.csv_file = csv_file

        self.fieldnames = [
            'id', 'timestamp', 'context', 'art_style', 'camera_angle',
            'environment', 'lighting', 'focus', 'color_palette',
            'composition', 'modifiers', 'generated_prompt'
        ]

        # Ensure directory and file exist
        self.ensure_csv_exists()
        self.logger.info(f"Initialized PromptDataManager with CSV path: {self.csv_file}")
    
    def ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        dir_name = os.path.dirname(self.csv_file)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def save_prompt(self, prompt_data: Dict[str, str]) -> str:
        """Save a new prompt to CSV and return the generated ID"""
        # Validate and sanitize data before saving
        sanitized_data = self._sanitize_prompt_data(prompt_data)
        
        prompt_id = str(uuid.uuid4())[:8]  # Short unique ID
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        row_data = {
            'id': prompt_id,
            'timestamp': timestamp,
            **sanitized_data
        }
        
        try:
            # Create backup before writing
            self._create_backup()
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writerow(row_data)
                self.logger.info(f"✅ Saved prompt to CSV: {self.csv_file}")
            return prompt_id
        except Exception as e:
            raise Exception(f"Failed to save prompt: {str(e)}")
    
    def _sanitize_prompt_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Sanitize prompt data to prevent CSV corruption"""
        sanitized = {}
        for key, value in data.items():
            if key in self.fieldnames and key not in ['id', 'timestamp']:
                # Remove or escape problematic characters
                if isinstance(value, str):
                    # Remove newlines and excessive whitespace
                    value = re.sub(r'\s+', ' ', value.strip())
                    # Escape quotes and commas that could break CSV
                    value = value.replace('"', '""')
                    # Limit length to prevent issues
                    if len(value) > 1000:
                        value = value[:1000] + "..."
                sanitized[key] = value
        return sanitized
    
    def _create_backup(self):
        """Create a backup of the CSV file before modifications"""
        if os.path.exists(self.csv_file):
            backup_file = f"{self.csv_file}.backup"
            shutil.copy2(self.csv_file, backup_file)
    
    def load_all_prompts(self) -> List[Dict[str, str]]:
        """Load all prompts from CSV"""
        prompts = []
        try:
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    prompts.append(row)
            return prompts
        except Exception as e:
            raise Exception(f"Failed to load prompts: {str(e)}")
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, str]]:
        """Get a specific prompt by ID"""
        prompts = self.load_all_prompts()
        for prompt in prompts:
            if prompt['id'] == prompt_id:
                return prompt
        return None
    
    def update_prompt(self, prompt_id: str, updated_data: Dict[str, str]) -> bool:
        """Update an existing prompt"""
        try:
            prompts = self.load_all_prompts()
            updated = False
            
            for prompt in prompts:
                if prompt['id'] == prompt_id:
                    # Update timestamp
                    prompt['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # Update data fields
                    for key, value in updated_data.items():
                        if key in self.fieldnames:
                            prompt[key] = value
                    updated = True
                    break
            
            if updated:
                # Write all prompts back to file
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                    writer.writeheader()
                    writer.writerows(prompts)
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to update prompt: {str(e)}")
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by ID"""
        try:
            prompts = self.load_all_prompts()
            original_count = len(prompts)
            prompts = [p for p in prompts if p['id'] != prompt_id]
            
            if len(prompts) < original_count:
                # Write remaining prompts back to file
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                    writer.writeheader()
                    writer.writerows(prompts)
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to delete prompt: {str(e)}")
    
    def get_prompt_summary_list(self) -> List[Dict[str, str]]:
        """Get a summary list of prompts for display (ID, timestamp, context preview)"""
        prompts = self.load_all_prompts()
        summaries = []
        for prompt in prompts:
            context_preview = prompt.get('context', '')[:50]
            if len(context_preview) == 50:
                context_preview += "..."
            
            summaries.append({
                'id': prompt['id'],
                'timestamp': prompt['timestamp'],
                'preview': context_preview
            })
        return summaries
    
    def search_prompts(self, search_term: str, field: str = None) -> List[Dict[str, str]]:
        """Search prompts by term in specified field or all fields"""
        prompts = self.load_all_prompts()
        if not search_term:
            return prompts
        
        search_term = search_term.lower()
        results = []
        
        for prompt in prompts:
            if field and field in prompt:
                # Search in specific field
                if search_term in prompt[field].lower():
                    results.append(prompt)
            else:
                # Search in all text fields
                for key, value in prompt.items():
                    if key not in ['id', 'timestamp'] and isinstance(value, str):
                        if search_term in value.lower():
                            results.append(prompt)
                            break
        
        return results
    
    def export_to_csv(self, output_file: str = None) -> str:
        """Export all prompts to a new CSV file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"prompts_export_{timestamp}.csv"
        
        prompts = self.load_all_prompts()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(prompts)
        
        return output_file
    
    def import_from_csv(self, input_file: str) -> int:
        """Import prompts from a CSV file"""
        imported_count = 0

        try:
            with open(input_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Build a proper output row with new id/timestamp
                    out_row = {key: '' for key in self.fieldnames}
                    out_row['id'] = str(uuid.uuid4())[:8]
                    out_row['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Sanitize only content fields
                    sanitized = self._sanitize_prompt_data(row)
                    for key, val in sanitized.items():
                        if key in out_row and key not in ['id', 'timestamp']:
                            out_row[key] = val

                    # Append to CSV
                    with open(self.csv_file, 'a', newline='', encoding='utf-8') as outfile:
                        writer = csv.DictWriter(outfile, fieldnames=self.fieldnames)
                        writer.writerow(out_row)

                    imported_count += 1
        except Exception as e:
            raise Exception(f"Failed to import from CSV: {str(e)}")

        return imported_count
