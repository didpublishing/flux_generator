import os
import re
from typing import Dict, List, Set

class PromptOptionsParser:
    """Parse prompt files to extract options for automated parameter selection"""
    
    def __init__(self, prompts_folder: str = "prompts"):
        self.prompts_folder = prompts_folder
        self.options = {
            'camera_angle': [],
            'art_style': [],
            'lighting': [],
            'environment': [],
            'focus': [],
            'color_palette': [],
            'composition': []
        }
        self._parse_all_files()
    
    def _parse_all_files(self):
        """Parse all relevant files in the prompts folder"""
        if not os.path.exists(self.prompts_folder):
            return
        
        # Parse camera angles
        self._parse_camera_angles()
        
        # Parse art styles
        self._parse_art_styles()
        
        # Parse lighting options
        self._parse_lighting()
        
        # Parse environment options
        self._parse_environments()
        
        # Parse focus options
        self._parse_focus()
        
        # Parse color palette options
        self._parse_color_palettes()
        
        # Parse composition options
        self._parse_compositions()
    
    def _parse_camera_angles(self):
        """Extract camera angle options from relevant files including lens info from photographers"""
        camera_angles = set()
        
        # Extract camera/lens info from Photographers and Styles Reference.txt
        photographers_file = os.path.join(self.prompts_folder, "Photographers and Styles Reference.txt")
        if os.path.exists(photographers_file):
            with open(photographers_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for camera/lens information section
                if "Camera/Lens Information for Camera Angle Section" in content:
                    lines = content.split('\n')
                    in_camera_section = False
                    for line in lines:
                        if "Camera/Lens Information for Camera Angle Section" in line:
                            in_camera_section = True
                            continue
                        elif in_camera_section:
                            if line.strip() and not line.startswith('='):
                                # Extract lens specifications from the descriptions
                                parts = line.split(':')
                                if len(parts) > 1:
                                    lens_desc = parts[1].strip()
                                    # Split by comma and extract individual lens specs
                                    terms = [t.strip() for t in lens_desc.split(',')]
                                    for term in terms:
                                        if term and len(term) > 2:
                                            camera_angles.add(term)
                            elif line.startswith('='):
                                break
        
        # From Cinematic Camera Prompts.txt
        camera_file = os.path.join(self.prompts_folder, "Cinematic Camera Prompts.txt")
        if os.path.exists(camera_file):
            with open(camera_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract camera angles from the structured format
                angle_patterns = [
                    r'`([^`]+)`',  # Backtick wrapped terms
                    r'-\s*`([^`]+)`',  # Bullet point with backticks
                    r'-\s*([^,\n]+)',  # Bullet point terms
                ]
                
                for pattern in angle_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        angle = match.strip()
                        # Clean up the angle
                        angle = self._clean_option(angle)
                        if angle and len(angle) > 2 and not self._is_table_header(angle):
                            camera_angles.add(angle)
        
        # From shot size sheet prompts.txt
        shot_file = os.path.join(self.prompts_folder, "shot size sheet prompts.txt")
        if os.path.exists(shot_file):
            with open(shot_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract shot types
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('shot size sheet'):
                        # Clean up the line
                        angle = self._clean_option(line)
                        if angle and len(angle) > 2 and not self._is_table_header(angle):
                            camera_angles.add(angle)
        
        # From shot description sheet.txt
        shot_desc_file = os.path.join(self.prompts_folder, "shot description sheet.txt")
        if os.path.exists(shot_desc_file):
            with open(shot_desc_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract camera angles from descriptions
                angle_patterns = [
                    r'`([^`]+)`',
                    r'-\s*([^,\n]+)',
                ]
                
                for pattern in angle_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        angle = self._clean_option(match)
                        if angle and len(angle) > 2 and not self._is_table_header(angle):
                            camera_angles.add(angle)
        
        self.options['camera_angle'] = sorted(list(camera_angles))
    
    def _parse_art_styles(self):
        """Extract image style options from relevant files including photographers"""
        art_styles = set()
        
        # From Photographers and Styles Reference.txt
        photographers_file = os.path.join(self.prompts_folder, "Photographers and Styles Reference.txt")
        if os.path.exists(photographers_file):
            with open(photographers_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    # Skip headers, separators, and empty lines
                    if line and not line.startswith('=') and not line.startswith('-') and '—' in line:
                        # Extract photographer name (before the —)
                        photographer = line.split('—')[0].strip()
                        if photographer and len(photographer) > 2:
                            # Add multiple variations
                            art_styles.add(f"photograph by {photographer}")
                            art_styles.add(f"photography style of {photographer}")
                            art_styles.add(f"image style of {photographer}")
                    
                    # Also parse prompt patterns section
                    if ':' in line and ('street' in line.lower() or 'color' in line.lower() or 'portrait' in line.lower() or 'landscape' in line.lower()):
                        # Extract style descriptions from prompt patterns
                        style_desc = line.split(':')[0].strip()
                        if style_desc and len(style_desc) > 5:
                            art_styles.add(style_desc)
        
        # From Comic Artists in prompt.txt
        artists_file = os.path.join(self.prompts_folder, "Comic  Artists in prompt.txt")
        if os.path.exists(artists_file):
            with open(artists_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract artist names and styles
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Steps:') and not line.startswith('Uploaded'):
                        # Clean up artist names
                        if ',' in line:
                            artists = line.split(',')
                            for artist in artists:
                                artist = artist.strip()
                                if artist and len(artist) > 2:
                                    art_styles.add(f"art style of {artist}")
                                    art_styles.add(f"image style of {artist}")
                        else:
                            if line and len(line) > 2:
                                art_styles.add(f"art style of {line}")
                                art_styles.add(f"image style of {line}")
        
        # From visual style from comic artists.txt
        visual_file = os.path.join(self.prompts_folder, "visual style from comic artists.txt")
        if os.path.exists(visual_file):
            with open(visual_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract artist names
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Here are') and not line.startswith('1960s') and not line.startswith('1980s'):
                        # Extract artist names
                        if ' - ' in line:
                            artist = line.split(' - ')[0].strip()
                            if artist and len(artist) > 2:
                                art_styles.add(f"art style of {artist}")
                                art_styles.add(f"image style of {artist}")
                        elif line and len(line) > 2 and not line.startswith('DC Comics') and not line.startswith('Marvel Comics'):
                            art_styles.add(f"art style of {line}")
                            art_styles.add(f"image style of {line}")
        
        # Add general art styles
        general_styles = [
            "digital painting", "photograph", "watercolor", "oil painting", "pencil sketch",
            "charcoal drawing", "ink illustration", "comic book style", "manga style",
            "anime style", "realistic", "stylized", "cartoon", "abstract", "impressionist",
            "surreal", "minimalist", "detailed", "sketch", "concept art", "matte painting",
            "35mm photography", "medium format photography", "large format photography",
            "street photography", "documentary photography", "portrait photography",
            "landscape photography", "fashion photography", "fine art photography"
        ]
        
        for style in general_styles:
            art_styles.add(style)
        
        self.options['art_style'] = sorted(list(art_styles))
    
    def _parse_lighting(self):
        """Extract lighting options from relevant files including photographer references"""
        lighting_options = set()
        
        # Extract lighting info from Photographers and Styles Reference.txt
        photographers_file = os.path.join(self.prompts_folder, "Photographers and Styles Reference.txt")
        if os.path.exists(photographers_file):
            with open(photographers_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for lighting information section
                if "Lighting Information for Lighting Section" in content:
                    lines = content.split('\n')
                    in_lighting_section = False
                    for line in lines:
                        if "Lighting Information for Lighting Section" in line:
                            in_lighting_section = True
                            continue
                        elif in_lighting_section:
                            if line.strip() and not line.startswith('='):
                                # Extract lighting terms from the descriptions
                                parts = line.split(':')
                                if len(parts) > 1:
                                    lighting_desc = parts[1].strip()
                                    # Split by comma and extract individual terms
                                    terms = [t.strip() for t in lighting_desc.split(',')]
                                    for term in terms:
                                        if term and len(term) > 3:
                                            lighting_options.add(term)
                            elif line.startswith('='):
                                break
        
        # Common lighting terms
        lighting_terms = [
            "golden hour", "blue hour", "dramatic lighting", "soft natural light",
            "harsh sunlight", "moonlight", "candlelight", "neon lighting",
            "studio lighting", "rim lighting", "backlighting", "side lighting",
            "chiaroscuro", "film noir lighting", "cinematic lighting", "moody lighting",
            "warm lighting", "cool lighting", "dramatic shadows", "soft shadows",
            "hard shadows", "natural lighting", "artificial lighting", "ambient lighting",
            "spotlight", "floodlight", "strobe lighting", "fluorescent lighting",
            "incandescent lighting", "LED lighting", "firelight", "torchlight",
            "available light", "on-camera flash", "hard sun", "white seamless",
            "complex film lighting", "harsh midday sun", "overcast sky", "long exposures"
        ]
        
        for lighting in lighting_terms:
            lighting_options.add(lighting)
        
        self.options['lighting'] = sorted(list(lighting_options))
    
    def _parse_environments(self):
        """Extract environment options from relevant files"""
        environments = set()
        
        # Common environment terms
        environment_terms = [
            "forest", "desert", "mountain", "ocean", "city", "urban", "rural",
            "indoor", "outdoor", "office", "home", "restaurant", "park",
            "beach", "lake", "river", "canyon", "valley", "plains", "hills",
            "tropical", "arctic", "tundra", "jungle", "savanna", "grassland",
            "underwater", "space", "sky", "clouds", "storm", "rain", "snow",
            "fog", "mist", "dawn", "dusk", "night", "day", "sunset", "sunrise",
            "modern", "ancient", "futuristic", "medieval", "victorian", "industrial",
            "abandoned", "ruins", "temple", "castle", "palace", "cave", "tunnel"
        ]
        
        for env in environment_terms:
            environments.add(env)
        
        self.options['environment'] = sorted(list(environments))
    
    def _parse_focus(self):
        """Extract focus options from relevant files including photographer references"""
        focus_options = set()
        
        # Extract focus info from Photographers and Styles Reference.txt
        photographers_file = os.path.join(self.prompts_folder, "Photographers and Styles Reference.txt")
        if os.path.exists(photographers_file):
            with open(photographers_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for focus information section
                if "Focus Information for Focus Section" in content:
                    lines = content.split('\n')
                    in_focus_section = False
                    for line in lines:
                        if "Focus Information for Focus Section" in line:
                            in_focus_section = True
                            continue
                        elif in_focus_section:
                            if line.strip() and not line.startswith('='):
                                # Extract focus terms from the descriptions
                                parts = line.split(':')
                                if len(parts) > 1:
                                    focus_desc = parts[1].strip()
                                    # Split by comma and extract individual terms
                                    terms = [t.strip() for t in focus_desc.split(',')]
                                    for term in terms:
                                        if term and len(term) > 3:
                                            focus_options.add(term)
                            elif line.startswith('='):
                                break
        
        # Common focus terms
        focus_terms = [
            "sharp foreground", "bokeh background", "everything in focus",
            "shallow depth of field", "deep depth of field", "selective focus",
            "macro focus", "tilt-shift", "blurred background", "sharp background",
            "foreground blur", "background blur", "center focus", "edge focus",
            "hyperfocal distance", "infinity focus", "close focus", "distant focus",
            "soft focus", "hard focus", "crystal clear", "hazy", "dreamy focus",
            "zone focus", "f/8–f/16", "f/1.4–f/5.6", "f/22–f/64", "tripod required"
        ]
        
        for focus in focus_terms:
            focus_options.add(focus)
        
        self.options['focus'] = sorted(list(focus_options))
    
    def _parse_color_palettes(self):
        """Extract color palette options from relevant files"""
        color_palettes = set()
        
        # Common color palette terms
        color_terms = [
            "monochrome", "black and white", "sepia", "grayscale", "colorful",
            "vibrant colors", "muted colors", "pastel tones", "earth tones",
            "warm colors", "cool colors", "primary colors", "secondary colors",
            "complementary colors", "analogous colors", "triadic colors",
            "split-complementary", "tetradic colors", "neutral colors",
            "bold colors", "subtle colors", "high contrast", "low contrast",
            "saturated", "desaturated", "bright", "dark", "light", "rich colors",
            "pale colors", "deep colors", "vivid colors", "soft colors",
            "harsh colors", "gentle colors", "intense colors", "mellow colors"
        ]
        
        for color in color_terms:
            color_palettes.add(color)
        
        self.options['color_palette'] = sorted(list(color_palettes))
    
    def _parse_compositions(self):
        """Extract composition options from relevant files"""
        compositions = set()
        
        # Common composition terms
        composition_terms = [
            "rule of thirds", "centered", "diagonal composition", "triangular composition",
            "circular composition", "linear composition", "symmetrical", "asymmetrical",
            "balanced", "unbalanced", "leading lines", "framing", "layering",
            "foreground", "middle ground", "background", "depth", "perspective",
            "bird's eye view", "worm's eye view", "eye level", "low angle", "high angle",
            "close-up", "wide shot", "medium shot", "long shot", "extreme close-up",
            "over the shoulder", "point of view", "two shot", "group shot", "single shot",
            "dynamic composition", "static composition", "flowing composition",
            "geometric composition", "organic composition", "minimalist composition",
            "complex composition", "simple composition", "dramatic composition",
            "subtle composition", "bold composition", "delicate composition"
        ]
        
        for comp in composition_terms:
            compositions.add(comp)
        
        self.options['composition'] = sorted(list(compositions))
    
    def get_options_for_parameter(self, parameter: str) -> List[str]:
        """Get options for a specific parameter"""
        return self.options.get(parameter, [])
    
    def get_all_options(self) -> Dict[str, List[str]]:
        """Get all available options"""
        return self.options
    
    def add_custom_option(self, parameter: str, option: str):
        """Add a custom option to a parameter"""
        if parameter in self.options:
            if option not in self.options[parameter]:
                self.options[parameter].append(option)
                self.options[parameter].sort()
    
    def remove_option(self, parameter: str, option: str):
        """Remove an option from a parameter"""
        if parameter in self.options and option in self.options[parameter]:
            self.options[parameter].remove(option)
    
    def _clean_option(self, option: str) -> str:
        """Clean up an option string"""
        if not option:
            return ""
        
        # Remove extra whitespace and tabs
        option = re.sub(r'\s+', ' ', option.strip())
        
        # Remove table-like formatting
        option = re.sub(r'\t+', ' ', option)
        
        # Remove pipe characters and table separators
        option = re.sub(r'\|', '', option)
        
        # Remove common unwanted prefixes
        unwanted_prefixes = ['ExamplesL', 'shot size sheet:', 'Camera Position']
        for prefix in unwanted_prefixes:
            if option.startswith(prefix):
                return ""
        
        # Remove lines that are clearly table headers
        if '|' in option and ('Shot' in option or 'Angle' in option):
            return ""
        
        return option.strip()
    
    def _is_table_header(self, option: str) -> bool:
        """Check if an option is a table header"""
        table_indicators = [
            'Camera Position', 'Extreme Long Shot', 'Long Shot', 'Mid-shot',
            'Close-Up', 'Extreme Close-Up', 'Eye Level', 'High Angle',
            'Low Angle', 'Over the Shoulder', 'Dolly Shot', 'Crane Shot',
            'Tracking Shot', 'Aerial View', 'Steadicam Shot'
        ]
        
        for indicator in table_indicators:
            if indicator in option:
                return True
        
        return False
