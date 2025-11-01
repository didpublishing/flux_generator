import streamlit as st
import streamlit.components.v1 as components

def scrollable_dropdown(
    label: str,
    options: list,
    key: str,
    default_value: str = "",
    help_text: str = None,
    placeholder: str = "Select an option...",
    height: int = 200
):
    """
    Create a scrollable dropdown component using Streamlit's selectbox with custom styling
    
    Args:
        label: Label for the dropdown
        options: List of options to display
        key: Unique key for the component
        default_value: Default selected value
        help_text: Help text to display
        placeholder: Placeholder text when no option is selected
        height: Height of the dropdown in pixels
    
    Returns:
        Selected value
    """
    
    # Add custom CSS for scrollable dropdown
    st.markdown(f"""
    <style>
    .stSelectbox > div > div {{
        max-height: {height}px;
        overflow-y: auto;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Create the selectbox with options
    if not options:
        st.warning(f"No options available for {label}")
        return default_value
    
    # Add a "None" option at the beginning
    display_options = [placeholder] + options
    
    # Find the index of the default value
    default_index = 0
    if default_value and default_value in options:
        default_index = options.index(default_value) + 1
    
    selected_value = st.selectbox(
        label,
        options=display_options,
        index=default_index,
        key=key,
        help=help_text
    )
    
    # Return the actual value (not the placeholder)
    if selected_value == placeholder:
        return ""
    return selected_value

def scrollable_dropdown_with_search(
    label: str,
    options: list,
    key: str,
    default_value: str = "",
    help_text: str = None,
    placeholder: str = "Type to search...",
    height: int = 200
):
    """
    Create a scrollable dropdown with search functionality
    
    Args:
        label: Label for the dropdown
        options: List of options to display
        key: Unique key for the component
        default_value: Default selected value
        help_text: Help text to display
        placeholder: Placeholder text for search
        height: Height of the dropdown in pixels
    
    Returns:
        Selected value
    """
    
    # Create a search input
    search_term = st.text_input(
        f"Search {label.lower()}:",
        key=f"{key}_search",
        placeholder=placeholder,
        help=help_text
    )
    
    # Filter options based on search term
    if search_term:
        filtered_options = [opt for opt in options if search_term.lower() in opt.lower()]
    else:
        filtered_options = options
    
    # Create the scrollable dropdown with filtered options
    return scrollable_dropdown(
        label=label,
        options=filtered_options,
        key=f"{key}_dropdown",
        default_value=default_value,
        help_text=None,
        placeholder="Select an option...",
        height=height
    )

def create_parameter_input(
    parameter: str,
    options: list,
    current_value: str = "",
    key_prefix: str = "param"
):
    """
    Create a parameter input with scrollable dropdown
    
    Args:
        parameter: Parameter name
        options: List of options for the parameter
        current_value: Current value of the parameter
        key_prefix: Prefix for the key
    
    Returns:
        Selected value
    """
    
    # Parameter labels and help text
    labels = {
        'camera_angle': 'Camera Angle',
        'art_style': 'Image Style',
        'lighting': 'Lighting',
        'environment': 'Environment',
        'focus': 'Focus',
        'color_palette': 'Color Palette',
        'composition': 'Composition'
    }
    
    help_texts = {
        'camera_angle': 'Camera perspective (e.g., "close-up", "overhead view", "wide angle")',
        'art_style': 'Image style, artistic medium, photographer, or artist (e.g., "photograph by Henri Cartier-Bresson", "digital painting", "35mm street photography")',
        'lighting': 'Lighting conditions (e.g., "golden hour", "dramatic shadows", "soft natural light")',
        'environment': 'Setting or location (e.g., "forest", "modern office", "underwater")',
        'focus': 'Depth of field (e.g., "sharp foreground", "bokeh background", "everything in focus")',
        'color_palette': 'Color scheme (e.g., "pastel tones", "monochrome", "vibrant colors")',
        'composition': 'Visual arrangement (e.g., "rule of thirds", "centered", "diagonal composition")'
    }
    
    label = labels.get(parameter, parameter.title())
    help_text = help_texts.get(parameter, "")
    
    # Check if options are available
    if not options:
        st.warning(f"No options available for {label}")
        return current_value
    
    # Create a search input
    search_key = f"{key_prefix}_{parameter}_search"
    search_term = st.text_input(
        f"Search {label.lower()}:",
        key=search_key,
        placeholder=f"Type to search {label.lower()}...",
        help=help_text
    )
    
    # Filter options based on search term
    if search_term:
        filtered_options = [opt for opt in options if search_term.lower() in opt.lower()]
    else:
        filtered_options = options
    
    # Create the selectbox with filtered options
    if not filtered_options:
        st.info(f"No options found matching '{search_term}'")
        return current_value
    
    # Add a "None" option at the beginning
    display_options = ["Select an option..."] + filtered_options
    
    # Find the index of the current value
    default_index = 0
    if current_value and current_value in filtered_options:
        default_index = filtered_options.index(current_value) + 1
    
    selected_value = st.selectbox(
        label,
        options=display_options,
        index=default_index,
        key=f"{key_prefix}_{parameter}",
        help=None
    )
    
    # Return the actual value (not the placeholder)
    if selected_value == "Select an option...":
        return ""
    return selected_value
