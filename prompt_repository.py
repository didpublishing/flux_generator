import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from pathlib import Path

class PromptRepository:
    """
    A repository system for storing and managing master prompts and knowledge base
    for AI prompt refinement and generation.
    """
    
    def __init__(self, repo_file='prompts/prompt_repository.json'):
        # Resolve repo file relative to this module to avoid CWD surprises
        base_dir = Path(__file__).parent.resolve()
        repo_path = Path(repo_file)
        if not repo_path.is_absolute():
            repo_path = base_dir / repo_path
        self.repo_file = str(repo_path)
        self.ensure_repository_exists()
    
    def ensure_repository_exists(self):
        """Create repository file with default structure if it doesn't exist"""
        if not os.path.exists(self.repo_file):
            default_repo = {
                "master_prompts": {},
                "knowledge_base": {
                    "camera_angles": [],
                    "image_formats": [],
                    "technical_parameters": [],
                    "style_guides": [],
                    "negative_prompts": []
                },
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat()
                }
            }
            self._save_repository(default_repo)
    
    def _load_repository(self) -> Dict[str, Any]:
        """Load the repository from file"""
        try:
            with open(self.repo_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load repository: {str(e)}")
    
    def _save_repository(self, data: Dict[str, Any]):
        """Save the repository to file"""
        try:
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.repo_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save repository: {str(e)}")
    
    def add_master_prompt(self, name: str, content: str, category: str = "general", 
                         description: str = "") -> str:
        """Add a new master prompt to the repository"""
        repo = self._load_repository()
        
        prompt_id = str(uuid.uuid4())[:8]
        master_prompt = {
            "id": prompt_id,
            "name": name,
            "content": content,
            "category": category,
            "description": description,
            "created": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0
        }
        
        repo["master_prompts"][prompt_id] = master_prompt
        self._save_repository(repo)
        return prompt_id
    
    def get_master_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific master prompt by ID"""
        repo = self._load_repository()
        return repo["master_prompts"].get(prompt_id)
    
    def get_all_master_prompts(self) -> List[Dict[str, Any]]:
        """Get all master prompts"""
        repo = self._load_repository()
        return list(repo["master_prompts"].values())
    
    def update_master_prompt(self, prompt_id: str, **updates) -> bool:
        """Update a master prompt"""
        repo = self._load_repository()
        
        if prompt_id in repo["master_prompts"]:
            for key, value in updates.items():
                if key in repo["master_prompts"][prompt_id]:
                    repo["master_prompts"][prompt_id][key] = value
            self._save_repository(repo)
            return True
        return False
    
    def delete_master_prompt(self, prompt_id: str) -> bool:
        """Delete a master prompt"""
        repo = self._load_repository()
        
        if prompt_id in repo["master_prompts"]:
            del repo["master_prompts"][prompt_id]
            self._save_repository(repo)
            return True
        return False
    
    def use_master_prompt(self, prompt_id: str) -> Optional[str]:
        """Mark a master prompt as used and return its content"""
        repo = self._load_repository()
        
        if prompt_id in repo["master_prompts"]:
            prompt = repo["master_prompts"][prompt_id]
            prompt["last_used"] = datetime.now().isoformat()
            prompt["usage_count"] = prompt.get("usage_count", 0) + 1
            self._save_repository(repo)
            return prompt["content"]
        return None
    
    def add_knowledge_item(self, category: str, item: str, description: str = "") -> bool:
        """Add an item to the knowledge base"""
        repo = self._load_repository()
        
        if category in repo["knowledge_base"]:
            knowledge_item = {
                "item": item,
                "description": description,
                "added": datetime.now().isoformat()
            }
            repo["knowledge_base"][category].append(knowledge_item)
            self._save_repository(repo)
            return True
        return False
    
    def get_knowledge_base(self, category: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get knowledge base items, optionally filtered by category"""
        repo = self._load_repository()
        
        if category:
            return {category: repo["knowledge_base"].get(category, [])}
        return repo["knowledge_base"]
    
    def search_knowledge_base(self, search_term: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search knowledge base for items containing the search term"""
        repo = self._load_repository()
        results = {}
        
        for category, items in repo["knowledge_base"].items():
            matching_items = []
            for item in items:
                if (search_term.lower() in item["item"].lower() or 
                    search_term.lower() in item.get("description", "").lower()):
                    matching_items.append(item)
            if matching_items:
                results[category] = matching_items
        
        return results
    
    def get_repository_summary(self) -> Dict[str, Any]:
        """Get a summary of the repository contents"""
        repo = self._load_repository()
        
        master_prompts = repo["master_prompts"]
        knowledge_base = repo["knowledge_base"]
        
        return {
            "total_master_prompts": len(master_prompts),
            "total_knowledge_items": sum(len(items) for items in knowledge_base.values()),
            "categories": {
                "master_prompts": list(set(p["category"] for p in master_prompts.values())),
                "knowledge_base": list(knowledge_base.keys())
            },
            "most_used_prompt": max(master_prompts.values(), 
                                  key=lambda x: x.get("usage_count", 0)) if master_prompts else None,
            "last_updated": repo["metadata"]["last_updated"]
        }
    
    def export_repository(self, output_file: str = None) -> str:
        """Export the entire repository to a JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"prompt_repository_export_{timestamp}.json"
        
        repo = self._load_repository()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(repo, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def import_repository(self, input_file: str) -> bool:
        """Import a repository from a JSON file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Validate structure
            required_keys = ["master_prompts", "knowledge_base", "metadata"]
            if all(key in imported_data for key in required_keys):
                self._save_repository(imported_data)
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to import repository: {str(e)}")
    
    def get_enhanced_prompt_context(self, user_input: str) -> str:
        """Get enhanced context for prompt generation using repository knowledge"""
        repo = self._load_repository()
        
        # Get the most used master prompt
        most_used = self.get_repository_summary().get("most_used_prompt")
        master_prompt = most_used["content"] if most_used else ""
        
        # Get relevant knowledge base items
        knowledge_context = []
        for category, items in repo["knowledge_base"].items():
            if items:
                knowledge_context.append(f"{category.title()}: {', '.join([item['item'] for item in items[:5]])}")
        
        # Combine all context
        context_parts = []
        if master_prompt:
            context_parts.append(f"Master Prompt: {master_prompt}")
        
        if knowledge_context:
            context_parts.append(f"Knowledge Base: {'; '.join(knowledge_context)}")
        
        context_parts.append(f"User Input: {user_input}")
        
        return "\n\n".join(context_parts)

