import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Jellyfin ---
JELLYFIN_SERVER = os.getenv('JELLYFIN_SERVER')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY')
MOVIES_LIBRARY_ID = os.getenv('MOVIE_LIBRARY_ID')

# --- TMDB ---
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_API_URL = "https://api.themoviedb.org/3"

# --- Helper Functions ---
def get_library_scan_task_id():
    """Gets the task scheduler ID for library scanning."""

    print("Getting library scan task ID...")
    url = f"{JELLYFIN_SERVER}/ScheduledTasks"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tasks = response.json()
    
    task_id = None
    for task in tasks:
        if task.get("Key") == "RefreshLibrary":
            task_id = task["Id"]
            break
    
    return task_id

def do_library_scan():
    """Performs a library scan on the Jellyfin server."""
    task_id = get_library_scan_task_id()
    
    if task_id:
        url = f"{JELLYFIN_SERVER}/ScheduledTasks/Running/{task_id}"
        headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        if response.status_code == 204:
            print("Starting library scan...")

def get_jellyfin_item(movie_name):
    """Retrieves item ID for a movie by name from the Jellyfin movies library."""
    url = f"{JELLYFIN_SERVER}/Items?parentId={MOVIES_LIBRARY_ID}&recursive=true&searchTerm={movie_name}"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    items = response.json()["Items"]
    return items[0]["Id"] if items else None

def get_tmdb_keywords(tmdb_id):
    """Retrieves keywords from TMDb for the given TMDb ID."""
    url = f"{TMDB_API_URL}/movie/{tmdb_id}/keywords?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    keywords = []
    if 'keywords' in data and 'keywords' in data['keywords']:

        keywords = [keyword['name'] for keyword in data['keywords']]
    return keywords

def create_jellyfin_collection(collection_name):
    """Creates a new collection in Jellyfin if it doesn't already exist."""
    print("Creating jellyfin collection...")
    url = f"{JELLYFIN_SERVER}/Collections?Name={collection_name}"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    collection_id = response.json()["Id"]
    return collection_id

def add_item_to_collection(collection_id, item_id):
    """Adds an item to a Jellyfin collection."""
    url = f"{JELLYFIN_SERVER}/Collections/{collection_id}/Items?ids={item_id}"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }

    response = requests.post(url, headers=headers)
    response.raise_for_status()

def find_tmdb_id(jellyfin_item):
    """Tries to find the TMDb ID from a Jellyfin item's provider IDs."""
    tmdb_id = None
    
    if 'ProviderIds' in jellyfin_item and jellyfin_item['ProviderIds']:
        for provider, id_value in jellyfin_item['ProviderIds'].items():
            if provider.lower() == "tmdb":
                tmdb_id = int(id_value)
                break
    
    return tmdb_id