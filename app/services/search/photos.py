# /DuckDuckFind/app/services/search/photos.py

print("/app/services/search/photos.py has been imported successfully!")

from datetime import datetime, timedelta
import re
import os
import pytz
from PIL import Image
from PIL.ExifTags import TAGS

photo_dir = '/app/app/Media/Photos'
selected_photos = []

def extract_year_from_query(query):
    """Extract the year from the given query string."""
    match = re.search(r'(\d{4})', query)
    if match:
        return int(match.group(1))
    return None

def extract_year_from_input(input_string):
    match = re.search(r'(\d{4})', input_string)
    if match:
        return int(match.group(1))
    else:
        print("No valid year found in the input.")
        sys.exit(1)

def get_date_taken(path):
    """Extract the DateTimeOriginal from the EXIF data of an image."""
    try:
        image = Image.open(path)
        exif_data = image._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'DateTimeOriginal':
                    return value.split(" ")[0]  # Return only the date part
    except Exception as e:
        print(f"Error reading EXIF data from {path}: {e}")
    return None

def find_photos_by_year(photo_dir, year):
    photos = []
    debug_info = []  # To store debug information

    for root, _, files in os.walk(photo_dir):
        debug_info.append(f"Searching in directory: {root}")
        for file in files:
            file_path = os.path.join(root, file)
            debug_info.append(f"Checking file: {file_path}")
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                date_taken = get_date_taken(file_path)
                if date_taken:
                    photo_year = date_taken.split(":")[0]
                    debug_info.append(f"Date Taken: {date_taken}")
                    if photo_year == str(year):
                        photos.append(os.path.relpath(file_path, photo_dir))
                        debug_info.append(f"Found matching photo: {file_path}")

    return photos, debug_info




def find_photos_one_year_ago(photo_dir):
    photos = []
    debug_info = []

    sweden_tz = pytz.timezone('Europe/Stockholm')

    today_sweden = datetime.now(sweden_tz)

    one_year_ago_start = (today_sweden - timedelta(days=1)).replace(year=today_sweden.year - 1).strftime("%Y:%m:%d")
    one_year_ago_end = (today_sweden + timedelta(days=1)).replace(year=today_sweden.year - 1).strftime("%Y:%m:%d")

    debug_info.append(f"Searching for photos from the date range: {one_year_ago_start} to {one_year_ago_end}")

    for root, _, files in os.walk(photo_dir):
        debug_info.append(f"Searching in directory: {root}")
        for file in files:
            file_path = os.path.join(root, file)
            debug_info.append(f"Checking file: {file_path}")
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                date_taken = get_date_taken(file_path)
                if date_taken:
                    date_taken_str = date_taken.split(" ")[0]  
                    debug_info.append(f"Date Taken: {date_taken_str}")
                    
                    if one_year_ago_start <= date_taken_str <= one_year_ago_end:
                        photos.append(os.path.relpath(file_path, photo_dir))
                        debug_info.append(f"Found matching photo: {file_path}")

    return photos, debug_info
