"""
Filename: tmdb.py
Date: 2023-10-05
Author: robinbtw

Description:
This module provides a class to manage interactions with the TMDB (The Movie Database) API.
It includes methods to search for movies, retrieve movie details, external IDs, release dates, and credits.
"""

# Import standard libraries
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TMDBManager:
    """A class to manage TMDB API interactions."""

    def __init__(self):
        """Initializes the TMDBManager with API credentials."""
        self.tmdb_api_key = os.getenv('TMDB_API_KEY')
        self.tmdb_api_url = os.getenv('TMDB_API_URL')

    def _make_request(self, method, endpoint, params=None, data=None, timeout=5):
        """Internal helper function to make API requests."""
        params = params or {}
        params['api_key'] = self.tmdb_api_key 
        url = f"{self.tmdb_api_url}{endpoint}"
        try:
            response = requests.request(method, url, params=params, data=data, timeout=timeout)
            response.raise_for_status()  
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ TMDb request failed: {e}")
            return None
        
    def search_movies(self, movie_name):
        """Searches for a movie by name on TMDB."""
        params = {'query': movie_name}
        return self._make_request('GET', '/search/movie?include_adult=false&language=en-US&page=1', params=params)
    
    def get_person(self, person_name):
        """Searches for a person by name on TMDB, return id."""
        params = {'query': person_name}
        return self._make_request('GET', '/search/person', params=params)
    
    def get_genres(self):
        """Retrieves a list of genres from TMDB."""
        return self._make_request('GET', '/genre/movie/list')

    def get_movie_details(self, movie_id):
        """Retrieves details for a specific movie by ID from TMDB."""
        return self._make_request('GET', f'/movie/{movie_id}')

    def get_movie_external_ids(self, movie_id):
        """Retrieves external IDs for a specific movie by ID from TMDB."""
        return self._make_request('GET', f'/movie/{movie_id}/external_ids')

    def get_movie_release_dates(self, movie_id):
         """Retrieves release dates for a specific movie by ID from TMDB."""
         return self._make_request('GET', f'/movie/{movie_id}/release_dates')
    
    def get_keyword(self, keyword):
        """Searches for a keyword by name on TMDB."""
        params = {'query': keyword}
        return self._make_request('GET', '/search/keyword', params=params)
    
    def get_movies_by_keyword(self, keyword_id, page=1):
        """Retrieves movies by keyword ID from TMDB."""
        params = {'page': page}
        return self._make_request('GET', f'/keyword/{keyword_id}/movies', params=params), params
    
    def get_movie_credits(self, person_id):
        """Retrieves combined credits for a specific person by ID from TMDB."""
        return self._make_request('GET', f'/person/{person_id}/movie_credits')
    
    def get_trending_movies(self, time_window='week'):
        """Retrieves trending movies from TMDB."""
        return self._make_request('GET', f'/trending/movie/{time_window}')
    
    def get_similar_movies(self, movie_id):
        """Retrieves similar movies for a specific movie by ID from TMDB."""
        return self._make_request('GET', f'/movie/{movie_id}/similar')
    
    def discover_movies(self, params=None):
        """Discover movies using various filters."""
        default_params = {
            'sort_by': 'popularity.desc',
            'vote_count.gte': 1000,  # Only well-reviewed movies
            'include_adult': False,
            'language': 'en-US'
        }
        if params:
            default_params.update(params)
        return self._make_request('GET', '/discover/movie', params=default_params)

    
