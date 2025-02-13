import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Jellyfin ---
JELLYFIN_SERVER = os.getenv('JELLYFIN_SERVER')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY')
JELLYFIN_MOVIES_LIBRARY_ID = os.getenv('JELLYFIN_MOVIE_LIBRARY_ID')

# --- TMDB ---
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_API_URL = os.getenv('TMDB_API_URL')

# --- Helper Functions ---
def get_library_scan_task_id():
    """Gets the task scheduler ID for library scanning."""
    try:
        print("Getting library scan task Id...")
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
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to get library scan task Id: {e}")
        return None

def do_library_scan():
    """Performs a library scan on the Jellyfin server."""
    try:
        task_id = get_library_scan_task_id()
        
        if task_id:
            url = f"{JELLYFIN_SERVER}/ScheduledTasks/Running/{task_id}"
            headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            if response.status_code == 204:
                print("Starting library scan...")
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to perform library scan: {e}")

def get_jellyfin_movie(movie_name):
    """Retrieves item ID for a movie by name from the Jellyfin movies library."""
    try:
        url = f"{JELLYFIN_SERVER}/Items?includeItemTypes=Movie&recursive=true&searchTerm={movie_name}"
        headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        items = response.json().get("Items", [])        
        if items:
            # Try exact match first
            for item in items:
                if item["Name"].lower() == movie_name.lower():
                    return item["Id"]
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to retrieve item for movie {movie_name}: {e}")
        return None

def create_jellyfin_collection(collection_name):
    """Creates a new collection in Jellyfin if it doesn't already exist."""
    try:
        collection = get_jellyfin_collection(collection_name)
        if collection:
            print(f"Collection {collection_name} already exists lets use it.")
            return collection

        print("Creating jellyfin collection...")
        url = f"{JELLYFIN_SERVER}/Collections?Name={collection_name}"
        headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }

        response = requests.post(url, headers=headers)
        response.raise_for_status()

        return response.json()["Id"]
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to create collection {collection_name}: {e}")
        return None

def get_jellyfin_collection(collection_name):
    """Retrieves a Jellyfin collection by name."""
    try:
        url = f"{JELLYFIN_SERVER}/Items?recursive=true&includeItemTypes=BoxSet&searchTerm={collection_name}"
        headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        items = response.json().get("Items", [])
        if items:
            for item in items:
                if item["Name"].lower() == collection_name.lower():
                    return item["Id"]   
                       
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to retrieve collection {collection_name}: {e}")
        return None
    
def is_movie_in_collection(name, collection_id):
    """Checks if a movie is already in a Jellyfin collection."""
    try:
        url = f"{JELLYFIN_SERVER}/Items?parentId={collection_id}&recursive=true&includeItemTypes=Movie&searchTerm={name}"
        headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        items = response.json().get("Items", [])
        if items:
            for item in items:
                if item["Name"].lower() == name.lower():
                    return item["Id"]
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to check if movie {name} is in collection: {e}")
    return None

def add_movie_to_collection(collection_id, movie_id):
    """Adds a movie to a Jellyfin collection."""
    try:
        if is_movie_in_collection(movie_id, collection_id):       
            return True
        
        url = f"{JELLYFIN_SERVER}/Collections/{collection_id}/Items?ids={movie_id}"
        headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        if response.status_code == 204:
            return True
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to add item {movie_id} to collection {collection_id}: {e}")
        return False