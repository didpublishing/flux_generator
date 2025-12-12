import openai
import base64
import io
from PIL import Image
from config import Config
import logging

logger = logging.getLogger("flux_prompt")

class ImageAnalyzer:
    def __init__(self):
        self.config = Config()
        self.client = openai.OpenAI(api_key=self.config.get_openai_api_key())
    
    def analyze_image(self, image_data, analysis_type="detailed"):
        """
        Analyze an image and generate a detailed description for prompt generation
        
        Args:
            image_data: PIL Image object or base64 encoded string
            analysis_type: "detailed", "artistic", "technical", or "simple"
        
        Returns:
            dict with analysis results
        """
        try:
            # Convert image to base64 if needed
            if isinstance(image_data, str):
                # Assume it's already base64
                base64_image = image_data
            else:
                # Convert PIL Image to base64
                buffered = io.BytesIO()
                image_data.save(buffered, format="PNG")
                base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Choose system prompt based on analysis type
            system_prompts = {
                "detailed": """You are an expert art analyst and prompt engineer. Analyze the provided image and create a comprehensive description that can be used to generate similar images with AI art tools like Stable Diffusion Flux.

Provide your analysis in this exact JSON format:
{
    "subject": "Main subject or focal point",
    "art_style": "Image style, artistic medium, photographer, or technique",
    "camera_angle": "Camera perspective and framing",
    "environment": "Setting, location, or background",
    "lighting": "Lighting conditions and mood",
    "focus": "Depth of field and focus areas",
    "color_palette": "Color scheme and tones",
    "composition": "Visual arrangement and layout",
    "modifiers": "Additional artistic elements, mood, atmosphere",
    "technical_notes": "Technical aspects like resolution, quality",
    "suggested_prompt": "Complete optimized prompt for AI generation"
}""",
                
                "artistic": """You are an art expert. Analyze this image focusing on artistic elements and style. Provide a description that captures the artistic essence, style, and visual qualities that would be useful for creating similar artwork.""",
                
                "technical": """You are a technical image analyst. Analyze this image focusing on technical aspects like composition, lighting, camera settings, and visual techniques. Provide detailed technical observations.""",
                
                "simple": """Analyze this image and provide a simple, clear description of what you see, focusing on the main elements and style."""
            }
            
            system_prompt = system_prompts.get(analysis_type, system_prompts["detailed"])
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Please analyze this image with a {analysis_type} approach:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON if it's structured
            if analysis_type == "detailed":
                try:
                    import json
                    # Try to find JSON in the response
                    if "{" in analysis_text and "}" in analysis_text:
                        # Extract JSON from the response
                        start = analysis_text.find("{")
                        end = analysis_text.rfind("}") + 1
                        json_text = analysis_text[start:end]
                        analysis_data = json.loads(json_text)
                        return analysis_data
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Return as text analysis
            return {
                "analysis_type": analysis_type,
                "description": analysis_text,
                "suggested_prompt": self._extract_prompt_from_analysis(analysis_text)
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "analysis_type": analysis_type,
                "description": "Unable to analyze image",
                "suggested_prompt": ""
            }
    
    def _extract_prompt_from_analysis(self, analysis_text):
        """Extract or generate a prompt from the analysis text"""
        try:
            # Try to find a prompt in the analysis
            if "suggested_prompt" in analysis_text.lower():
                # Extract the suggested prompt
                lines = analysis_text.split('\n')
                for line in lines:
                    if "suggested_prompt" in line.lower() or "prompt:" in line.lower():
                        return line.split(':', 1)[1].strip()
            
            # Generate a prompt from the analysis
            prompt_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Convert this image analysis into a concise, optimized prompt for Stable Diffusion Flux. Focus on the key visual elements, style, and composition."
                    },
                    {
                        "role": "user",
                        "content": f"Convert this analysis into a Flux prompt:\n\n{analysis_text}"
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return prompt_response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Prompt extraction failed: {str(e)}")
            return "Unable to generate prompt from analysis"
    
    def get_analysis_types(self):
        """Return available analysis types"""
        return {
            "detailed": "Comprehensive analysis with structured data",
            "artistic": "Focus on artistic style and visual qualities", 
            "technical": "Technical aspects like composition and lighting",
            "simple": "Basic description of main elements"
        }
