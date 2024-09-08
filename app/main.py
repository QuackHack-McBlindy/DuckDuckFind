# /DuckDuckFind/app/main.py
from flask import Flask, request, jsonify, render_template, send_from_directory, current_app, url_for, redirect, Response, flash, send_file
import os
import ast
import pytz
import requests
import logging
from datetime import datetime, timedelta
from settings import *
from services.search.search import *
from services.search.documents import *
from services.search.photos import *
from services.stocks.price import *
from services.connect.trafiklab import *
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
app = Flask(__name__)
app.config['SETTINGS'] = settings
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
ENABLE_LOGGING = get_setting("ENABLE_LOGGING")

transport_triggers = ast.literal_eval(get_setting("transport_triggers"))
document_triggers = ast.literal_eval(get_setting("document_triggers"))
stock_triggers = ast.literal_eval(get_setting("stock_triggers"))
photos_triggers = ast.literal_eval(get_setting("photos_triggers"))

ENABLE_TRANSPORT = get_setting("ENABLE_TRANSPORT")
ENABLE_DOCUMENT = get_setting("ENABLE_DOCUMENT")
ENABLE_STOCK = get_setting("ENABLE_STOCK")
ENABLE_PHOTO = get_setting("ENABLE_PHOTO")
ENABLE_VIEWER = get_setting("ENABLE_VIEWER")

handlers = {
    'transport': lambda query: handle_transport(query) if ENABLE_TRANSPORT else web_search(query),
    'document': lambda query: handle_document(query) if ENABLE_DOCUMENT else web_search(query),
    'stock': lambda query: handle_query() if ENABLE_STOCK else web_search(query),
    'photos': lambda query: find_photos() if ENABLE_PHOTO else web_search(query),
    'default': lambda query: web_search(query),
}





#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ ROUTES ←──
@app.route('/', methods=['POST'])
def route_request(): 
    data = request.json
    query = data.get('query', '').lower()

    for trigger, handler in handlers.items():
        if any(word in query for word in globals().get(f"{trigger}_triggers", [])):
            response = handler(query)
            break
    else:
        response = handlers['default'](query)
    return response 

def handle_transport(query):
    try:
        TRAFIKLAB_API_TOKEN = os.getenv('TRAFIKLAB_API_TOKEN')   
        if not TRAFIKLAB_API_TOKEN:
            return "Error: TRAFIKLAB_API_TOKEN is not set."

        origin_stop, dest_stop = trafiklab_parse_query(query)
        origin_id = trafiklab_get_stop_id(origin_stop, TRAFIKLAB_API_TOKEN)
        dest_id = trafiklab_get_stop_id(dest_stop, TRAFIKLAB_API_TOKEN)

        if origin_id.startswith("Error:") or dest_id.startswith("Error:"):
            return origin_id if origin_id.startswith("Error:") else dest_id
        trips = trafiklab_get_next_route(origin_id, dest_id, TRAFIKLAB_API_TOKEN)
        if isinstance(trips, str) and trips.startswith("Error:"):
            return trips
        
        return trafiklab_format_transport_response(trips) 
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def handle_document(query):
    if not query:
        return "No query provided"
    
    for trigger in document_triggers:
        if trigger in query:
            query = query.replace(trigger, '').strip()

    if not query:
        return "The query is empty after removing trigger words."
    
    result_text = search_documents(query)
    return result_text

def web_search(query):
    if not query:
        return "No query provided"   
    result = search_web_for_answer(query)
    return result

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ CHAT ←──
@app.route('/chat', methods=['POST', 'GET'])
def render_chat():
    return render_template('chat.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    if not data or 'query' not in data:
        return Response("No query provided", mimetype='text/plain', status=400)

    return route_request()

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ STOCK PRICE ←──
@app.route('/stock_price', methods=['POST'])
def handle_query():
    data = request.get_json()
    if not data or 'query' not in data:
        return Response("JSON payload with 'query' field is required", status=400, mimetype='text/plain')
    query = data['query']
    
    query = query.replace("?", "").replace("!", "")
    
    result = get_stock_price(query) 
    if "error" in result:
        return Response(result["error"], status=404, mimetype='text/plain')

    detected_language = detect_language(query)
    formatted_output = format_output(result['symbol'], result['price'], detected_language)
    return Response(formatted_output, mimetype='text/plain')

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
if ENABLE_VIEWER:
#──→ VIEWER ←──
    @app.route('/viewer')
    def viewer():
        global selected_photos
        if not selected_photos:
            selected_photos, debug_info = find_photos_one_year_ago(photo_dir)
            if not selected_photos:
                return render_template('viewer_empty.html')

            debug_info_html = "<br>".join(debug_info)  # Convert debug info to HTML
            return render_template('viewer.html', photos=selected_photos, debug_info_html=debug_info_html)
        return render_template('viewer.html', photos=selected_photos)

#──→ FIND PHOTOS ←──
@app.route('/find_photos', methods=['POST'])
def find_photos():
    try:
        data = request.get_json()
        query = data.get('query', '')
        year = extract_year_from_query(query)

        if not year:
            return jsonify({"error": "Please provide a valid year in the format YYYY"}), 400

        global selected_photos
        selected_photos, debug_info = find_photos_by_year(photo_dir, year)

        debug_info_html = "<br>".join(debug_info)
        gallery_link = url_for('viewer')

        if 'curl' in request.headers.get('User-Agent', '').lower():
            print(f"Found {len(selected_photos)} photos from the year {year}, displaying them in the viewer.")

            return f"Found {len(selected_photos)} photos from the year {year}, displaying them in the viewer."

        return render_template('viewer.html',
                               photos=selected_photos,
                               debug_info_html=debug_info_html,
                               gallery_link=gallery_link)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

#──→ PHOTO MEMORIES ←──
@app.route('/find_photos_one_year_ago')
def find_photos_one_year_ago_route():
    global selected_photos
    selected_photos, debug_info = find_photos_one_year_ago(photo_dir)

    if selected_photos:
        debug_info_html = "<br>".join(debug_info)  # Convert debug info to HTML
        viewer_link = url_for('viewer')
        return f"<p>Found {len(selected_photos)} photos taken exactly one year ago.</p><a href='{viewer_link}'>Viewer</a><br><br><strong>Debug Information:</strong><br>{debug_info_html}"
    else:
        debug_info_html = "<br>".join(debug_info)  
        return f"No photos found taken exactly one year ago.<br><br><strong>Debug Information:</strong><br>{debug_info_html}"

#──→ SERVE PHOTO ←──
@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory('/app/app/Media/Photos', filename)
    
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS ←──
@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    return redirect(url_for('settings_general_page'))
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / GENERAL ←──
@app.route('/settings/general', methods=['GET', 'POST'])
def settings_general_page():
    if request.method == 'POST':
        try:
            process_settings_form('general', request.form)
            save_settings_to_python()
            
            from settings import settings_general
            current_app.config['SETTINGS'].update(settings_general)

            return redirect(url_for('settings_general_page'))
        except Exception as e:
            return render_template('settings_general.html', settings=current_app.config['SETTINGS'], error=str(e))

    form_html = generate_settings_form('general')
    return render_template('settings_general.html', form_html=form_html, settings=current_app.config['SETTINGS'])

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / SEARCH ←──
@app.route('/settings/search', methods=['GET', 'POST'])
def settings_search_page():
    if request.method == 'POST':
        try:
            process_settings_form('search', request.form)

            save_settings_to_python()

            current_app.config['SETTINGS'].update(settings_search)

            return redirect(url_for('settings_search_page'))
        except Exception as e:
            return render_template('settings_search.html', form_html=generate_settings_form('search'), error=str(e))

    form_html = generate_settings_form('search')
    return render_template('settings_search.html', form_html=form_html, settings=current_app.config['SETTINGS'])

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / SCRAPE ←──
@app.route('/settings/scrape', methods=['GET', 'POST'])
def settings_scrape_page():
    if request.method == 'POST':
        try:
            process_settings_form('scrape', request.form)
            save_settings_to_python()
            from settings import settings_scrape
            current_app.config['SETTINGS'].update(settings_scrape)

            return redirect(url_for('settings_scrape_page'))
        except Exception as e:
            return render_template('settings_scrape.html', settings=current_app.config['SETTINGS'], error=str(e))

    form_html = generate_settings_form('scrape')
    return render_template('settings_scrape.html', form_html=form_html, settings=current_app.config['SETTINGS'])

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / SCORE ←──
@app.route('/settings/score', methods=['GET', 'POST'])
def settings_score_page():
    if request.method == 'POST':
        try:
            process_settings_form('score', request.form)
            save_settings_to_python()
            from settings import settings_score
            current_app.config['SETTINGS'].update(settings_score)

            return redirect(url_for('settings_score_page'))
        except Exception as e:
            return render_template('settings_score.html', settings=current_app.config['SETTINGS'], error=str(e))

    form_html = generate_settings_form('score')
    return render_template('settings_score.html', form_html=form_html, settings=current_app.config['SETTINGS'])

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / MEDIA ←──
@app.route('/settings/media', methods=['GET', 'POST'])
def settings_media_page():
    if request.method == 'POST':
        try:
            process_settings_form('media', request.form)
            save_settings_to_python()
            from settings import settings_media
            current_app.config['SETTINGS'].update(settings_media)

            return redirect(url_for('settings_media_page'))
        except Exception as e:
            return render_template('settings_media.html', settings=current_app.config['SETTINGS'], error=str(e))

    form_html = generate_settings_form('media')
    return render_template('settings_media.html', form_html=form_html, settings=current_app.config['SETTINGS'])

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / VIEWER ←──
@app.route('/settings/viewer', methods=['GET', 'POST'])
def settings_viewer_page():
    if request.method == 'POST':
        try:
            process_settings_form('viewer', request.form)
            save_settings_to_python()
            from settings import settings_viewer
            current_app.config['SETTINGS'].update(settings_viewer)

            return redirect(url_for('settings_viewer_page'))
        except Exception as e:
            return render_template('settings_viewer.html', settings=current_app.config['SETTINGS'], error=str(e))

    form_html = generate_settings_form('viewer')
    return render_template('settings_viewer.html', form_html=form_html, settings=current_app.config['SETTINGS'])

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / CONNECT ←──
@app.route('/settings/connect', methods=['GET', 'POST'])
def settings_connect_page():
    if request.method == 'POST':
        try:
            process_settings_form('connect', request.form)
            save_settings_to_python()
            from settings import settings_connect
            current_app.config['SETTINGS'].update(settings_connect)

            return redirect(url_for('settings_connect_page'))
        except Exception as e:
            return render_template('settings_connect.html', settings=current_app.config['SETTINGS'], error=str(e))

    form_html = generate_settings_form('connect')
    return render_template('settings_connect.html', form_html=form_html, settings=current_app.config['SETTINGS'])

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / OUTPUT ←──
@app.route('/settings/output', methods=['GET', 'POST'])
def settings_output_page():
    if request.method == 'POST':
        try:
            process_settings_form('output', request.form)
            save_settings_to_python()
            from settings import settings_output
            current_app.config['SETTINGS'].update(settings_output)

            return redirect(url_for('settings_output_page'))
        except Exception as e:
            return render_template('settings_output.html', settings=current_app.config['SETTINGS'], error=str(e))

    form_html = generate_settings_form('output')
    return render_template('settings_output.html', form_html=form_html, settings=current_app.config['SETTINGS'])
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ SETTINGS / RESET ←──
@app.route('/reset_settings', methods=['POST'])
def reset_settings():
    return 'test', 200

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ MISC ←──
@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if ENABLE_LOGGING:
    logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    @app.before_request
    def log_request():
        logging.info(f"Request: {request.method} {request.url}")
        logging.info(f"Headers: {dict(request.headers)}")
        
        request_data = request.get_data(as_text=True)
        if request_data:
            logging.info(f"Body: {request_data}")

    @app.after_request
    def log_response(response):
        if request.path.startswith('/static'):
            return response

        logging.info(f"Response Status: {response.status}")

        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type or 'application/json' in content_type:
            response_data = response.get_data(as_text=True)
            logging.info(f"Response Body: {response_data}")
            response.set_data(response_data)
        else:
            logging.info(f"Binary Response: {len(response.get_data())} bytes")

        return response
else:
    print("Logging is disabled.")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°°✶.•°•.•°•.•°•.✶°
#──→ END ←──
