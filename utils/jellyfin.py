import json
import requests
import os

JELLYFIN_SERVER = "http://localhost:8096"  # Replace with your Jellyfin server address
JELLYFIN_API_KEY = ""  # Replace with your Jellyfin API key
MOVIE_LIBRARY_ID = "" # Replace with your Movie Library ID. You can find this in the Jellyfin web interface.
TMDB_API_KEY = ""  # Replace with your TMDb API key

def do_library_scan():

    # TODO: figure out what this hash/request is: 7738148ffcd07979c7ceb148e06b3aed | replace it with yours (soon)
    """Performs a library scan on the Jellyfin server."""
    url = f"{JELLYFIN_SERVER}/ScheduledTasks/Running/7738148ffcd07979c7ceb148e06b3aed"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    if response.status_code == 204:
        print("Starting library scan...")

def get_jellyfin_item(movie_name):
    """Retrieves item ID for a movie by name from the Jellyfin movies library."""
    url = f"{JELLYFIN_SERVER}/Items?parentId={MOVIE_LIBRARY_ID}&recursive=true&searchTerm={movie_name}"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for bad status codes
    items = response.json()["Items"]
    if items:
        return items[0]["Id"], items[0]["ProductionYear"] 
    else:
        return None, None

def get_tmdb_keywords(tmdb_id):
    """Retrieves keywords from TMDb for the given TMDb ID."""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/keywords?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if 'keywords' in data and 'keywords' in data['keywords']: #check if keywords are present, some movies might not have them
        return [keyword['name'] for keyword in data['keywords']]
    else:
        return []


def create_jellyfin_collection(collection_name):
    print("Creating jellyfincollection...")
    """Creates a new collection in Jellyfin if it doesn't already exist."""    # Create ne collection if it doesn't exist
    url = f"{JELLYFIN_SERVER}/Collections?Name={collection_name}"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["Id"]

def add_item_to_collection(collection_id, item_id):
    """Adds an item to a Jellyfin collection."""
    url = f"{JELLYFIN_SERVER}/Collections/{collection_id}/Items?ids={item_id}"
    headers = {"Authorization": "Mediabrowser Token=" + JELLYFIN_API_KEY }

    response = requests.post(url, headers=headers)
    response.raise_for_status()


def find_tmdb_id(jellyfin_item):
    """Tries to find the TMDb ID from a Jellyfin item's provider IDs."""

    if 'ProviderIds' in jellyfin_item and jellyfin_item['ProviderIds']:
        for provider, id_value in jellyfin_item['ProviderIds'].items():
            if provider.lower() == "tmdb":
                return int(id_value)
    return None