# Standard library imports
import os
import uuid
import time
import random
import argparse
import concurrent.futures

# Third-party imports
import requests
from dotenv import load_dotenv

# Local imports
from utils.torrent import (
    search_1337x,
    add_magnet_to_debrid,
    start_magnet_in_debrid
)

# Jellyfin imports
from utils.jellyfin import (
    create_jellyfin_collection,
    add_item_to_collection,
    get_jellyfin_item,
    do_library_scan
)

load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_API_URL = "https://api.themoviedb.org/3"
TUNARR_API_URL = os.getenv('TUNARR_SERVER') + "/api" 

# Generic keywords that are more likely to return good results
generic_keywords = [
    "horror", "action", "comedy", 
    "drama", "adventure", "fantasy",
    "mystery", "crime", "thriller", "romance",
    "animation", "documentary", "family", "horror", "western", "war",
    "history", "biography", "sport", "reality", "game"]

# Specific keywords that are more likely to return good results
specific_keywords  = [
    "antihero", "female protagonist", "superhero", 
    "mcu", "disaster", "live action", "based on young adult novel",
    "based on video game"]

# Search for a keyword in the TMDB API and let user select from matching results.
def search_keyword_id(keyword, title="Unknown"):

    # Construct the API endpoint and parameters
    endpoint = f"{TMDB_API_URL}/search/keyword"
    params = {
        "api_key": TMDB_API_KEY,
        "query": keyword,
    }
    
    try:
        # Make API request and validate response
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        if results:
            # Display matching keywords to user
            print("\nFound these keyword matches:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.get('name')}")
      
            # Keep prompting until valid selection is made
            while True:
                try:
                    choice = int(input("\nSelect a keyword (1-{0}): ".format(len(results))))
                    if 1 <= choice <= len(results):
                        return results[choice-1].get("id"), results[choice-1].get("name") or title
                    
                    print("Please enter a valid number.")
                    quit()
                except ValueError:
                    print("Please enter a valid number.")
                    quit()
        else:
            print("No results found. Try:")
            print(f"`{random.choice(specific_keywords)}`, `{random.choice(generic_keywords)}`")
            quit()
   
    except requests.exceptions.RequestException as e:
        print(f"TMDB API error: {e}")
        return None

# Get movies that have the specified keyword ID.
def get_movies_by_keyword(keyword_id, max_results):

    endpoint = f"{TMDB_API_URL}/keyword/{keyword_id}/movies"
    params = {
        "api_key": TMDB_API_KEY,
        "page": 1,
    }

    results = []  # Initialize results list
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Check initial request

        data = response.json()
        total_pages = data.get("total_pages", 1)  # Handle missing total_pages
        results.extend(data.get("results", []))  # Add initial results

        # Stop if we hit max results
        if len(results) >= max_results:
            return sorted(results[:max_results], key=lambda x: x.get('vote_average', 0), reverse=True)

        # Iterate remaining pages until we hit max results
        for page in range(2, total_pages + 1):
            params["page"] = page
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            results.extend(response.json().get("results", []))
            
            if len(results) >= max_results:
                return sorted(results[:max_results], key=lambda x: x.get('vote_average', 0), reverse=True)

        # Sort all results by vote average before returning
        return sorted(results, key=lambda x: x.get('vote_average', 0), reverse=True)
    except requests.exceptions.RequestException as e:
        print(f"TMDB API error: {e}")

        return []
    
def waiting_animation_dots(message="Processing", delay=0.3, iterations=3):

    for i in range(iterations):
        dots = "." * (i + 1)
        print(f"\r{message}{dots}", end="", flush=True)
        time.sleep(delay)

# Get detailed information about a specific movie.
def get_movie_details(movie_id):

    endpoint = f"{TMDB_API_URL}/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
    }
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"TMDB API error: {e}")
        return None
    
def get_movie_certification(movie):
    endpoint = f"{TMDB_API_URL}/movie/{movie.get('id')}/release_dates"
    params = {
        "api_key": TMDB_API_KEY,
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    return response.json()["results"]["certification"]
    

def process_movie_parallel(movie):
    """Process a single movie in parallel - handles torrent search and magnet addition"""
    title = movie.get('title')
    year = movie.get('release_date')[:4]
    search_term = f"{title} {year}"
    
    print(f"Processing: {search_term}")
    torrent = search_1337x(search_term)
    
    if torrent:
        response, id = add_magnet_to_debrid(torrent['magnet'])
        if response:
            start_magnet_in_debrid(id)
            print(f"✓ {title} ({year}) added to real-debrid!")
            return True
    print(f"✗ Failed to process {title}")
    return False

def add_movie_to_collection_parallel(movie, group_id):
    """Add a single movie to Jellyfin collection in parallel"""
    title = movie.get('title')
    year = movie.get('release_date')[:4]
    
    item_id = get_jellyfin_item(title)
    if item_id:
        add_item_to_collection(group_id, item_id)
        print(f"✓ {title} ({year}) added to collection!")
        return True
    print(f"✗ Failed to add {title} to collection")
    return False

if __name__ == "__main__":
    print("Starting...")

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Search and process movies by keyword or person')
    parser.add_argument('--keyword', '-k', type=str, help='Keyword to search for (use quotes for multiple words)')
    parser.add_argument('--max-results', '-m', type=int, default=50, help='Maximum number of movies to process')
    parser.add_argument('--workers', '-w', type=int, default=5, help='Number of parallel workers')
    args = parser.parse_args()

    keyword = args.keyword if args.keyword else input("Enter a keyword to search for: ")
    keyword_id, title = search_keyword_id(keyword)

    if keyword_id:
        movies = get_movies_by_keyword(keyword_id, args.max_results)

    group_id = None
    if movies:

        if input("\nCreate a jellyfin collection with this collection? (y/n): ").lower() == 'y':              
           # Create a jellyfin collection with the keyword
            group_id = create_jellyfin_collection(title)

        if input(f"\nWould you like to add movies to real-debrid? ({len(movies)}) (y/n): ").lower() == 'y':
            # Process movies in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(process_movie_parallel, movie) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"\nProcessed {successful}/{len(movies)} movies successfully")

            # Wait for zurg to reload
            for i in range(30):
                waiting_animation_dots(f"Wait for zurg reload... {i+1}/30")

        if input("\nWould you like to add movies to a collection? (y/n): ").lower() == 'y':

            # Do a library scan to ensure the movies are added to the library
            do_library_scan()   

            # wait for the library to update
            for i in range(15):
                waiting_animation_dots(f"Waiting for library to update... {i+1}/15")
                
            # Create a jellyfin collection with the keyword if not already created
            if not group_id:
                group_id = create_jellyfin_collection(title)

            # Add movies to collection in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(add_movie_to_collection_parallel, movie, group_id) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"\nAdded {successful}/{len(movies)} movies to collection successfully")

    else:
        print("No movies found with the keyword.")