import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
from datetime import datetime
import uuid
import logging

from config import Config, logger
from data_manager import PromptDataManager
from prompt_generator import PromptGenerator
from image_analyzer import ImageAnalyzer
from prompt_repository import PromptRepository
from prompt_options_parser import PromptOptionsParser
from scrollable_dropdown import create_parameter_input
from image_generator import ImageGenerator
from image_provider import ImageStyle

# Configure Streamlit page
st.set_page_config(
    page_title="Flux Generator with ComfyUI", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_components():
    """Initialize all components with error handling"""
    try:
        if 'config' not in st.session_state:
            st.session_state.config = Config()
        if 'data_manager' not in st.session_state:
            st.session_state.data_manager = PromptDataManager(csv_file='prompts/prompts.csv')
        if 'prompt_generator' not in st.session_state:
            st.session_state.prompt_generator = PromptGenerator()
        if 'image_analyzer' not in st.session_state:
            st.session_state.image_analyzer = ImageAnalyzer()
        if 'prompt_repository' not in st.session_state:
            st.session_state.prompt_repository = PromptRepository()
        if 'options_parser' not in st.session_state:
            st.session_state.options_parser = PromptOptionsParser()
        if 'image_generator' not in st.session_state:
            try:
                st.session_state.image_generator = ImageGenerator()
            except Exception as e:
                logger.warning(f"Image generator not initialized: {e}")
        
        # Force refresh providers if ComfyUI might be available now
        # This helps when ComfyUI starts after the app
        if 'image_generator' in st.session_state:
            try:
                # Check if we should refresh providers (e.g., ComfyUI might have started)
                providers = st.session_state.image_generator.get_available_providers()
                if "comfyui" not in providers:
                    # Try to reinitialize router to pick up ComfyUI if it's now available
                    from image_provider_router import ImageProviderRouter
                    config = Config()
                    router = ImageProviderRouter(config)
                    if "comfyui" in router.get_available_providers():
                        # ComfyUI is now available, reinitialize generator
                        st.session_state.image_generator = ImageGenerator()
                        logger.info("Refreshed ImageGenerator to include ComfyUI provider")
            except Exception as e:
                logger.debug(f"Provider refresh check failed: {e}")
        return True
    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        st.info("Please check your .env file and ensure your OpenAI API key is configured.")
        return False

def load_css():
    """Load CSS styles - embedded for better compatibility"""
    css = '''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main Application Container */
    [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        padding: 20px !important;
    }
    
    .stApp {
        background: transparent !important;
    }
    
    .main {
        background: transparent !important;
    }
    
    /* Sidebar Styles - H:241 S:69 V:52 = rgb(42,41,132) */
    [data-testid="stSidebar"] {
        background: rgb(42, 41, 132) !important;
        width: 250px !important;
        min-width: 250px !important;
        max-width: 250px !important;
        padding: 0 !important;
        border-radius: 0 !important;
        border-right: none !important;
        transform: translateX(0) !important;
        visibility: visible !important;
    }
    
    /* Force sidebar to always be expanded */
    [data-testid="stSidebar"][aria-expanded="false"] {
        transform: translateX(0) !important;
        width: 250px !important;
    }
    
    /* Hide the collapse button or ensure sidebar stays open */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Ensure sidebar content is visible */
    section[data-testid="stSidebar"] > div {
        width: 250px !important;
        min-width: 250px !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: rgb(42, 41, 132) !important;
        padding: 30px 20px !important;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
    
    /* Sidebar Logo Image Styling - Comprehensive Centering Solution */
    /* Target all possible Streamlit image structures */
    [data-testid="stSidebar"] [data-testid="stImage"],
    [data-testid="stSidebar"] [data-testid="stImage"] > div,
    [data-testid="stSidebar"] [data-testid="stImage"] > span,
    [data-testid="stSidebar"] [data-testid="stImage"] > div > div,
    [data-testid="stSidebar"] [data-testid="stImage"] > div > img {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 auto !important;
        text-align: center !important;
        width: 100% !important;
        max-width: 100% !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Target the actual image element */
    [data-testid="stSidebar"] img,
    [data-testid="stSidebar"] [data-testid="stImage"] img,
    [data-testid="stSidebar"] [data-testid="stImage"] > div > img,
    [data-testid="stSidebar"] [data-testid="stImage"] > div > div > img,
    .sidebar-branding img,
    .sidebar-logo {
        width: 80px !important;
        height: auto !important;
        max-width: 80px !important;
        min-width: 80px !important;
        margin: 0 auto 15px auto !important;
        margin-left: auto !important;
        margin-right: auto !important;
        display: block !important;
        object-fit: contain !important;
        position: relative !important;
        left: auto !important;
        right: auto !important;
        flex-shrink: 0 !important;
    }
    
    /* Ensure logo is centered in sidebar branding - Flexbox approach */
    .sidebar-branding {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        margin-bottom: 40px !important;
        text-align: center !important;
    }
    
    .sidebar-branding [data-testid="stImage"],
    .sidebar-branding [data-testid="stImage"] > div,
    .sidebar-branding [data-testid="stImage"] > span {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 0 !important;
    }
    
    /* Sidebar Title - Centered */
    .sidebar-title {
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        margin-bottom: 15px !important;
        text-align: center !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Sidebar Branding Container */
    .sidebar-branding {
        margin-bottom: 40px;
        text-align: center;
    }
    
    /* Sidebar Buttons - Non-active buttons: H:207 S:96 V:54 = rgb(5,78,137) */
    /* Higher specificity to override .stButton styles */
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: rgb(5, 78, 137) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        margin: 5px 0 !important;
        text-align: left !important;
        width: 100% !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        justify-content: flex-start !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background: rgb(8, 95, 155) !important;
    }
    
    /* Sidebar Buttons Active/Hot - H:207 S:92 V:87 = rgb(17,130,221) */
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] button:active,
    [data-testid="stSidebar"] button:focus {
        background: rgb(17, 130, 221) !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: rgb(25, 140, 230) !important;
    }
    
    /* Main Content */
    .main .block-container {
        background: #000000 !important;
        padding: 30px 40px !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        flex: 1;
    }
    
    /* Top Bar */
    .top-bar {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .deploy-button {
        color: #FFFFFF;
        background: transparent;
        border: none;
        font-size: 14px;
        cursor: pointer;
        padding: 8px 12px;
        border-radius: 6px;
        transition: background 0.2s;
    }
    
    .menu-icon {
        color: #FFFFFF;
        cursor: pointer;
        font-size: 18px;
        padding: 8px;
    }
    
    /* Page Headers */
    .page-header {
        color: #FFFFFF !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
    }
    
    .page-subtitle {
        color: #FFFFFF !important;
        font-size: 16px !important;
        margin-bottom: 30px !important;
        opacity: 0.9 !important;
    }
    
    /* Dashboard card instructions area */
    .dashboard-card-instructions {
        background: rgb(42, 41, 132) !important; /* Same as sidebar */
        border: 1px solid rgb(50, 49, 145) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 30px 20px 20px 20px !important; /* Increased top padding to push instructions down */
        margin-bottom: 25px !important;
        min-height: 180px !important;
    }
    
    .dashboard-card-instructions ul {
        list-style: none !important;
        padding-left: 0 !important;
        margin: 0 !important;
    }
    
    .dashboard-card-instructions li {
        color: #FFFFFF !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
        margin: 8px 0 !important;
    }
    
    /* Dashboard Cards - Legacy class for any remaining markdown cards */
    .dashboard-card {
        background: rgb(42, 41, 132) !important; /* Same as sidebar */
        border: 1px solid rgb(50, 49, 145) !important;
        border-radius: 20px 20px 12px 12px !important; /* More rounded top corners */
        padding: 20px !important;
        min-height: 250px !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
        cursor: pointer !important;
        margin-bottom: 25px !important;
    }
    
    .dashboard-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 20px rgba(42, 41, 132, 0.4) !important;
    }
    
    .dashboard-card-title {
        color: #FFFFFF !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        margin-bottom: 15px !important;
    }
    
    .dashboard-card ul {
        list-style: none !important;
        padding-left: 0 !important;
        margin-top: 10px !important;
    }
    
    .dashboard-card li {
        color: #FFFFFF !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        margin: 6px 0 !important;
    }
    
    /* Form Elements */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background: #333344 !important;
        border: 1px solid #444455 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        font-size: 14px !important;
        width: 100% !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus {
        outline: none !important;
        border-color: #1A00FF !important;
        box-shadow: 0 0 0 3px rgba(26, 0, 255, 0.2) !important;
    }
    
    ::placeholder {
        color: #888888 !important;
        opacity: 0.7 !important;
    }
    
    /* Buttons - Default styling removed, use sidebar/dashboard styles instead */
    
    /* Dashboard Cards - IMPORTANT: Must come AFTER general button styles to override */
    button[key*="dashboard_"],
    button[key^="dashboard_"],
    .stButton > button[key*="dashboard_"],
    .stButton button[key^="dashboard_"] {
        background: rgb(5, 78, 137) !important; /* Same as sidebar non-active buttons */
        border: 1px solid rgb(8, 95, 155) !important;
        border-bottom: none !important;
        border-radius: 20px 20px 0 0 !important;
        padding: 20px 20px 10px 20px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        align-items: flex-start !important;
        color: #FFFFFF !important;
        font-size: 20px !important;
        font-weight: 700 !important;
    }
    
    button[key*="dashboard_"]:hover,
    button[key^="dashboard_"]:hover,
    .stButton > button[key*="dashboard_"]:hover,
    .stButton button[key^="dashboard_"]:hover {
        background: rgb(8, 95, 155) !important; /* Same as sidebar hover */
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(5, 78, 137, 0.4) !important;
    }
    
    button[key*="dashboard_"]:active,
    button[key^="dashboard_"]:active,
    .stButton > button[key*="dashboard_"]:active,
    .stButton button[key^="dashboard_"]:active {
        transform: translateY(0) !important;
    }
    
    /* Sections */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }
    
    .section-title {
        color: #FFFFFF;
        font-size: 24px;
        font-weight: 700;
    }
    
    .section-title-small {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .help-icon {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        color: #FFFFFF;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        cursor: help;
    }
    
    /* Image Upload Area */
    .drag-drop-area {
        border: 2px dashed #666666;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        background: #0A0A0A;
        margin-bottom: 15px;
        transition: border-color 0.2s, background 0.2s;
        cursor: pointer;
        position: relative;
        z-index: 1;
    }
    
    .drag-drop-area:hover {
        border-color: #1A00FF;
        background: #151515;
    }
    
    .drag-drop-area.drag-over {
        border-color: #1A00FF !important;
        background: #151515 !important;
    }
    
    .drag-drop-icon {
        font-size: 48px;
        color: #666666;
        margin-bottom: 15px;
    }
    
    .drag-drop-text {
        color: #AAAAAA;
        font-size: 16px;
        margin-bottom: 8px;
    }
    
    .drag-drop-info {
        color: #666666;
        font-size: 12px;
    }
    
    /* Analysis Type List */
    .analysis-type-list {
        list-style: none;
        padding: 0;
        margin: 15px 0;
    }
    
    .analysis-type-item {
        color: #FFFFFF;
        padding: 10px 0;
        font-size: 14px;
    }
    
    .analysis-type-item strong {
        font-weight: 600;
    }
    
    .analysis-type-item.selected {
        color: rgb(17, 130, 221); /* Match sidebar active button color */
    }
    
    /* Image Preview */
    .image-preview-container {
        background: #1E1E2E;
        border: 1px solid #333344;
        border-radius: 12px;
        padding: 20px;
        margin-top: 25px;
    }
    
    .image-info {
        color: #FFFFFF;
        font-size: 14px;
        margin-bottom: 15px;
    }
    
    .image-dimensions {
        color: #AAAAAA;
        font-size: 12px;
    }
    
    /* Instructions */
    .instructions-section {
        background: #1E1E2E;
        border-radius: 12px;
        padding: 25px;
        margin-top: 30px;
    }
    
    .instructions-title {
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 15px;
    }
    
    .instructions-list {
        color: #FFFFFF;
        list-style-position: inside;
        line-height: 1.8;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* Override Streamlit defaults */
    html, body, [data-testid="stAppViewContainer"], .main, .block-container, .stApp {
        background: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
    }
    
    .stMarkdown {
        color: #FFFFFF !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #FFFFFF !important;
    }
    </style>
    <script>
    // Force sidebar to be expanded on page load and keep it expanded
    (function() {
        function expandSidebar() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.setAttribute('aria-expanded', 'true');
                sidebar.classList.add('force-expanded');
                
                // Use setProperty with important flag
                sidebar.style.setProperty('transform', 'translateX(0)', 'important');
                sidebar.style.setProperty('width', '250px', 'important');
                sidebar.style.setProperty('min-width', '250px', 'important');
                sidebar.style.setProperty('max-width', '250px', 'important');
                sidebar.style.setProperty('visibility', 'visible', 'important');
                sidebar.style.setProperty('opacity', '1', 'important');
                
                // Also ensure the content is visible
                const sidebarContent = sidebar.querySelector('div');
                if (sidebarContent) {
                    sidebarContent.style.setProperty('width', '250px', 'important');
                    sidebarContent.style.setProperty('display', 'flex', 'important');
                }
                
                // Hide collapse button if it exists
                const collapseBtn = sidebar.querySelector('[data-testid="collapsedControl"]');
                if (collapseBtn) {
                    collapseBtn.style.setProperty('display', 'none', 'important');
                }
            }
        }
        
        // Run on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', expandSidebar);
        } else {
            expandSidebar();
        }
        
        // Run after delays to catch any late-loading elements
        setTimeout(expandSidebar, 100);
        setTimeout(expandSidebar, 500);
        setTimeout(expandSidebar, 1000);
        
        // Use MutationObserver to keep sidebar expanded
        const observer = new MutationObserver(function(mutations) {
            expandSidebar();
        });
        
        // Observe changes to the sidebar
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            observer.observe(sidebar, {
                attributes: true,
                attributeFilter: ['aria-expanded', 'style', 'class'],
                childList: true,
                subtree: true
            });
        }
        
        // Also observe the document body in case sidebar is added dynamically
        if (document.body) {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        // Function to trigger dashboard navigation
        window.triggerDashboardNav = function(pageName) {
            const button = document.querySelector('button[key*="dashboard_' + pageName + '"]');
            if (button) {
                button.click();
            }
        };
        
        // Force logo centering - Comprehensive approach
        function centerLogo() {
            // Target all image elements in sidebar
            const sidebarImages = document.querySelectorAll(
                '[data-testid="stSidebar"] img, ' +
                '[data-testid="stSidebar"] [data-testid="stImage"] img, ' +
                '[data-testid="stSidebar"] [data-testid="stImage"] > div > img, ' +
                '.sidebar-branding img, ' +
                '.sidebar-logo'
            );
            
            sidebarImages.forEach(img => {
                // Only target logo images (not buttons/icons)
                if (img.src && (img.src.includes('logo') || img.src.includes('crown') || img.closest('.sidebar-branding'))) {
                    img.style.setProperty('margin', '0 auto 15px auto', 'important');
                    img.style.setProperty('margin-left', 'auto', 'important');
                    img.style.setProperty('margin-right', 'auto', 'important');
                    img.style.setProperty('display', 'block', 'important');
                    img.style.setProperty('width', '80px', 'important');
                    img.style.setProperty('height', 'auto', 'important');
                    img.style.setProperty('max-width', '80px', 'important');
                    img.style.setProperty('min-width', '80px', 'important');
                    img.style.setProperty('object-fit', 'contain', 'important');
                }
            });
            
            // Target all Streamlit image containers in sidebar
            const imageContainers = document.querySelectorAll(
                '[data-testid="stSidebar"] [data-testid="stImage"], ' +
                '[data-testid="stSidebar"] [data-testid="stImage"] > div, ' +
                '[data-testid="stSidebar"] [data-testid="stImage"] > span, ' +
                '.sidebar-branding [data-testid="stImage"]'
            );
            
            imageContainers.forEach(container => {
                container.style.setProperty('display', 'flex', 'important');
                container.style.setProperty('justify-content', 'center', 'important');
                container.style.setProperty('align-items', 'center', 'important');
                container.style.setProperty('margin', '0 auto', 'important');
                container.style.setProperty('width', '100%', 'important');
                container.style.setProperty('padding', '0', 'important');
            });
            
            // Ensure sidebar-branding container is flex
            const brandingContainers = document.querySelectorAll('.sidebar-branding');
            brandingContainers.forEach(container => {
                container.style.setProperty('display', 'flex', 'important');
                container.style.setProperty('flex-direction', 'column', 'important');
                container.style.setProperty('align-items', 'center', 'important');
                container.style.setProperty('justify-content', 'center', 'important');
                container.style.setProperty('width', '100%', 'important');
                container.style.setProperty('text-align', 'center', 'important');
            });
        }
        
        // Run logo centering with multiple attempts and observer
        centerLogo();
        setTimeout(centerLogo, 100);
        setTimeout(centerLogo, 300);
        setTimeout(centerLogo, 500);
        setTimeout(centerLogo, 1000);
        setTimeout(centerLogo, 2000);
        
        // Use MutationObserver to watch for logo changes
        const logoObserver = new MutationObserver(function(mutations) {
            centerLogo();
        });
        
        // Observe sidebar for changes
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            logoObserver.observe(sidebar, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            });
        }
        
        // Force button colors
        function updateButtonColors() {
            const sidebarButtons = document.querySelectorAll('[data-testid="stSidebar"] button:not([kind="primary"])');
            sidebarButtons.forEach(btn => {
                const isActive = btn.getAttribute('kind') === 'primary';
                if (!isActive) {
                    btn.style.setProperty('background', 'rgb(5, 78, 137)', 'important');
                }
            });
        }
        
        updateButtonColors();
        setTimeout(updateButtonColors, 100);
        setTimeout(updateButtonColors, 500);
    })();
    </script>
    '''
    st.markdown(css, unsafe_allow_html=True)

def render_sidebar():
    """Render custom sidebar navigation"""
    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    # Sidebar branding with logo
    try:
        # Try to load the crown logo from images folder
        import os
        logo_path = 'images/logo-crown.png'
        if os.path.exists(logo_path):
            # Use cleaner HTML structure with base64 encoding for better control
            import base64
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode()
            st.sidebar.markdown(f"""
                <div class="sidebar-branding">
                    <div class="sidebar-title">FLUX GENERATOR</div>
                    <img src="data:image/png;base64,{logo_data}" class="sidebar-logo" alt="Crown Logo" style="width: 80px; height: auto; display: block; margin: 0 auto 15px auto;">
                </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback to logo.png if crown logo doesn't exist
            fallback_path = 'images/logo.png'
            if os.path.exists(fallback_path):
                import base64
                with open(fallback_path, 'rb') as f:
                    logo_data = base64.b64encode(f.read()).decode()
                st.sidebar.markdown(f"""
                    <div class="sidebar-branding">
                        <div class="sidebar-title">FLUX GENERATOR</div>
                        <img src="data:image/png;base64,{logo_data}" class="sidebar-logo" alt="Logo" style="width: 80px; height: auto; display: block; margin: 0 auto 15px auto;">
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Final fallback to SVG
                st.sidebar.markdown("""
                    <div class="sidebar-branding">
                        <div class="sidebar-title">FLUX GENERATOR</div>
                        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 10 L30 50 L50 45 L70 50 Z' fill='%23FFD700' stroke='white' stroke-width='2'/%3E%3Cpath d='M50 45 L35 70 L50 65 L65 70 Z' fill='%23FFD700' stroke='white' stroke-width='2'/%3E%3C/svg%3E" class="sidebar-logo" alt="Crown Logo" style="width: 80px; height: auto; display: block; margin: 0 auto 15px auto;">
                    </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        # Error fallback
        st.sidebar.markdown("""
            <div class="sidebar-branding">
                <div class="sidebar-title">FLUX GENERATOR</div>
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 10 L30 50 L50 45 L70 50 Z' fill='%23FFD700' stroke='white' stroke-width='2'/%3E%3Cpath d='M50 45 L35 70 L50 65 L65 70 Z' fill='%23FFD700' stroke='white' stroke-width='2'/%3E%3C/svg%3E" class="sidebar-logo" alt="Crown Logo" style="width: 80px; height: auto; display: block; margin: 0 auto 15px auto;">
            </div>
        """, unsafe_allow_html=True)
    
    # Navigation items
    nav_items = [
        ('Dashboard', '📊'),
        ('Generate Prompt', '📝'),
        ('Image Analysis', '🖼️'),
        ('Prompt Repository', '📚'),
        ('Manage Prompts', '⚙️'),
        ('Generate Images', '🎨'),
        ('Image Editing', '✏️'),
    ]
    
    # Render navigation items
    for item_name, icon in nav_items:
        is_active = st.session_state.current_page == item_name
        if st.sidebar.button(
            f"{item_name}",
            key=f"nav_{item_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_page = item_name
            st.rerun()
    
    # Bottom section
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    bottom_items = [
        ('Settings', '⚙️'),
        ('Image Vault', '🗄️'),
    ]
    
    for item_name, icon in bottom_items:
        if st.sidebar.button(
            f"{icon} {item_name}",
            key=f"nav_{item_name}",
            use_container_width=True
        ):
            st.session_state.current_page = item_name
            st.rerun()

def render_top_bar():
    """Render top bar with Deploy button"""
    st.markdown("""
        <div class="top-bar">
            <button class="deploy-button">Deploy</button>
            <div class="menu-icon">⋮</div>
        </div>
    """, unsafe_allow_html=True)

def dashboard_page():
    """Dashboard page with grid layout"""
    st.markdown("""
        <p class="page-subtitle" style="margin-top: 20px;">Generate, save, and manage your Stable Diffusion Flux prompts</p>
    """, unsafe_allow_html=True)
    
    # Dashboard cards with instructions
    cards = [
        {
            "title": "Generate Prompt",
            "instructions": [
                "Pick a model target (Flux or other).",
                "Describe subject, style, camera",
                "Add lighting, composition, context.",
                "Click Generate to get a prompt.",
                "Copy or Save to Repository."
            ],
            "page": "Generate Prompt"
        },
        {
            "title": "Image Analysis",
            "instructions": [
                "Upload an image or paste a URL.",
                "The tool generates a description of the image.",
                "Convert findings into a ready-to-use prompt.",
                "Save as a new prompt or append to an existing one."
            ],
            "page": "Image Analysis"
        },
        {
            "title": "Prompt Repository",
            "instructions": [
                "Browse, search, and filter by tags, model, or date.",
                "Open a prompt to preview, copy, or quick-edit.",
                "Duplicate, version, or favorite for fast access."
            ],
            "page": "Prompt Repository"
        },
        {
            "title": "Manage Prompts",
            "instructions": [
                "Bulk edit titles, tags, and metadata.",
                "Move prompts into collections.",
                "Import/Export prompts as JSON or CSV.",
                "Archive or delete with undo."
            ],
            "page": "Manage Prompts"
        },
        {
            "title": "Generate Images",
            "instructions": [
                "Choose a backend and model (Flux, SD, etc.).",
                "Attach a prompt from the Repository or paste one.",
                "Run."
            ],
            "page": "Generate Images"
        },
        {
            "title": "Image Editing",
            "instructions": [
                "Upload an image to edit.",
                "Enter a prompt describing the changes.",
                "Adjust strength to control how much to change.",
                "Generate and download the edited image."
            ],
            "page": "Image Editing"
        },
    ]
    
    # Create grid using columns
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    
    cols_list = [
        (row1_col1, cards[0]),
        (row1_col2, cards[1]),
        (row1_col3, cards[2]),
        (row2_col1, cards[3]),
        (row2_col2, cards[4]),
        (row2_col3, cards[5]),
    ]
    
    for col, card_data in cols_list:
        with col:
            instructions_html = "".join([f'<li>{inst}</li>' for inst in card_data["instructions"]])
            # Wrap card in a clickable container
            card_container_key = f"card_container_{card_data['page']}"
            button_key = f"dashboard_{card_data['page']}"
            
            # Create clickable card header button
            if st.button(card_data['title'], key=button_key, use_container_width=True):
                st.session_state.current_page = card_data["page"]
                st.rerun()
            
            # Display instructions below button (visually part of the card, also clickable)
            st.markdown(f"""
                <div class="dashboard-card-instructions" onclick="triggerDashboardNav('{card_data['page']}');" style="cursor: pointer;">
                    <ul style="list-style: none; padding-left: 0; margin-top: 0;">
                        {instructions_html}
                    </ul>
                </div>
            """, unsafe_allow_html=True)

def main():
    # Load CSS styles
    load_css()
    
    # Render top bar
    render_top_bar()
    
    # Render sidebar navigation
    render_sidebar()
    
    # Initialize components
    if not initialize_components():
        return
    
    # Render current page based on selection
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    if current_page == 'Dashboard':
        dashboard_page()
    elif current_page == 'Generate Prompt':
        generate_prompt_tab()
    elif current_page == 'Image Analysis':
        image_analysis_tab()
    elif current_page == 'Prompt Repository':
        prompt_repository_tab()
    elif current_page == 'Manage Prompts':
        manage_prompts_tab()
    elif current_page == 'Generate Images':
        generate_images_tab()
    elif current_page == 'Image Editing':
        image_editing_tab()
    elif current_page == 'Settings':
        st.header("Settings")
        st.info("Settings page coming soon.")
    elif current_page == 'Image Vault':
        image_vault_tab()

def generate_prompt_tab():
    """Tab for generating new prompts"""
    st.markdown("""
        <h1 class="page-header">Generate New Prompt</h1>
        <p class="page-subtitle">Generate, save, and manage your Stable Diffusion Flux prompts</p>
    """, unsafe_allow_html=True)
    
    # Show notification if a prompt was loaded
    if st.session_state.get('prompt_loaded', False):
        loaded_id = st.session_state.get('loaded_prompt_id', '')
        st.success(f"✅ Prompt {loaded_id} loaded successfully! Form fields are populated below.")
        # Clear the flag after showing
        st.session_state['prompt_loaded'] = False
    
    generator = st.session_state.prompt_generator
    data_manager = st.session_state.data_manager
    options_parser = st.session_state.options_parser
    
    # Get parameter info
    parameters = generator.get_parameter_order()
    labels = generator.get_parameter_labels()
    tooltips = generator.get_tooltips()
    
    # Show available options info - styled as link
    st.markdown("""
        <div class="section-header">
            <h2 class="section-title">Prompt Parameters</h2>
            <a href="#" class="options-preview-link" onclick="event.preventDefault(); document.querySelector('[data-testid=\\'stExpanderToggleButton\\']').click();">
                📄 Available Options Preview
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📋 Available Options Preview", expanded=False):
        st.markdown("**Available options for each parameter:**")
        all_options = options_parser.get_all_options()
        for param, options in all_options.items():
            if options:
                st.markdown(f"**{labels.get(param, param.title())}** ({len(options)} options):")
                # Show first 10 options as preview
                preview_options = options[:10]
                st.markdown(f"*{', '.join(preview_options)}*")
                if len(options) > 10:
                    st.markdown(f"*... and {len(options) - 10} more options*")
                st.markdown("---")
    
    # Create input fields
    with st.form("prompt_form"):
        
        param_values = {}
        
        # Create two columns for better layout
        col1, col2 = st.columns(2)
        
        for i, param in enumerate(parameters):
            column = col1 if i % 2 == 0 else col2
            
            with column:
                if param in ['context', 'modifiers']:
                    # Keep text areas for user-generated content
                    param_values[param] = st.text_area(
                        labels[param],
                        help=tooltips[param],
                        key=f"param_{param}"
                    )
                else:
                    # Use scrollable dropdowns for automated parameters
                    options = options_parser.get_options_for_parameter(param)
                    current_value = st.session_state.get(f"param_{param}", "")
                    
                    param_values[param] = create_parameter_input(
                        parameter=param,
                        options=options,
                        current_value=current_value,
                        key_prefix="param"
                    )
        
        # Form buttons - styled to match design
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            generate_btn = st.form_submit_button("Generate Prompt", type="primary", use_container_width=True)
        with col2:
            save_btn = st.form_submit_button("Save Prompt", use_container_width=True)
            st.markdown("""
                <style>
                    div[data-testid="column"]:nth-child(2) button {
                        background: #1E1E2E !important;
                        color: #FFFFFF !important;
                    }
                </style>
            """, unsafe_allow_html=True)
        with col3:
            clear_btn = st.form_submit_button("Clear All", use_container_width=True)
            st.markdown("""
                <style>
                    div[data-testid="column"]:nth-child(3) button {
                        background: #1E1E2E !important;
                        color: #FFFFFF !important;
                    }
                </style>
            """, unsafe_allow_html=True)
    
    # Handle form actions
    if generate_btn:
        # Validate and generate prompt
        is_valid, error_msg = generator.validate_parameters(param_values)
        
        if is_valid:
            # Use repository-enhanced generation
            generated_prompt = generator.optimize_prompt_with_repository(param_values)
            
            st.subheader("Generated Prompt:")
            st.text_area("Generated Prompt", value=generated_prompt, height=150, key="generated_prompt_display")
            
            # Copy to clipboard button for generated prompt (Generate Prompt tab)
            if generated_prompt:
                components.html(
                    f"""
                    <div>
                      <button style=\"padding:8px 12px; margin-top:6px;\" onclick=\"navigator.clipboard.writeText(text_{id(generated_prompt)}).then(()=>{{{{this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy Generated Prompt',1500)}}}});\">Copy Generated Prompt</button>
                      <script>
                        const text_{id(generated_prompt)} = {json.dumps(generated_prompt)};
                      </script>
                    </div>
                    """,
                    height=60,
                )
            
            # Store in session state for saving
            st.session_state.current_prompt = generated_prompt
            st.session_state.current_params = param_values
            
        else:
            st.error(error_msg)
    
    if save_btn:
        if 'current_prompt' in st.session_state and 'current_params' in st.session_state:
            try:
                # Prepare data for saving
                save_data = st.session_state.current_params.copy()
                save_data['generated_prompt'] = st.session_state.current_prompt
                
                # Save to CSV
                prompt_id = data_manager.save_prompt(save_data)
                st.success(f"Prompt saved with ID: {prompt_id}")
                logger.info(f"Prompt saved via web interface with ID: {prompt_id}")
                
            except Exception as e:
                st.error(f"Error saving prompt: {str(e)}")
        else:
            st.warning("Please generate a prompt first before saving")
    
    if clear_btn:
        # Clear session state
        for param in parameters:
            if f"param_{param}" in st.session_state:
                del st.session_state[f"param_{param}"]
        # Also clear generated prompt artifacts
        for key in ["current_prompt", "current_params"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def manage_prompts_tab():
    """Tab for managing saved prompts"""
    st.markdown("""
        <h1 class="page-header">Manage Prompts</h1>
        <p class="page-subtitle">Edit, delete, and organize your saved prompts</p>
    """, unsafe_allow_html=True)
    
    data_manager = st.session_state.data_manager
    
    try:
        # Search functionality
        st.subheader("🔍 Search & Filter")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("Search prompts", placeholder="Enter search term...", help="Search in all prompt fields")
        
        with col2:
            search_field = st.selectbox("Search in", ["All fields", "Context", "Image Style", "Environment", "Generated Prompt"])
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Timestamp (Newest)", "Timestamp (Oldest)", "ID", "Context"])
        
        # Load and filter prompts
        if search_term:
            field_map = {
                "All fields": None,
                "Context": "context",
                "Image Style": "art_style", 
                "Environment": "environment",
                "Generated Prompt": "generated_prompt"
            }
            field = field_map.get(search_field)
            prompts = data_manager.search_prompts(search_term, field)
        else:
            prompts = data_manager.load_all_prompts()
        
        # Sort prompts
        if prompts:
            if sort_by == "Timestamp (Newest)":
                prompts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            elif sort_by == "Timestamp (Oldest)":
                prompts.sort(key=lambda x: x.get('timestamp', ''))
            elif sort_by == "ID":
                prompts.sort(key=lambda x: x.get('id', ''))
            elif sort_by == "Context":
                prompts.sort(key=lambda x: x.get('context', '').lower())
        
        if not prompts:
            if search_term:
                st.info(f"No prompts found matching '{search_term}'")
            else:
                st.info("No saved prompts found. Generate and save some prompts first!")
            return
        
        # Display options
        st.subheader("📋 Display Options")
        show_extended = st.checkbox("Show extended columns (Image Style, Environment, etc.)", value=False)
        
        # Create DataFrame for display
        df_display = []
        for prompt in prompts:
            row = {
                'ID': prompt['id'],
                'Timestamp': prompt['timestamp'],
                'Context': prompt.get('context', '')[:100] + ('...' if len(prompt.get('context', '')) > 100 else ''),
                'Generated Prompt': prompt.get('generated_prompt', '')[:150] + ('...' if len(prompt.get('generated_prompt', '')) > 150 else '')
            }
            if show_extended:
                row['Image Style'] = prompt.get('art_style', '')[:50] + ('...' if len(prompt.get('art_style', '')) > 50 else '')
                row['Environment'] = prompt.get('environment', '')[:50] + ('...' if len(prompt.get('environment', '')) > 50 else '')
                row['Camera Angle'] = prompt.get('camera_angle', '')[:30] + ('...' if len(prompt.get('camera_angle', '')) > 30 else '')
                row['Lighting'] = prompt.get('lighting', '')[:30] + ('...' if len(prompt.get('lighting', '')) > 30 else '')
            df_display.append(row)
        
        df = pd.DataFrame(df_display)
        
        # Display prompts table
        st.subheader(f"Saved Prompts ({len(prompts)} total)")
        
        # Add selection functionality
        selected_indices = st.multiselect(
            "Select prompts to manage:",
            options=range(len(df)),
            format_func=lambda x: f"{df.iloc[x]['ID']} - {df.iloc[x]['Timestamp']}"
        )
        
        st.dataframe(df, use_container_width=True)
        
        # Management buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Load Selected", help="Load the first selected prompt into the generator"):
                if selected_indices:
                    idx = selected_indices[0]  # Load first selected
                    prompt_id = df.iloc[idx]['ID']
                    load_prompt(prompt_id)
                else:
                    st.warning("Please select a prompt to load")
        
        with col2:
            # Initialize delete confirmation state
            if 'delete_confirmation' not in st.session_state:
                st.session_state.delete_confirmation = None
            
            if st.button("🗑️ Delete Selected", help="Delete selected prompts (with confirmation)"):
                if selected_indices:
                    st.session_state.delete_confirmation = selected_indices.copy()
                    st.rerun()
                else:
                    st.warning("Please select prompts to delete")
            
            # Show delete confirmation if pending
            if st.session_state.delete_confirmation is not None:
                # Validate that confirmation indices are still valid
                valid_indices = [idx for idx in st.session_state.delete_confirmation if 0 <= idx < len(df)]
                if valid_indices:
                    delete_prompts(valid_indices, df, prompts)
                else:
                    # Clear invalid confirmation state
                    st.session_state.delete_confirmation = None
                    st.warning("Delete confirmation cancelled - selected prompts are no longer visible.")
        
        with col3:
            if st.button("📤 Export Selected", help="Export selected prompts as CSV"):
                if selected_indices:
                    selected_prompts = [prompts[i] for i in selected_indices]
                    export_csv(selected_prompts)
                else:
                    st.warning("Please select prompts to export")
        
        with col4:
            if st.button("📋 Export All", help="Export all prompts as CSV"):
                export_csv(prompts)
        
        # Import/Export section
        st.subheader("📁 Import/Export")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Export All to File"):
                try:
                    export_file = data_manager.export_to_csv()
                    st.success(f"✅ Prompts exported to: {export_file}")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
        with col2:
            uploaded_csv = st.file_uploader("📥 Import CSV", type=['csv'], help="Upload a CSV file to import prompts")
            if uploaded_csv is not None:
                if st.button("Import Prompts"):
                    try:
                        # Save uploaded file temporarily
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                            tmp_file.write(uploaded_csv.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        # Import prompts
                        imported_count = data_manager.import_from_csv(tmp_file_path)
                        
                        # Clean up temp file
                        import os
                        os.unlink(tmp_file_path)
                        
                        st.success(f"✅ Imported {imported_count} prompts successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Import failed: {str(e)}")
        
        # Show detailed view if one prompt is selected
        if len(selected_indices) == 1:
            show_prompt_details(prompts[selected_indices[0]], data_manager)
            
    except Exception as e:
        st.error(f"Error loading prompts: {str(e)}")

def load_prompt(prompt_id):
    """Load a prompt into the generator form"""
    try:
        data_manager = st.session_state.data_manager
        prompt_data = data_manager.get_prompt_by_id(prompt_id)
        
        if prompt_data:
            # Store in session state to populate form
            for param in st.session_state.prompt_generator.get_parameter_order():
                value = prompt_data.get(param, '')
                st.session_state[f"param_{param}"] = value
            
            # Store flag to show success message on Generate Prompt tab
            st.session_state['prompt_loaded'] = True
            st.session_state['loaded_prompt_id'] = prompt_id
            
            st.success(f"✅ Prompt {prompt_id} loaded successfully! Switch to 'Generate Prompt' tab to view and edit.")
            st.info("💡 Tip: The form fields are now populated with the loaded prompt values.")
            st.rerun()  # Refresh to show loaded values
        else:
            st.error("Prompt not found")
            
    except Exception as e:
        st.error(f"Error loading prompt: {str(e)}")

def delete_prompts(selected_indices, df, prompts):
    """Delete selected prompts with confirmation"""
    try:
        # Show confirmation
        st.markdown("---")
        if len(selected_indices) == 1:
            prompt_id = df.iloc[selected_indices[0]]['ID']
            context_preview = prompts[selected_indices[0]].get('context', '')[:50]
            st.warning(f"⚠️ **Delete Confirmation** - Are you sure you want to delete prompt {prompt_id}?")
            st.info(f"**Context:** {context_preview}...")
        else:
            st.warning(f"⚠️ **Delete Confirmation** - Are you sure you want to delete {len(selected_indices)} prompts?")
            st.info("This action cannot be undone.")
        
        # Confirmation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete", type="primary", key="confirm_delete_btn"):
                data_manager = st.session_state.data_manager
                deleted_count = 0
                
                for idx in selected_indices:
                    prompt_id = df.iloc[idx]['ID']
                    if data_manager.delete_prompt(prompt_id):
                        deleted_count += 1
                
                # Clear confirmation state
                st.session_state.delete_confirmation = None
                st.success(f"✅ Deleted {deleted_count} prompt(s) successfully")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key="cancel_delete_btn"):
                # Clear confirmation state
                st.session_state.delete_confirmation = None
                st.info("Deletion cancelled")
                st.rerun()
        
    except Exception as e:
        st.error(f"Error deleting prompts: {str(e)}")
        # Clear confirmation state on error
        st.session_state.delete_confirmation = None

def export_csv(prompts):
    """Export prompts as CSV download"""
    try:
        df = pd.DataFrame(prompts)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"flux_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error exporting CSV: {str(e)}")

def show_prompt_details(prompt, data_manager):
    """Show detailed view of a selected prompt with edit functionality"""
    st.subheader("📝 Prompt Details")
    
    # Initialize edit mode in session state if not exists
    if f"edit_mode_{prompt['id']}" not in st.session_state:
        st.session_state[f"edit_mode_{prompt['id']}"] = False
    
    edit_mode = st.session_state[f"edit_mode_{prompt['id']}"]
    
    # Edit mode toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Prompt ID:** {prompt['id']} | **Created:** {prompt['timestamp']}")
    with col2:
        if st.button("✏️ Edit" if not edit_mode else "👁️ View Only", key=f"toggle_edit_{prompt['id']}"):
            st.session_state[f"edit_mode_{prompt['id']}"] = not edit_mode
            st.rerun()
    
    with st.expander("View/Edit Full Details", expanded=True):
        # Store edited values
        edited_data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("ID", value=prompt['id'], disabled=True, key=f"id_{prompt['id']}")
            st.text_input("Timestamp", value=prompt['timestamp'], disabled=True, key=f"timestamp_{prompt['id']}")
            
            edited_data['context'] = st.text_area(
                "Context", 
                value=prompt.get('context', ''), 
                disabled=not edit_mode,
                key=f"context_{prompt['id']}",
                height=100
            )
            edited_data['art_style'] = st.text_input(
                "Image Style", 
                value=prompt.get('art_style', ''), 
                disabled=not edit_mode,
                key=f"art_style_{prompt['id']}"
            )
            edited_data['camera_angle'] = st.text_input(
                "Camera Angle", 
                value=prompt.get('camera_angle', ''), 
                disabled=not edit_mode,
                key=f"camera_angle_{prompt['id']}"
            )
        
        with col2:
            edited_data['environment'] = st.text_input(
                "Environment", 
                value=prompt.get('environment', ''), 
                disabled=not edit_mode,
                key=f"environment_{prompt['id']}"
            )
            edited_data['lighting'] = st.text_input(
                "Lighting", 
                value=prompt.get('lighting', ''), 
                disabled=not edit_mode,
                key=f"lighting_{prompt['id']}"
            )
            edited_data['focus'] = st.text_input(
                "Focus", 
                value=prompt.get('focus', ''), 
                disabled=not edit_mode,
                key=f"focus_{prompt['id']}"
            )
            edited_data['color_palette'] = st.text_input(
                "Color Palette", 
                value=prompt.get('color_palette', ''), 
                disabled=not edit_mode,
                key=f"color_palette_{prompt['id']}"
            )
            edited_data['composition'] = st.text_input(
                "Composition", 
                value=prompt.get('composition', ''), 
                disabled=not edit_mode,
                key=f"composition_{prompt['id']}"
            )
        
        edited_data['modifiers'] = st.text_area(
            "Modifiers", 
            value=prompt.get('modifiers', ''), 
            disabled=not edit_mode,
            key=f"modifiers_{prompt['id']}",
            height=80
        )
        edited_data['generated_prompt'] = st.text_area(
            "Generated Prompt", 
            value=prompt.get('generated_prompt', ''), 
            disabled=not edit_mode,
            key=f"generated_prompt_{prompt['id']}",
            height=150
        )
        
        # Save button (only shown in edit mode)
        if edit_mode:
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Save Changes", type="primary", key=f"save_{prompt['id']}"):
                    try:
                        # Update the prompt
                        if data_manager.update_prompt(prompt['id'], edited_data):
                            st.success("✅ Prompt updated successfully!")
                            st.session_state[f"edit_mode_{prompt['id']}"] = False
                            st.rerun()
                        else:
                            st.error("Failed to update prompt")
                    except Exception as e:
                        st.error(f"Error updating prompt: {str(e)}")
            
            with col2:
                if st.button("❌ Cancel", key=f"cancel_{prompt['id']}"):
                    st.session_state[f"edit_mode_{prompt['id']}"] = False
                    st.rerun()

def image_analysis_tab():
    """Tab for analyzing images and generating prompts"""
    st.markdown("""
        <h1 class="page-header">Image Analysis & Prompt Generation</h1>
        <p class="page-subtitle">Upload an image to analyze and generate a Flux prompt from it</p>
    """, unsafe_allow_html=True)
    
    analyzer = st.session_state.image_analyzer
    data_manager = st.session_state.data_manager
    
    # Layout: Left side for controls, right side for preview
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        # Image upload section
        st.markdown("""
            <div class="image-upload-section">
                <h3 class="section-title-small">Choose an image file <span class="help-icon">?</span></h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Image upload - Streamlit native uploader with custom styling
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
            help="Upload an image to analyze and generate a prompt from",
            key="image_analysis_uploader"
        )
    
        # Analysis type section
        st.markdown("""
            <h3 class="section-title-small">Analysis Type <span class="help-icon">?</span></h3>
        """, unsafe_allow_html=True)
        
        analysis_types = analyzer.get_analysis_types()
        analysis_type = st.selectbox(
            "Analysis Type",
            options=list(analysis_types.keys()),
            format_func=lambda x: f"{x.title()} - {analysis_types[x]}",
            help="Choose the type of analysis to perform",
            label_visibility="collapsed"
        )
        
        # Analysis type list display
        st.markdown('<ul class="analysis-type-list">', unsafe_allow_html=True)
        for atype, desc in analysis_types.items():
            is_selected = "selected" if analysis_type == atype else ""
            st.markdown(f'<li class="analysis-type-item {is_selected}"><strong>{atype.title()}</strong> - {desc}</li>', unsafe_allow_html=True)
        st.markdown('</ul>', unsafe_allow_html=True)
        
        # Analyze button - Match sidebar active color
        analyze_clicked = st.button("🔍 Analyze image", type="primary", use_container_width=True)
        st.markdown("""
            <style>
                div[data-testid="column"]:nth-child(1) button[kind="primary"] {
                    background: rgb(17, 130, 221) !important;
                    color: #FFFFFF !important;
                    font-weight: 700 !important;
                }
                div[data-testid="column"]:nth-child(1) button[kind="primary"]:hover {
                    background: rgb(25, 140, 230) !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Instructions section
        st.markdown("""
            <div class="instructions-section">
                <h3 class="instructions-title">How to Use Image Analysis</h3>
                <ul class="instructions-list">
                    <li><strong>Upload an Image:</strong> Choose any image file (PNG, JPG, etc.)</li>
                    <li><strong>Select Analysis Type:</strong>
                        <ul style="margin-left: 20px; margin-top: 10px;">
                            <li><strong>Detailed:</strong> Comprehensive analysis - structured data</li>
                            <li><strong>Artistic:</strong> Focus on artistic style and visual qualities</li>
                            <li><strong>Technical:</strong> Aspects like composition and lighting</li>
                            <li><strong>Simple:</strong> Basic description of main elements</li>
                        </ul>
                    </li>
                    <li><strong>Analyze:</strong> Click the analyze button to process the image</li>
                    <li><strong>Review Results:</strong> Check the generated description and prompt</li>
                    <li><strong>Save:</strong> Save the analysis as a new prompt for future use</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        if uploaded_file is not None:
            # Display the uploaded image in preview
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # MB
            st.markdown(f"""
                <div class="image-preview-container">
                    <div class="image-info">{uploaded_file.name} {file_size:.1f}MB</div>
            """, unsafe_allow_html=True)
            
            st.image(uploaded_file, use_container_width=True)
            
            # Get image dimensions if possible
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(uploaded_file.getvalue()))
                width, height = img.size
                st.markdown(f'<div class="image-dimensions">{width} x {height}</div>', unsafe_allow_html=True)
            except:
                pass
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis processing
    if uploaded_file is not None and analyze_clicked:
        with st.spinner("Analyzing image..."):
            try:
                # Convert uploaded file to PIL Image
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(uploaded_file.getvalue()))
                
                # Perform analysis
                analysis_result = analyzer.analyze_image(image, analysis_type)
                
                if "error" in analysis_result:
                    st.error(analysis_result["error"])
                else:
                    # Display results
                    st.success("✅ Analysis complete!")
                    
                    # Show analysis results in left column
                    with col_left:
                        if analysis_type == "detailed" and "subject" in analysis_result:

                            # Structured analysis
                            st.subheader("📊 Analysis Results")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.text_input("Subject", value=analysis_result.get("subject", ""), disabled=True)
                                st.text_input("Image Style", value=analysis_result.get("art_style", ""), disabled=True)
                                st.text_input("Camera Angle", value=analysis_result.get("camera_angle", ""), disabled=True)
                                st.text_input("Environment", value=analysis_result.get("environment", ""), disabled=True)
                                st.text_input("Lighting", value=analysis_result.get("lighting", ""), disabled=True)
                            
                            with col2:
                                st.text_input("Focus", value=analysis_result.get("focus", ""), disabled=True)
                                st.text_input("Color Palette", value=analysis_result.get("color_palette", ""), disabled=True)
                                st.text_input("Composition", value=analysis_result.get("composition", ""), disabled=True)
                                st.text_area("Modifiers", value=analysis_result.get("modifiers", ""), disabled=True)
                            
                            # Generated prompt
                            suggested_prompt = analysis_result.get("suggested_prompt", "")
                            st.text_area("Generated Prompt", value=suggested_prompt, height=150, disabled=True)
                            
                            # Send to Generate Prompt button
                            subject_text = analysis_result.get("subject", "") or suggested_prompt
                            if st.button("Send to Generate Prompt", key="send_to_generate_prompt_detailed"):
                                st.session_state["param_context"] = subject_text
                                st.success("Sent to Generate Prompt! Switch to the 'Generate Prompt' tab to continue.")
                            
                            # Copy to clipboard button for generated prompt
                            if suggested_prompt:
                                components.html(
                                    f"""
                                    <div>
                                      <button style=\"padding:8px 12px; margin-top:6px;\" onclick=\"navigator.clipboard.writeText(text_{id(suggested_prompt)}).then(()=>{{{{this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy Generated Prompt',1500)}}}});\">Copy Generated Prompt</button>
                                      <script>
                                        const text_{id(suggested_prompt)} = {json.dumps(suggested_prompt)};
                                      </script>
                                    </div>
                                    """,
                                    height=60,
                                )
                            
                            # Store for saving
                            st.session_state.analysis_result = analysis_result
                            
                            # Always show save button if analysis result exists
                            if 'analysis_result' in st.session_state:
                                save_clicked = st.button("💾 Save Analysis as Prompt", key="detailed_save")
                                if save_clicked:


                                    st.write(f"Analysis result in session state: {'analysis_result' in st.session_state}")
                                    if 'analysis_result' in st.session_state:

                                        st.write(f"Analysis result keys: {list(st.session_state.analysis_result.keys()) if isinstance(st.session_state.analysis_result, dict) else 'Not a dict'}")
                                        
                                        if 'analysis_result' in st.session_state:
                                            try:
                                                result = st.session_state.analysis_result
                                                
                                                # Prepare data for saving
                                                save_data = {
                                                    'context': result.get('subject', ''),
                                                    'art_style': result.get('art_style', ''),
                                                    'camera_angle': result.get('camera_angle', ''),
                                                    'environment': result.get('environment', ''),
                                                    'lighting': result.get('lighting', ''),
                                                    'focus': result.get('focus', ''),
                                                    'color_palette': result.get('color_palette', ''),
                                                    'composition': result.get('composition', ''),
                                                    'modifiers': result.get('modifiers', ''),
                                                    'generated_prompt': result.get('suggested_prompt', '')
                                                }
                                                
                                                # Save to CSV
                                                prompt_id = data_manager.save_prompt(save_data)
                                                st.success(f"✅ Analysis saved as prompt with ID: {prompt_id}")
                                                logger.info(f"Image analysis saved as prompt with ID: {prompt_id}")
                                                
                                            except Exception as e:
                                                st.error(f"Error saving analysis: {str(e)}")
                                        else:
                                            st.warning("Please analyze an image first")
                            
                        else:
                            # Text analysis
                            st.subheader("📝 Analysis Description")
                            st.text_area("Description", value=analysis_result.get("description", ""), height=200, disabled=True)
                            
                            st.subheader("🎯 Suggested Prompt")
                            suggested_prompt = analysis_result.get("suggested_prompt", "")
                            st.text_area("Generated Prompt", value=suggested_prompt, height=150, disabled=True)
                            
                            # Send to Generate Prompt button (text/simple analysis)
                            text_context = analysis_result.get("description", "") or suggested_prompt
                            if st.button("Send to Generate Prompt", key="send_to_generate_prompt_text"):
                                st.session_state["param_context"] = text_context
                                st.success("Sent to Generate Prompt! Switch to the 'Generate Prompt' tab to continue.")

                            # Copy to clipboard button for generated prompt (text analysis)
                            if suggested_prompt:
                                components.html(
                                    f"""
                                    <div>
                                      <button style=\"padding:8px 12px; margin-top:6px;\" onclick=\"navigator.clipboard.writeText(text_{id(suggested_prompt)}).then(()=>{{{{this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy Generated Prompt',1500)}}}});\">Copy Generated Prompt</button>
                                      <script>
                                        const text_{id(suggested_prompt)} = {json.dumps(suggested_prompt)};
                                      </script>
                                    </div>
                                    """,
                                    height=60,
                                )

                            # Store for saving
                            st.session_state.analysis_result = analysis_result
                            
                            # Save prompt button for text analysis
                            if st.button("💾 Save Analysis as Prompt"):


                                st.write(f"Analysis result in session state: {'analysis_result' in st.session_state}")
                                if 'analysis_result' in st.session_state:

                                    st.write(f"Analysis result keys: {list(st.session_state.analysis_result.keys()) if isinstance(st.session_state.analysis_result, dict) else 'Not a dict'}")
                                else:

                                    st.warning("No analysis result found. Please analyze an image first.")
                                    return
                                
                                if 'analysis_result' in st.session_state:
                                    try:
                                        result = st.session_state.analysis_result
                                        
                                        # Prepare data for saving
                                        save_data = {
                                            'context': 'Image Analysis',
                                            'art_style': '',
                                            'camera_angle': '',
                                            'environment': '',
                                            'lighting': '',
                                            'focus': '',
                                            'color_palette': '',
                                            'composition': '',
                                            'modifiers': result.get('description', ''),
                                            'generated_prompt': result.get('suggested_prompt', '')
                                        }
                                        
                                        # Save to CSV
                                        prompt_id = data_manager.save_prompt(save_data)
                                        st.success(f"✅ Analysis saved as prompt with ID: {prompt_id}")
                                        logger.info(f"Image analysis saved as prompt with ID: {prompt_id}")
                                        
                                    except Exception as e:
                                        st.error(f"Error saving analysis: {str(e)}")
                                else:
                                    st.warning("Please analyze an image first")
                    
            except Exception as e:
                st.error(f"Error analyzing image: {str(e)}")
                logger.error(f"Image analysis error: {str(e)}")

def generate_images_tab():
    """Tab for generating images from prompts"""
    st.markdown("""
        <h1 class="page-header">Generate Images</h1>
        <p class="page-subtitle">Generate images from your Flux prompts using AI</p>
    """, unsafe_allow_html=True)
    
    # Check if image generator is available
    if 'image_generator' not in st.session_state:
        st.warning("Image generation is not available. Please check your API keys in the .env file.")
        st.info("Required: OPENAI_API_KEY and BLACK_FOREST_LABS_API_KEY")
        return
    
    generator = st.session_state.image_generator
    
    # Check if ComfyUI should be available but isn't in providers
    # This handles the case where ComfyUI started after the app
    providers = generator.get_available_providers()
    if "comfyui" not in providers:
        try:
            from image_provider_router import ImageProviderRouter
            config = Config()
            test_router = ImageProviderRouter(config)
            test_providers = test_router.get_available_providers()
            if "comfyui" in test_providers:
                # ComfyUI is now available, refresh the generator
                # Clear old instance first
                if 'image_generator' in st.session_state:
                    del st.session_state.image_generator
                # Create fresh instance
                st.session_state.image_generator = ImageGenerator()
                generator = st.session_state.image_generator
                providers = generator.get_available_providers()
                logger.info(f"Auto-refreshed ImageGenerator. Providers now: {list(providers.keys())}")
                # Show success message
                st.success("✓ ComfyUI detected! Providers updated.")
                st.rerun()
        except Exception as e:
            logger.debug(f"Provider refresh check in tab failed: {e}")
    
    # Two-column layout
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        st.markdown("""
            <h3 class="section-title-small">Prompt & Settings</h3>
        """, unsafe_allow_html=True)
        
        # Prompt input
        prompt = st.text_area(
            "Enter your prompt",
            height=150,
            placeholder="A cinematic sunset over mountains, dramatic lighting, photorealistic",
            help="Enter a detailed prompt for image generation"
        )
        
        # Load prompt from repository (if available)
        if st.session_state.get('prompt_repository'):
            repository = st.session_state.prompt_repository
            master_prompts = repository.get_all_master_prompts()
            if master_prompts:
                st.markdown("**Or select from saved prompts:**")
                prompt_options = ["None"] + [p['name'] for p in master_prompts]
                selected_prompt = st.selectbox("Load saved prompt", prompt_options)
                if selected_prompt != "None":
                    selected_prompt_data = next((p for p in master_prompts if p['name'] == selected_prompt), None)
                    if selected_prompt_data:
                        prompt = selected_prompt_data.get('content', prompt)
                        st.text_area("Loaded prompt", value=prompt, height=100, disabled=True, key="loaded_prompt_display")
        
        # Style selection
        st.markdown("""
            <h3 class="section-title-small">Image Style</h3>
        """, unsafe_allow_html=True)
        
        style_options = {
            "fast_draft": "Fast Draft - Quick, lower quality",
            "photoreal": "Photorealistic - High quality realistic images",
            "brand_layout": "Brand Layout - Marketing visuals",
            "portrait": "Portrait - Professional portraits",
            "product": "Product - Product photography",
            "logo_text": "Logo/Text - Logos and text-based images",
            "artistic": "Artistic - Creative styles",
            "cinematic": "Cinematic - Film-quality images"
        }
        
        selected_style = st.selectbox(
            "Select image style",
            options=list(style_options.keys()),
            format_func=lambda x: style_options[x],
            help="Choose the style that best matches your needs"
        )
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                width = st.selectbox(
                    "Width",
                    options=[512, 768, 1024, 1280, 1536],
                    index=2,
                    help="Image width in pixels"
                )
                seed = st.number_input(
                    "Seed (for reproducibility)",
                    min_value=None,
                    max_value=None,
                    value=None,
                    help="Optional: Set a seed for reproducible results",
                    key="image_seed"
                )
            
            with col2:
                height = st.selectbox(
                    "Height",
                    options=[512, 768, 1024, 1280, 1536],
                    index=2,
                    help="Image height in pixels"
                )
                negative_prompt = st.text_area(
                    "Negative Prompt",
                    height=80,
                    placeholder="blurry, low quality, distorted",
                    help="What to avoid in the image"
                )
        
        # Provider selection
        st.markdown("---")
        
        # Add refresh button for providers
        col_refresh, col_provider_label = st.columns([1, 4])
        with col_refresh:
            refresh_clicked = st.button("🔄 Refresh Providers", help="Refresh provider list to detect ComfyUI if it just started", key="refresh_providers_btn")
            if refresh_clicked:
                # Force clear and reinitialize ImageGenerator
                try:
                    # Clear the cached generator
                    if 'image_generator' in st.session_state:
                        del st.session_state.image_generator
                    # Create fresh instance
                    st.session_state.image_generator = ImageGenerator()
                    generator = st.session_state.image_generator
                    # Verify ComfyUI is now available
                    new_providers = generator.get_available_providers()
                    if "comfyui" in new_providers:
                        st.success(f"✓ Providers refreshed! ComfyUI is now available.")
                    else:
                        st.warning("Providers refreshed, but ComfyUI not detected. Make sure ComfyUI is running.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to refresh: {e}")
                    logger.error(f"Provider refresh error: {e}", exc_info=True)
        
        with col_provider_label:
            st.markdown("**Provider**")
        
        # Get providers (may have been refreshed above or in the check at top of function)
        providers = generator.get_available_providers()
        
        # Debug: Log available providers
        logger.info(f"Available providers in UI: {list(providers.keys())}")
        
        if providers:
            provider_names = list(providers.keys())
            provider_options = {}
            for name, info in providers.items():
                # Better display names
                if name == "comfyui":
                    display_name = f"ComfyUI (SDXL - Local)"
                elif name == "flux":
                    display_name = f"FLUX ({info['model']})"
                elif name == "openai":
                    display_name = f"OpenAI (DALL-E 3)"
                else:
                    display_name = f"{name.upper()} ({info['model']})"
                provider_options[name] = display_name
            
            # Check for ComfyUI status
            comfyui_available = "comfyui" in providers
            comfyui_status = ""
            
            # Only check server status if ComfyUI is not in providers
            # This prevents showing warning when ComfyUI is actually available
            if not comfyui_available:
                # Try to check if ComfyUI server might be available but not initialized
                try:
                    config = Config()
                    comfyui_server = config.get_comfyui_server_address()
                    import urllib.request
                    import urllib.error
                    try:
                        # Use longer timeout and better error handling
                        urllib.request.urlopen(f"http://{comfyui_server}/system_stats", timeout=5)
                        # Server is reachable but provider not initialized - suggest refresh
                        comfyui_status = f"⚠️ ComfyUI server at {comfyui_server} is reachable but not initialized. Click '🔄 Refresh Providers' button above."
                    except urllib.error.URLError:
                        # Server not reachable
                        comfyui_status = f"ℹ️ ComfyUI server at {comfyui_server} not reachable. Start ComfyUI to enable local generation."
                    except Exception:
                        # Other errors - don't show confusing message
                        pass
                except Exception:
                    pass
            else:
                # ComfyUI is available - clear any previous status
                comfyui_status = ""
            
            # Default to "auto" for automatic selection
            provider_options = {"auto": "Auto (Best for style)"} | provider_options
            
            selected_provider = st.selectbox(
                "Provider",
                options=list(provider_options.keys()),
                format_func=lambda x: provider_options[x],
                help="Choose a specific provider or 'Auto' to let the system select the best one for your style",
                key="image_provider_select"
            )
            
            # Show provider info
            if selected_provider != "auto" and selected_provider in providers:
                provider_info = providers[selected_provider]
                features = provider_info.get('features', {})
                feature_list = [f for f, enabled in features.items() if enabled]
                if feature_list:
                    st.caption(f"Features: {', '.join(feature_list)}")
            
            # Show ComfyUI status if not available
            # Only show if status message exists AND ComfyUI is not in providers
            if comfyui_status and not comfyui_available:
                st.info(comfyui_status)
            elif comfyui_available:
                # ComfyUI is available - optionally show success message (commented out to reduce clutter)
                # st.success("✓ ComfyUI is available for local generation")
                pass
        else:
            selected_provider = "auto"
            st.warning("No providers available. Please check your API keys.")
        
        # Generate button
        generate_button = st.button("🎨 Generate Image", type="primary", use_container_width=True)
    
    with col_right:
        st.markdown("""
            <h3 class="section-title-small">Preview</h3>
        """, unsafe_allow_html=True)
        
        # Display generated image
        if generate_button and prompt:
            with st.spinner("Generating image... This may take 30-60 seconds."):
                try:
                    # Convert style string to enum
                    style_enum = ImageStyle(selected_style) if selected_style in [s.value for s in ImageStyle] else None
                    
                    # Use selected provider if not "auto"
                    provider_override = None if selected_provider == "auto" else selected_provider
                    
                    result = generator.generate(
                        prompt=prompt,
                        style=style_enum,
                        width=width,
                        height=height,
                        seed=int(seed) if seed else None,
                        negative_prompt=negative_prompt if negative_prompt else None,
                        num_images=1,
                        provider=provider_override
                    )
                    
                    if result.success:
                        st.success(f"✓ Generated using {result.provider} ({result.model})")
                        
                        # Display image - handle both URLs and binary data
                        image_url = result.get_image_url(0)
                        image_bytes = result.get_image_bytes(0)
                        
                        if image_bytes:
                            # Handle binary image data (e.g., from ComfyUI)
                            from PIL import Image as PILImage
                            import io
                            img = PILImage.open(io.BytesIO(image_bytes))
                            st.image(img, caption=f"Generated Image - {selected_style}", use_container_width=True)
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Image",
                                data=image_bytes,
                                file_name=f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png"
                            )
                        elif image_url:
                            # Handle URL-based images (e.g., from OpenAI, Flux API)
                            st.image(image_url, caption=f"Generated Image - {selected_style}", use_container_width=True)
                            
                            # Download button
                            try:
                                import requests
                                img_response = requests.get(image_url)
                                st.download_button(
                                    label="📥 Download Image",
                                    data=img_response.content,
                                    file_name=f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                    mime="image/png"
                                )
                            except Exception as e:
                                logger.warning(f"Could not download image: {e}")
                                st.info(f"Image URL: {image_url}")
                        else:
                            st.warning("Image generated but no image data available. Check metadata.")
                        
                        # Save to session state
                        st.session_state.last_generated_image = result
                        
                    else:
                        st.error(f"Generation failed: {result.error}")
                        if "No available" in result.error:
                            st.info("Make sure you have configured your API keys in the .env file")
                
                except Exception as e:
                    st.error(f"Error generating image: {str(e)}")
                    logger.error(f"Image generation error: {e}", exc_info=True)
        
        elif generate_button and not prompt:
            st.warning("Please enter a prompt first")
        
        else:
            # Show instructions when no generation yet
            st.info("""
            **Instructions:**
            1. Enter your prompt in the left panel
            2. Select an image style
            3. Adjust settings (optional)
            4. Click "Generate Image"
            
            **Tip:** You can load prompts from your Prompt Repository!
            """)
    
    # Show last generated image info
    if 'last_generated_image' in st.session_state:
        result = st.session_state.last_generated_image
        st.markdown("---")
        with st.expander("Last Generated Image Details"):
            st.json({
                "provider": result.provider,
                "model": result.model,
                "metadata": result.metadata
            })

def image_editing_tab():
    """Tab for image-to-image editing"""
    st.markdown("""
        <h1 class="page-header">Image Editing</h1>
        <p class="page-subtitle">Transform and edit images using AI image-to-image generation</p>
    """, unsafe_allow_html=True)
    
    # Check if image generator is available
    if 'image_generator' not in st.session_state:
        st.warning("Image editing is not available. Please check your API keys in the .env file.")
        st.info("Required: OPENAI_API_KEY and BLACK_FOREST_LABS_API_KEY (for img2img)")
        return
    
    generator = st.session_state.image_generator
    
    # Check if Flux provider supports img2img
    providers = generator.get_available_providers()
    flux_available = False
    for name, info in providers.items():
        if "flux" in name.lower() and info['features'].get('img2img', False):
            flux_available = True
            break
    
    if not flux_available:
        st.error("Image-to-image editing requires Flux provider with img2img support.")
        st.info("Make sure you have BLACK_FOREST_LABS_API_KEY configured in your .env file.")
        return
    
    # Three-column layout: Input | Controls | Output
    col_input, col_controls, col_output = st.columns([1, 1, 1])
    
    with col_input:
        st.markdown("""
            <h3 class="section-title-small">Source Image</h3>
        """, unsafe_allow_html=True)
        
        # Image upload
        uploaded_file = st.file_uploader(
            "Upload image to edit",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
            help="Upload the image you want to edit/transform",
            key="img2img_uploader"
        )
        
        source_image = None
        source_image_url = None
        
        if uploaded_file is not None:
            # Display uploaded image
            from PIL import Image as PILImage
            import io
            import base64
            
            source_image = PILImage.open(uploaded_file)
            st.image(source_image, caption="Source Image", use_container_width=True)
            
            # Convert to base64 data URL for API
            buffered = io.BytesIO()
            # Save in original format or PNG
            format_ext = uploaded_file.type.split('/')[-1].upper()
            if format_ext == 'JPEG':
                format_ext = 'JPEG'
            else:
                format_ext = 'PNG'
            source_image.save(buffered, format=format_ext)
            img_bytes = buffered.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            source_image_url = f"data:image/{format_ext.lower()};base64,{img_base64}"
            
            # Show image info
            st.caption(f"Size: {source_image.size[0]}x{source_image.size[1]} pixels")
    
    with col_controls:
        st.markdown("""
            <h3 class="section-title-small">Edit Settings</h3>
        """, unsafe_allow_html=True)
        
        # Prompt input
        prompt = st.text_area(
            "Edit Prompt",
            height=120,
            placeholder="Make this more cinematic, add dramatic lighting, change the mood to mysterious",
            help="Describe how you want to transform the image"
        )
        
        # Strength slider
        strength = st.slider(
            "Transformation Strength",
            min_value=0.1,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="How much to change the image (0.1 = subtle, 1.0 = major transformation)"
        )
        st.caption(f"Strength: {int(strength * 100)}% - {'Subtle changes' if strength < 0.5 else 'Moderate changes' if strength < 0.8 else 'Major transformation'}")
        
        # Style selection (optional)
        st.markdown("""
            <h3 class="section-title-small">Style (Optional)</h3>
        """, unsafe_allow_html=True)
        
        style_options = {
            "None": "No style override",
            "photoreal": "Photorealistic",
            "cinematic": "Cinematic",
            "artistic": "Artistic",
        }
        
        selected_style = st.selectbox(
            "Apply style",
            options=list(style_options.keys()),
            format_func=lambda x: style_options[x],
            help="Optional: Apply a specific style to the transformation"
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            seed = st.number_input(
                "Seed (for reproducibility)",
                min_value=None,
                max_value=None,
                value=None,
                help="Optional: Set a seed for reproducible results",
                key="img2img_seed"
            )
            negative_prompt = st.text_area(
                "Negative Prompt",
                height=60,
                placeholder="blurry, distorted, low quality",
                help="What to avoid in the edited image"
            )
        
        # Generate button
        generate_button = st.button("🖼️ Generate Edited Image", type="primary", use_container_width=True)
    
    with col_output:
        st.markdown("""
            <h3 class="section-title-small">Edited Image</h3>
        """, unsafe_allow_html=True)
        
        # Display result
        if generate_button:
            if not uploaded_file:
                st.warning("⚠ Please upload an image first")
            elif not prompt:
                st.warning("⚠ Please enter an edit prompt")
            elif not source_image_url:
                st.warning("⚠ Could not process uploaded image")
            else:
                with st.spinner("Editing image... This may take 30-60 seconds."):
                    try:
                        # Convert style string to enum
                        style_enum = None
                        if selected_style != "None":
                            try:
                                style_enum = ImageStyle(selected_style)
                            except ValueError:
                                pass
                        
                        # Generate edited image using img2img with Flux Kontext
                        # The router will automatically use Flux Kontext from routing config
                        result = generator.generate(
                            prompt=prompt,
                            style=style_enum,
                            source_image_url=source_image_url,
                            strength=strength,
                            seed=int(seed) if seed else None,
                            negative_prompt=negative_prompt if negative_prompt else None,
                            num_images=1,
                            use_cache=False  # Don't cache img2img results
                        )
                        
                        if result.success:
                            st.success(f"✓ Generated using {result.provider} ({result.model})")
                            
                            # Display edited image
                            image_url = result.get_image_url(0)
                            if image_url:
                                st.image(image_url, caption="Edited Image", use_container_width=True)
                                
                                # Before/After comparison
                                if source_image:
                                    st.markdown("**Before / After Comparison**")
                                    col_before, col_after = st.columns(2)
                                    with col_before:
                                        st.caption("**Before**")
                                        st.image(source_image, use_container_width=True)
                                    with col_after:
                                        st.caption("**After**")
                                        st.image(image_url, use_container_width=True)
                                
                                # Download button
                                try:
                                    import requests
                                    img_response = requests.get(image_url)
                                    st.download_button(
                                        label="📥 Download Edited Image",
                                        data=img_response.content,
                                        file_name=f"edited_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                        mime="image/png",
                                        use_container_width=True
                                    )
                                except Exception as e:
                                    logger.warning(f"Could not download image: {e}")
                                    st.info(f"Image URL: {image_url}")
                            else:
                                st.warning("Image generated but URL not available. Check metadata.")
                            
                            # Save to session state
                            st.session_state.last_edited_image = result
                        
                        else:
                            st.error(f"Editing failed: {result.error}")
                            if "img2img" in result.error.lower() or "not support" in result.error.lower():
                                st.info("💡 Tip: Make sure you're using Flux provider (Black Forest Labs API) as it supports image-to-image editing.")
                    
                    except Exception as e:
                        st.error(f"Error editing image: {str(e)}")
                        logger.error(f"Image editing error: {e}", exc_info=True)
        
        else:
            # Show instructions when no generation yet
            st.info("""
            **Instructions:**
            1. Upload an image in the left panel
            2. Enter a prompt describing the changes
            3. Adjust the strength slider
            4. Click "Generate Edited Image"
            
            **Tips:**
            - Lower strength = subtle changes
            - Higher strength = major transformation
            - Use negative prompts to avoid unwanted changes
            """)

def image_vault_tab():
    """Tab for viewing and managing saved images in the vault"""
    st.markdown("""
        <h1 class="page-header">Image Vault</h1>
        <p class="page-subtitle">Browse and manage all your generated and edited images</p>
    """, unsafe_allow_html=True)
    
    # Check if image generator and vault are available
    if 'image_generator' not in st.session_state:
        st.warning("Image Vault is not available. Please initialize the image generator first.")
        return
    
    generator = st.session_state.image_generator
    if not generator.vault:
        st.warning("Image Vault is not initialized. Images will not be automatically saved.")
        return
    
    vault = generator.vault
    
    # Stats section
    stats = vault.get_vault_stats()
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total Images", stats["total_images"])
    with col_stat2:
        st.metric("Total Size", f"{stats['total_size_mb']} MB")
    with col_stat3:
        generated_count = stats["by_source_type"].get("generated", 0)
        st.metric("Generated", generated_count)
    with col_stat4:
        edited_count = stats["by_source_type"].get("edited", 0)
        st.metric("Edited", edited_count)
    
    # Filters
    st.markdown("---")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        filter_source = st.selectbox(
            "Filter by Type",
            options=["All", "Generated", "Edited"],
            help="Filter images by source type"
        )
    
    with col_filter2:
        providers_list = ["All"] + list(set(stats["by_provider"].keys()))
        filter_provider = st.selectbox(
            "Filter by Provider",
            options=providers_list if providers_list else ["All"],
            help="Filter images by provider"
        )
    
    with col_filter3:
        styles_list = ["All"] + [s for s in stats["by_style"].keys() if s != "none"]
        filter_style = st.selectbox(
            "Filter by Style",
            options=styles_list if styles_list else ["All"],
            help="Filter images by style"
        )
    
    # Apply filters
    source_type_filter = filter_source.lower() if filter_source != "All" else None
    provider_filter = filter_provider if filter_provider != "All" else None
    style_filter = filter_style if filter_style != "All" else None
    
    # Get filtered images
    images = vault.list_images(
        source_type=source_type_filter,
        provider=provider_filter,
        style=style_filter,
        limit=None,
        sort_by="timestamp",
        reverse=True
    )
    
    if not images:
        st.info("No images found in vault. Generated images will be automatically saved here.")
        return
    
    # Display images in grid
    st.markdown(f"### Showing {len(images)} image(s)")
    
    # Create grid layout - 3 columns
    num_cols = 3
    cols = st.columns(num_cols)
    
    for idx, img_meta in enumerate(images):
        col_idx = idx % num_cols
        with cols[col_idx]:
            try:
                image_path = vault.get_image_path(img_meta["id"])
                
                if image_path and image_path.exists():
                    # Display image
                    st.image(str(image_path), use_container_width=True)
                    
                    # Image info
                    source_type_label = "✏️" if img_meta.get("source_type") == "edited" else "🎨"
                    st.caption(f"{source_type_label} {img_meta.get('provider', 'unknown').upper()} | {img_meta.get('date', '')}")
                    
                    # Truncated prompt
                    prompt_preview = img_meta.get("prompt", "")[:60]
                    if len(img_meta.get("prompt", "")) > 60:
                        prompt_preview += "..."
                    st.caption(f"*{prompt_preview}*")
                    
                    # Expandable details
                    with st.expander("Details"):
                        st.write(f"**ID:** {img_meta['id']}")
                        st.write(f"**Provider:** {img_meta.get('provider', 'N/A')}")
                        st.write(f"**Model:** {img_meta.get('model', 'N/A')}")
                        st.write(f"**Style:** {img_meta.get('style', 'N/A')}")
                        st.write(f"**Date:** {img_meta.get('date', 'N/A')} {img_meta.get('time', '')}")
                        st.write(f"**Prompt:** {img_meta.get('prompt', 'N/A')}")
                        
                        # Download and delete buttons
                        col_download, col_delete = st.columns(2)
                        with col_download:
                            try:
                                with open(image_path, 'rb') as f:
                                    st.download_button(
                                        "📥 Download",
                                        data=f.read(),
                                        file_name=img_meta["filename"],
                                        mime="image/png",
                                        key=f"download_{img_meta['id']}",
                                        use_container_width=True
                                    )
                            except Exception:
                                pass
                        
                        with col_delete:
                            if st.button("🗑️ Delete", key=f"delete_{img_meta['id']}", use_container_width=True):
                                if vault.delete_image(img_meta['id']):
                                    st.success("Image deleted")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete image")
                
                else:
                    st.warning(f"Image file not found: {img_meta.get('filename', 'N/A')}")
            
            except Exception as e:
                st.error(f"Error loading image: {e}")
                logger.error(f"Error displaying vault image: {e}")
    
    # Show more if there are many images
    if len(images) > 9:
        st.info(f"Showing first 9 images. Total: {len(images)}. Use filters to narrow down results.")

def prompt_repository_tab():
    """Tab for managing the prompt repository"""
    st.markdown("""
        <h1 class="page-header">Prompt Repository</h1>
        <p class="page-subtitle">Manage master prompts and knowledge base for enhanced prompt generation</p>
    """, unsafe_allow_html=True)
    
    repository = st.session_state.prompt_repository
    
    # Repository summary
    summary = repository.get_repository_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Master Prompts", summary['total_master_prompts'])
    with col2:
        st.metric("Knowledge Items", summary['total_knowledge_items'])
    with col3:
        st.metric("Categories", len(summary['categories']['knowledge_base']))
    with col4:
        if summary['most_used_prompt']:
            st.metric("Most Used", summary['most_used_prompt']['name'][:20] + "...")
    
    # Tabs for different repository functions
    repo_tab1, repo_tab2, repo_tab3 = st.tabs(["Master Prompts", "Knowledge Base", "Search & Export"])
    
    with repo_tab1:
        st.subheader("🎯 Master Prompts")
        
        # Display existing master prompts
        master_prompts = repository.get_all_master_prompts()
        
        if master_prompts:
            for prompt in master_prompts:
                with st.expander(f"{prompt['name']} ({prompt['category']})"):
                    st.text_area("Content", value=prompt['content'], height=200, disabled=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.text(f"Usage Count: {prompt.get('usage_count', 0)}")
                    with col2:
                        st.text(f"Created: {prompt['created'][:10]}")
                    with col3:
                        if prompt.get('last_used'):
                            st.text(f"Last Used: {prompt['last_used'][:10]}")
        else:
            st.info("No master prompts found. Run the setup script to initialize the repository.")
        
        # Add new master prompt
        st.subheader("➕ Add New Master Prompt")
        with st.form("add_master_prompt"):
            name = st.text_input("Prompt Name")
            category = st.selectbox("Category", ["flux_master", "general", "technical", "artistic"])
            description = st.text_area("Description")
            content = st.text_area("Master Prompt Content", height=200)
            
            if st.form_submit_button("Add Master Prompt"):
                if name and content:
                    try:
                        prompt_id = repository.add_master_prompt(name, content, category, description)
                        st.success(f"✅ Master prompt added with ID: {prompt_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding master prompt: {str(e)}")
                else:
                    st.warning("Please fill in name and content")
    
    # (Removed duplicate tab header)
    with repo_tab2:
        st.subheader("Knowledge Base")

        # Display knowledge base by category
        knowledge_base = repository.get_knowledge_base()

        for category, items in knowledge_base.items():
            if items:
                with st.expander(f"{category.replace('_', ' ').title()} ({len(items)} items)"):
                    for item in items[:10]:  # Show first 10 items
                        st.text(f"- {item['item']}")
                    if len(items) > 10:
                        st.text(f"... and {len(items) - 10} more items")

        # Add new knowledge item
        st.subheader("Add Knowledge Item")
        with st.form("add_knowledge_item"):
            category = st.selectbox("Category", list(knowledge_base.keys()))
            item = st.text_input("Item")
            description = st.text_input("Description")

            if st.form_submit_button("Add Item"):
                if item:
                    try:
                        repository.add_knowledge_item(category, item, description)
                        st.success("Knowledge item added")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding item: {str(e)}")
                else:
                    st.warning("Please enter an item")

    with repo_tab3:
        st.subheader("Search Knowledge Base")

        search_term = st.text_input("Search for knowledge items", placeholder="Enter search term...")

        if search_term:
            results = repository.search_knowledge_base(search_term)

            if results:
                st.success(f"Found {sum(len(items) for items in results.values())} matching items")

                for category, items in results.items():
                    if items:
                        with st.expander(f"{category.replace('_', ' ').title()} ({len(items)} matches)"):
                            for item in items:
                                st.text(f"- {item['item']}")
                                if item.get('description'):
                                    st.caption(f"  {item['description']}")
            else:
                st.info("No matching items found")

        # Export/Import
        st.subheader("Export/Import Repository")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export Repository"):
                try:
                    export_file = repository.export_repository()
                    st.success(f"Repository exported to: {export_file}")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

        with col2:
            uploaded_repo = st.file_uploader("Import Repository", type=['json'], help="Upload a repository JSON file")
            if uploaded_repo is not None:
                if st.button("Import Repository"):
                    try:
                        # Save uploaded file temporarily
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                            tmp_file.write(uploaded_repo.getvalue())
                            tmp_file_path = tmp_file.name
 
                        # Import repository
                        success = repository.import_repository(tmp_file_path)
 
                        # Clean up temp file
                        import os
                        os.unlink(tmp_file_path)
 
                        if success:
                            st.success("Repository imported successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid repository format")
 
                    except Exception as e:
                        st.error(f"Import failed: {str(e)}")

if __name__ == "__main__":
    main()

