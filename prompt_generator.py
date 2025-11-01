import openai
from config import Config
from prompt_repository import PromptRepository

class PromptGenerator:
    def __init__(self):
        self.config = Config()
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.config.api_key)
        # Initialize prompt repository
        self.repository = PromptRepository()
        self.parameter_order = [
            'context',
            'art_style', 
            'camera_angle',
            'environment',
            'lighting',
            'focus',
            'color_palette',
            'composition',
            'modifiers'
        ]
        
        self.parameter_labels = {
            'context': 'Context/Subject',
            'art_style': 'Image Style',
            'camera_angle': 'Camera Angle',
            'environment': 'Environment',
            'lighting': 'Lighting',
            'focus': 'Focus',
            'color_palette': 'Color Palette',
            'composition': 'Composition',
            'modifiers': 'Additional Modifiers'
        }
        
        self.tooltips = {
            'context': 'Main subject or action (e.g., "woman reading a book", "mountain landscape")',
            'art_style': 'Image style, artistic medium, photographer, or artist (e.g., "photograph by Henri Cartier-Bresson", "digital painting", "35mm street photography")',
            'camera_angle': 'Camera perspective (e.g., "close-up", "overhead view", "wide angle")',
            'environment': 'Setting or location (e.g., "forest", "modern office", "underwater")',
            'lighting': 'Lighting conditions (e.g., "golden hour", "dramatic shadows", "soft natural light")',
            'focus': 'Depth of field (e.g., "sharp foreground", "bokeh background", "everything in focus")',
            'color_palette': 'Color scheme (e.g., "pastel tones", "monochrome", "vibrant colors")',
            'composition': 'Visual arrangement (e.g., "rule of thirds", "centered", "diagonal composition")',
            'modifiers': 'Additional elements (e.g., "moody atmosphere", "high detail", "cinematic")'
        }
    
    def generate_prompt(self, parameters: dict) -> str:
        """Generate a structured Stable Diffusion Flux prompt from parameters"""
        prompt_parts = []
        
        for param in self.parameter_order:
            value = parameters.get(param, '').strip()
            if value:
                prompt_parts.append(value)
        
        if not prompt_parts:
            return "Please fill in at least one parameter to generate a prompt."
        
        # Join with commas and ensure proper formatting
        prompt = ', '.join(prompt_parts)
        
        # Clean up any double commas or extra spaces
        prompt = ' '.join(prompt.split())
        prompt = prompt.replace(' ,', ',').replace(',,', ',')
        
        return prompt
    
    def optimize_prompt_with_openai(self, parameters: dict) -> str:
        """Use OpenAI API to optimize the prompt for Flux"""
        try:
            # Build the user input from parameters
            user_input = []
            for param in self.parameter_order:
                value = parameters.get(param, '').strip()
                if value:
                    label = self.parameter_labels.get(param, param)
                    user_input.append(f"{label}: {value}")
            
            if not user_input:
                return "Please fill in at least one parameter to generate a prompt."
            
            user_prompt = "\n".join(user_input)
            
            # Create the system prompt for Flux optimization
            system_prompt = """You are an expert Stable Diffusion Flux prompt engineer. Your task is to take the user's detailed description and transform it into a long, highly detailed, Flux-optimized prompt for image generation.

Key rules:
- Never omit, summarize, or reword any user-provided details. All user input must appear in the output, verbatim and in full, at the start of the prompt.
- Expand the prompt by adding relevant artistic, cinematic, technical, and atmospheric details, but always after the user's original description.
- Use comma-separated format: [user description], [art style], [camera angle], [lighting], [environment], [composition], [quality modifiers], [format/aspect ratio if provided].
- Add professional photography, film, and art terminology as appropriate.
- Output only the final prompt, no explanations or extra text.

Example:
User: “A young detective from the 1940s, Pulp fiction style illustration, Dutch tilt, City street in the 1940s at night, chiaroscuro, film noire, A lone figure, Somber tones with splashes of bright colour, Vertical book cover format, Young man holding a 45 automatic and wearing a trench coat and fedora looking wearily ahead as he's getting ready for trouble”

Output: “A young detective from the 1940s, Pulp fiction style illustration, Dutch tilt, City street in the 1940s at night, chiaroscuro, film noire, A lone figure, Somber tones with splashes of bright colour, Vertical book cover format, Young man holding a 45 automatic and wearing a trench coat and fedora looking wearily ahead as he's getting ready for trouble, cinematic lighting, dramatic shadows, high detail, professional illustration, 8k, masterpiece”
"""

            # Make the API call using the client
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please optimize this input for a Flux prompt:\n\n{user_prompt}"}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            optimized_prompt = response.choices[0].message.content.strip()
            return optimized_prompt
            
        except Exception as e:
            # Fallback to basic generation if OpenAI fails
            print(f"OpenAI optimization failed: {e}")
            return self.generate_prompt(parameters)
    
    def get_parameter_labels(self):
        """Return the parameter labels for UI display"""
        return self.parameter_labels
    
    def get_tooltips(self):
        """Return tooltips for parameter guidance"""
        return self.tooltips
    
    def get_parameter_order(self):
        """Return the order parameters should be displayed"""
        return self.parameter_order
    
    def validate_parameters(self, parameters: dict) -> tuple[bool, str]:
        """Validate parameters and return (is_valid, error_message)"""
        # Check if at least one parameter is filled
        has_content = any(parameters.get(param, '').strip() for param in self.parameter_order)
        
        if not has_content:
            return False, "Please fill in at least one parameter."
        
        # Check for excessively long inputs
        for param, value in parameters.items():
            if isinstance(value, str) and len(value) > 500:
                label = self.parameter_labels.get(param, param)
                return False, f"{label} is too long (max 500 characters)."
        
        return True, ""
    
    def get_empty_parameters(self):
        """Return a dictionary with empty parameters"""
        return {param: '' for param in self.parameter_order}
    
    def optimize_prompt_with_repository(self, parameters: dict) -> str:
        """Use the prompt repository to enhance prompt generation"""
        try:
            # Get enhanced context from repository
            user_input = self._format_user_input(parameters)
            enhanced_context = self.repository.get_enhanced_prompt_context(user_input)
            
            # Create the system prompt using repository knowledge
            system_prompt = """You are an expert Stable Diffusion Flux prompt engineer with access to a comprehensive knowledge base. Your task is to create highly optimized prompts using the provided context and knowledge base.

Key rules:
- Use the master prompt guidance and knowledge base information
- Include technical camera details, lens specifications, and exposure settings
- Wrap main subjects in brackets for emphasis: [subject]
- Use comma-separated structure with logical ordering
- Include negative prompts when appropriate: --neg [unwanted elements]
- Specify aspect ratios: --ar 16:9
- Add technical parameters from the knowledge base
- Ensure prompts are free of conflicting instructions

Generate a professional, technically accurate prompt optimized for Flux models."""

            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a Flux-optimized prompt using this context:\n\n{enhanced_context}"}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            optimized_prompt = response.choices[0].message.content.strip()
            
            # Mark the master prompt as used
            summary = self.repository.get_repository_summary()
            if summary.get("most_used_prompt"):
                self.repository.use_master_prompt(summary["most_used_prompt"]["id"])
            
            return optimized_prompt
            
        except Exception as e:
            print(f"Repository optimization failed: {e}")
            # Fallback to standard optimization
            return self.optimize_prompt_with_openai(parameters)
    
    def _format_user_input(self, parameters: dict) -> str:
        """Format user parameters into a readable input string"""
        user_input_parts = []
        
        for param in self.parameter_order:
            value = parameters.get(param, '').strip()
            if value:
                label = self.parameter_labels.get(param, param)
                user_input_parts.append(f"{label}: {value}")
        
        return "\n".join(user_input_parts)
    
    def get_repository_summary(self):
        """Get summary of the prompt repository"""
        return self.repository.get_repository_summary()
    
    def search_knowledge_base(self, search_term: str):
        """Search the knowledge base for relevant information"""
        return self.repository.search_knowledge_base(search_term)
