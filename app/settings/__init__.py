# /DuckDuckFind/app/settings/__init__.py
from dotenv import set_key
from flask import current_app
import importlib
import os
import ast
import json
from settings.settings_general import settings_general
from settings.settings_search import settings_search
from settings.settings_scrape import settings_scrape
from settings.settings_score import settings_score
from settings.settings_media import settings_media
from settings.settings_viewer import settings_viewer
from settings.settings_connect import settings_connect
from settings.settings_output import settings_output
from settings.allowed_regions import ALLOWED_REGIONS 

API_KEY_FIELDS = ['TRAFIKLAB_API_TOKEN'] 

settings = {}

# Merge all settings into the settings dictionary
settings.update(settings_general)
settings.update(settings_search)
settings.update(settings_scrape)
settings.update(settings_score)
settings.update(settings_media)
settings.update(settings_viewer)
settings.update(settings_connect)
settings.update(settings_output)

def reload_settings_module(module_name):
    """
    Completely reload a module by first removing it from sys.modules.
    This ensures that a fresh version of the module is loaded.
    """
    if module_name in sys.modules:
        del sys.modules[module_name]  # Remove the module from cache
    return importlib.import_module(module_name)

def get_setting(key):
    """Retrieve the value of a setting by key."""
    return settings.get(key, {}).get("value")

def get_dict_setting(setting_name):
    try:
        setting_value = settings.get(setting_name, {}).get('value', '')
        
        print(f"Raw setting value for {setting_name}: {setting_value}")
        
        parsed_value = ast.literal_eval(setting_value)
        
        print(f"Parsed setting value for {setting_name}: {parsed_value}")
        
        return parsed_value
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing the setting '{setting_name}': {e}")
        return {}

def get_description(key):
    """Retrieve the description of a setting by key."""
    return settings.get(key, {}).get("description")

def get_settings_section(section):
    if section == 'general':
        return settings_general
    elif section == 'search':
        return settings_search
    elif section == 'scrape':
        return settings_scrape
    elif section == 'score':
        return settings_score
    elif section == 'media':
        return settings_media
    elif section == 'viewer':
        return settings_viewer
    elif section == 'connect':
        return settings_connect
    elif section == 'output':
        return settings_output
    else:
        return {}

def reload_all_settings():
    """Force reload all settings from their respective files and update the in-memory settings."""
    global settings

    settings_general = reload_settings_module('settings.settings_general')
    settings_search = reload_settings_module('settings.settings_search')
    settings_scrape = reload_settings_module('settings.settings_scrape')
    settings_score = reload_settings_module('settings.settings_score')
    settings_media = reload_settings_module('settings.settings_media')
    settings_viewer = reload_settings_module('settings.settings_viewer')
    settings_connect = reload_settings_module('settings.settings_connect')
    settings_output = reload_settings_module('settings.settings_output')

    settings.clear()
    settings.update(settings_general.settings_general)
    settings.update(settings_search.settings_search)
    settings.update(settings_scrape.settings_scrape)
    settings.update(settings_score.settings_score)
    settings.update(settings_media.settings_media)
    settings.update(settings_viewer.settings_viewer)
    settings.update(settings_connect.settings_connect)
    settings.update(settings_output.settings_output)

    current_app.config['SETTINGS'] = settings.copy()

def generate_settings_form(section):
    """Generate HTML form elements for settings in the specified section."""
    settings = get_settings_section(section)
    form_html = ""

    for key, setting in settings.items():
        
        if 'title' in setting:
            form_html += f"<h3>{setting['title']}</h3>"

        # Handle API keys separately (as password inputs)
        if key in API_KEY_FIELDS:
            form_html += f'''
                <div class="form-group">
                    <label for="{key}">{setting['description']}</label>
                    <input type="password" id="{key}" name="{key}" value="" placeholder="Enter your API key">
                </div>
            '''
        # Handle 'REGION' as a dropdown based on 'ALLOWED_REGIONS'
        elif key == 'REGION':
            form_html += f'''
                <div class="form-group">
                    <label for="{key}">{setting['description']}</label>
                    <select id="{key}" name="{key}">
            '''
            for region in ALLOWED_REGIONS:  # Use imported ALLOWED_REGIONS
                selected = 'selected' if region == setting['value'] else ''
                form_html += f'<option value="{region}" {selected}>{region}</option>'
            form_html += '</select></div>'
        elif isinstance(setting['value'], bool):
            form_html += f'''
                <div class="form-group">
                    <label for="{key}">{setting['description']}</label>
                    <label class="switch">
                    <input type="checkbox" id="{key}" name="{key}" {"checked" if setting['value'] else ""}>
                    <span class="slider"></span>
                    </label>
                </div>
            '''
        elif isinstance(setting['value'], int):
            form_html += f'''
                <div class="form-group">
                    <label for="{key}">{setting['description']}</label>
                    <input type="number" id="{key}" name="{key}" value="{setting['value']}">
                </div>
            '''
        else:
            form_html += f'''
                <div class="form-group">
                    <label for="{key}">{setting['description']}</label>
                    <input type="text" id="{key}" name="{key}" value="{setting['value']}">
                </div>
            '''
    return form_html

def process_settings_form(section, form_data):
    """Process submitted form data and update settings for the specified section."""
    section_settings = get_settings_section(section)

    for key in section_settings.keys():
        form_value = form_data.get(key)

        # Handle API keys separately
        if key in API_KEY_FIELDS:
            if form_value:
                set_key('.env', key, form_value)

        # Handle 'REGION' specifically since it has a set of allowed values
        elif key == 'REGION':
            if form_value not in ALLOWED_REGIONS:  # Use imported ALLOWED_REGIONS
                raise ValueError(f"Invalid region selected: {form_value}")
            section_settings[key]['value'] = form_value

        # Handle boolean settings (checkboxes)
        elif isinstance(section_settings[key]['value'], bool):
            section_settings[key]['value'] = form_value is not None

        # Handle integer settings (numeric input)
        elif isinstance(section_settings[key]['value'], int):
            section_settings[key]['value'] = int(form_value) if form_value else section_settings[key]['value']

        # Handle text or other settings
        else:
            section_settings[key]['value'] = form_value if form_value else section_settings[key]['value']

    save_settings_to_python()

# SAVE SETTINGS TO PYTHON FILES
def save_settings_to_python():
    """Save the current settings back to their respective Python files."""
    sections = {
        'settings_general.py': settings_general,
        'settings_search.py': settings_search,
        'settings_scrape.py': settings_scrape,
        'settings_score.py': settings_score,
        'settings_media.py': settings_media,
        'settings_viewer.py': settings_viewer,
        'settings_connect.py': settings_connect,
        'settings_output.py': settings_output,
    }

    for filename, section_settings in sections.items():
        try:
            with open(f'/app/app/settings/{filename}', 'w') as f:
                f.write("# This file is auto-generated by the application.\n\n")

                f.write(f"{filename.split('.')[0]} = {{\n")
                for key, setting in section_settings.items():
                    f.write(f'    "{key}": {{\n')

                    # Write the title if it exists
                    if 'title' in setting:
                        f.write(f'        "title": {repr(setting["title"])},\n')

                    # Handle list values properly
                    if isinstance(setting['value'], list):
                        f.write('        "value": [\n')
                        for item in setting['value']:
                            f.write(f'            {repr(item)},\n')
                        f.write('        ],\n')
                    else:
                        f.write(f'        "value": {repr(setting["value"])},\n')

                    # Write the description
                    f.write(f'        "description": {repr(setting["description"])}\n')
                    f.write("    },\n")
                f.write("}\n")
            print(f"Settings successfully saved to {filename}")
        except Exception as e:
            print(f"Error saving settings to {filename}: {e}")


# Function to save settings for all sections to a JSON file
def save_settings(file_path='settings.json'):
    """Save the current settings to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            combined_settings = {}
            combined_settings.update(settings_general)
            combined_settings.update(settings_search)
            combined_settings.update(settings_connect)
            json.dump(combined_settings, f, indent=4)
        print(f"Settings successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving settings: {e}")

