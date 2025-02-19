"""
Filename: jelyfin.py
Date: 02-17-2025
Author: robinbtw

Description:
This module provides a class to manage interactions with the Jellyfin API.
It includes methods to perform library scans, retrieve item IDs for movies, and create collections.
"""

# Import standard libraries
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class JellyfinManager:
    """A class to manage Jellyfin API interactions."""

    def __init__(self):
        """Initializes the JellyfinManager with API credentials."""
        self.jellyfin_server = os.getenv('JELLYFIN_SERVER')
        self.jellyfin_api_key = os.getenv('JELLYFIN_API_KEY')
        self.headers = {"Authorization": "Mediabrowser Token=" + self.jellyfin_api_key}

    def _make_request(self, method, endpoint, params=None, timeout=5):
        """Internal helper function to make API requests."""
        url = f"{self.jellyfin_server}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, timeout=timeout)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            
            if method.upper() in ['POST', 'DELETE']:
                return True if response.status_code == 204 else response.json() if response.content else True

            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Jellyfin request ({endpoint}) failed: {e}")
            return None

    def _get_library_scan_task_id(self):
        """Gets the task scheduler ID for library scanning."""
        print("Getting library scan task Id...")
        tasks = self._make_request('GET', "/ScheduledTasks")
        
        task_id = None
        for task in tasks:
            if task.get("Key") == "RefreshLibrary":
                task_id = task["Id"]
                break
        
        return task_id
    
    def _get_all_movies(self):
        """Retrieves all movies from Jellyfin."""
        params = {
            'recursive': 'true',
            'includeItemTypes': 'Movie'
        }
        return self._make_request('GET', "/Items", params=params)
    
    def _get_jellyfin_collection(self, collection_name):
        """Retrieves a Jellyfin collection by name."""
        params = {'recursive': 'true', 'includeItemTypes': 'BoxSet', 'searchTerm': collection_name}
        response = self._make_request('GET', "/Items", params=params)
        
        if response:
            items = response.get("Items", [])
            if items:
                for item in items:
                    if item["Name"].lower() == collection_name.lower():
                        return item["Id"]
        return None
        
    def _is_movie_in_collection(self, movie_id, collection_id) -> bool:
        """Checks if a movie is already in a Jellyfin collection."""
        params = {'parentId': collection_id, 'recursive': 'true'}
        response = self._make_request('GET', "/Items", params=params)
        
        if response:
            items = response.get("Items", [])
            if items:
                for item in items:
                    if item["Id"].lower() == movie_id.lower():
                        return True
        return False

    def delete_movie(self, movie_id):
        """Removes a movie from the Jellyfin library."""
        self._make_request('DELETE', f"/Items/{movie_id}")

    def get_movie(self, movie_name):
        """Retrieves item ID for a movie by name from the Jellyfin movies library."""
        params = {'includeItemTypes': 'Movie', 'recursive': 'true', 'searchTerm': movie_name}
        response = self._make_request('GET', "/Items", params=params)
        
        if response:
            items = response.get("Items", [])
            if items:
                # Try exact match first
                for item in items:
                    if item["Name"].lower() == movie_name.lower():
                        return item
        return None

    def get_all_collections(self):
        """Retrieves all Jellyfin collections."""
        params = {'recursive': 'true', 'includeItemTypes': 'BoxSet'}
        return self._make_request('GET', "/Items", params=params)
    
    def get_all_duplicate_movies(self):
        """Retrieves duplicate movies from Jellyfin by name."""
        movies = self._get_all_movies().get("Items", [])
        seen = {}
        duplicates = []

        for movie in movies:
            name = movie.get('Name')
            if name in seen:
                duplicates.append({
                    'name': name,
                    'original_id': seen[name],
                    'duplicate_id': movie.get('Id')
                })
            else:
                seen[name] = movie.get('Id')

        return duplicates
        
    def add_movie_to_collection(self, movie_id, collection_id):
        """Adds a movie to a Jellyfin collection."""
        if self._is_movie_in_collection(movie_id, collection_id):
            return
                
        params = {'ids': movie_id}
        self._make_request('POST', f"/Collections/{collection_id}/Items", params=params)

    def create_collection(self, collection_name):
        """Creates a new collection in Jellyfin if it doesn't already exist."""
        collection = self._get_jellyfin_collection(collection_name)
        if collection:
            print(f"Collection {collection_name} already exists lets use it.")
            return collection

        print("Creating jellyfin collection...")
        params = {'Name': collection_name}
        response = self._make_request('POST', "/Collections", params=params)
        return response["Id"] if response else None
    
    def do_library_scan(self):
        """Performs a library scan on the Jellyfin server."""
        task_id = self._get_library_scan_task_id()
        if task_id:
            response = self._make_request('POST', f"/ScheduledTasks/Running/{task_id}")
            if response:
                print("Starting library scan...")
                return True


            

