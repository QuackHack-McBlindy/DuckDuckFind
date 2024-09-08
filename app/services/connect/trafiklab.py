# /app/services/connect/trafiklab.py

print("/app/services/connect/trafiklab.py has been imported successfully!")

from datetime import datetime, timezone, timedelta
import re
import requests
from settings import get_setting

GMT_PLUS_2 = timezone(timedelta(hours=2))  

def trafiklab_parse_query(query):
    query = query.lower().strip()
    from_pattern = re.compile(r'från\s+([\w\s]+)\s+till\s+([\w\s]+)')
    to_pattern = re.compile(r'till\s+([\w\s]+)\s+från\s+([\w\s]+)')

    match_from_to = from_pattern.search(query)
    match_to_from = to_pattern.search(query)

    if match_from_to:
        origin = match_from_to.group(1).strip()
        destination = match_from_to.group(2).strip()
    elif match_to_from:
        destination = match_to_from.group(1).strip()
        origin = match_to_from.group(2).strip()
    else:
        raise ValueError("Kunde inte tolka frågan. Använd formatet 'När går bussen från [Start] till [Slut]?' eller 'När går bussen till [Slut] från [Start]?'")
    
    return origin, destination

def trafiklab_get_stop_id(stop_name, TRAFIKLAB_API_TOKEN):
    url = f"https://api.resrobot.se/v2.1/location.name?input={stop_name}&format=json&accessId={TRAFIKLAB_API_TOKEN}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
    except ValueError:
        return "Error: Could not parse JSON response."
    
    stop_locations = [item['StopLocation'] for item in data.get('stopLocationOrCoordLocation', []) if 'StopLocation' in item]
    
    if not stop_locations:
        return f"Error: No stops found for {stop_name}."
    
    stop_id = stop_locations[0]['extId']
    return stop_id

def trafiklab_get_next_route(origin_id, dest_id, TRAFIKLAB_API_TOKEN):
    url = f"https://api.resrobot.se/v2.1/trip?format=json&originId={origin_id}&destId={dest_id}&passlist=0&showPassingPoints=0&numF=3&accessId={TRAFIKLAB_API_TOKEN}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
    except ValueError:
        return "Error: Could not parse JSON response."
    
    if 'Trip' not in data or not data['Trip']:
        return "Error: No trips found."
    
    return data['Trip']

def trafiklab_format_transport_response(trips):
    now = datetime.now(GMT_PLUS_2)
    formatted_response = f"Aktuell tid är {now.strftime('%H:%M')}.\n"
    
    for i, trip in enumerate(trips):
        origin = trip['LegList']['Leg'][0]['Origin']
        destination = trip['LegList']['Leg'][0]['Destination']
        product = trip['LegList']['Leg'][0]['Product'][0]
        
        dep_time = datetime.strptime(f"{origin['date']} {origin['time']}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(GMT_PLUS_2)
        arr_time = datetime.strptime(f"{destination['date']} {destination['time']}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).astimezone(GMT_PLUS_2)
        
        minutes_to_departure = int((dep_time - now).total_seconds() / 60)
        day = dep_time.strftime("%A")
        bus_number = product['num']
        
        if i == 0:
            formatted_response += (
                f"Nästa resa från {origin['name']} till {destination['name']} med buss {bus_number} avgår om {minutes_to_departure} minuter "
                f"({dep_time.strftime('%H:%M')}) på {day} och anländer kl. {arr_time.strftime('%H:%M')}."
            )
        else:
            formatted_response += (
                f" Nästa avgång efter det med buss {bus_number} är om {minutes_to_departure} minuter ({dep_time.strftime('%H:%M')})."
            )

    return formatted_response
