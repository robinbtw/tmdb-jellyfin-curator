"""
Filename: jelyfin.py
Date: 2023-10-05
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

    def _make_request(self, method, endpoint, params=None, data=None, timeout=5):
        """Internal helper function to make API requests."""
        url = f"{self.jellyfin_server}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, data=data, timeout=timeout)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"✗ API request failed: {e}")
            return None

    def get_library_scan_task_id(self):
        """Gets the task scheduler ID for library scanning."""
        try:
            print("Getting library scan task Id...")
            url = f"{self.jellyfin_server}/ScheduledTasks"
            response = requests.get(url, headers=self.headers)
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

    def do_library_scan(self):
        """Performs a library scan on the Jellyfin server."""
        try:
            task_id = self.get_library_scan_task_id()
            
            if task_id:
                url = f"{self.jellyfin_server}/ScheduledTasks/Running/{task_id}"
                response = requests.post(url, headers=self.headers)
                response.raise_for_status()
                if response.status_code == 204:
                    print("Starting library scan...")

        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to perform library scan: {e}")

    def get_jellyfin_movie(self, movie_name):
        """Retrieves item ID for a movie by name from the Jellyfin movies library."""
        try:
            url = f"{self.jellyfin_server}/Items?includeItemTypes=Movie&recursive=true&searchTerm={movie_name}"
            response = requests.get(url, headers=self.headers)
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

    def create_jellyfin_collection(self, collection_name):
        """Creates a new collection in Jellyfin if it doesn't already exist."""
        try:
            collection = self.get_jellyfin_collection(collection_name)
            if collection:
                print(f"Collection {collection_name} already exists lets use it.")
                return collection

            print("Creating jellyfin collection...")
            url = f"{self.jellyfin_server}/Collections?Name={collection_name}"
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()

            return response.json()["Id"]
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to create collection {collection_name}: {e}")
            return None

    def get_jellyfin_collection(self, collection_name):
        """Retrieves a Jellyfin collection by name."""
        try:
            url = f"{self.jellyfin_server}/Items?recursive=true&includeItemTypes=BoxSet&searchTerm={collection_name}"
            response = requests.get(url, headers=self.headers)
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
        
    def get_all_jellyfin_collections(self):
        """Retrieves all Jellyfin collections."""
        try:
            url = f"{self.jellyfin_server}/Items?recursive=true&includeItemTypes=BoxSet"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to retrieve all collections: {e}")
            return None
        
    def is_movie_in_collection(self, movie_id, collection_id):
        """Checks if a movie is already in a Jellyfin collection."""
        try:
            url = f"{self.jellyfin_server}/Items?parentId={collection_id}&recursive=true"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            items = response.json().get("Items", [])
            if items:
                for item in items:
                    if item["Id"].lower() == movie_id.lower():
                        return item["Id"]
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to check if movie {movie_id} is in collection: {e}")
        return None

    def add_movie_to_collection(self, movie_id, collection_id):
        """Adds a movie to a Jellyfin collection."""
        try:
            if self.is_movie_in_collection(movie_id, collection_id):
                return

            url = f"{self.jellyfin_server}/Collections/{collection_id}/Items?ids={movie_id}"
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to add movie to collection: {e}")

    def get_all_movies(self):
        """Retrieves all movies from Jellyfin."""
        try:
            url = f"{self.jellyfin_server}/Items?recursive=true&includeItemTypes=Movie"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to retrieve all movies: {e}")
            return None