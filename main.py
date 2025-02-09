import requests
import uuid
import time
import random
import argparse
from utils.torrent import search_1337x, add_magnet_to_debrid, start_magnet_in_debrid
from utils.jellyfin import create_jellyfin_collection, add_item_to_collection, get_jellyfin_item, do_library_scan

TMDB_API_KEY = ""  # Replace with your actual TMDB API key
TMDB_API_URL = "https://api.themoviedb.org/3"
TUNARR_API_URL = "http://localhost:8000/api"  # Adjust this to your Tunarr server URL

generic_keywords = [
    "horror", "action", "comedy", 
    "drama", "adventure", "fantasy",
    "mystery", "crime", "thriller", "romance",
    "animation", "documentary", "family", "horror", "western", "war",
    "history", "biography", "sport", "reality", "game"]

specific_keywords  = [
    "antihero", "mutant", "superhero", 
    "mcu", "dcu", "live action", "animated",
    "video game"]

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

# TODO: broken
def add_movie_to_channel(movie, jellyfin_movie_id):
    id = str(uuid.uuid4())

    program_data = {
        "type": "manual",
        "programs": {
            f"{id}": {
                "persisted": True,
                "uniqueId": f"{id}",
                "summary": f"{movie.get('overview')}",
                "date": f"{movie.get('release_date')}T00:00:00.0000000Z",
                "rating": str(get_movie_certification(movie)),
                "title": f"{movie.get('title')}",
                "duration": 1,
                "type": "content",
                "id": id,
                "subtype": "movie",
                "externalIds": [
                    {
                        "type": "multi",
                        "source": "jellyfin",
                        "sourceId": "Jellyfin",
                        "id": f"{jellyfin_movie_id}"
                    },                            
                    {
                        "type": "single",
                        "source": "tmdb",
                        "id": f"{movie.get('id')}"
                    },
                    {
                        "type": "single",
                        "source": "imdb",
                        "id": f"{movie.get('imdb_id')}"
                    }

                ],
                "externalKey" : f"{jellyfin_movie_id}",
                "externalSourceId": "Jellyfin",
                "externalSourceName": "Jellyfin",
                "externalSourceType": "jellyfin"
            }
        },

        "lineup": [
            {
                "persisted": True,
                "type": "content",
                "id": id,
                "duration": 1,
            }
        ]
    }

    #send program data to tunarr
    headers = { "Content-Type": "application/json" }
    response = requests.post(f"{TUNARR_API_URL}/channels/{id}/programming", json=program_data, headers=headers)
    response.raise_for_status()
    return response.json()    

# Create a Tunarr channel with the found movies.
def create_tunarr_channel(title):

    id = str(uuid.uuid4())
    endpoint = f"{TUNARR_API_URL}/channels"
    
    # Prepare the channel configuration
    channel_data = {
        "disableFillerOverlay": False,
        "duration": 0, # 24 hours in seconds
        "fillerCollections": [],
        "fillerRepeatCooldown": 30000,
        "groupTitle": f"Movies",
        "guideMinimumDuration": 30000, # 5 minutes
        "icon": {
            "duration": 0,
            "path": "",
            "position": "bottom-right",
            "width": 0
        },
        "id": id,
        "name": f"24/7 {title.upper()}",
        "number": len(requests.get(f"{TUNARR_API_URL}/channels").json()) + 1,
        "offline": {
            "mode": "pic" ,
            "picture": "",
            "soundtrack": ""
        },
        "onDemand": { "enabled": False },
        "programCount": 0,
        "startTime": int(round(time.time() * 1000)),
        "stealth": False,
        "streamMode": "hls",

        "transcoding": {
            "targetResolution": "global",
            "videoBitrate": "global",
            "videoBufferSize": "global"
        },

        "watermark": { 
            "animated": False,
            "duration": 0,
            "enabled": False, 
            "fixedSize": False,
            "horizontalMargin": 1,
            "opacity": 100,
            "position": "bottom-right",
            "url": "", 
            "verticalMargin": 1,
            "width": 10
        },

        "transcodeConfigId": "db1e3de8-6896-47b1-9c13-ca6309a191ea" #x265
    }
    
    headers = { "Content-Type": "application/json" }
    
    try:
        response = requests.post(endpoint, json=channel_data, headers=headers)  
        response.raise_for_status()
        print(f"\nSuccessfully created Tunarr channel '{channel_data['name']}'")
        return response.json(), id
    except requests.exceptions.RequestException as e:
        print(f"Tunarr API error: {e}")
        return None
    

if __name__ == "__main__":
    print("Starting...")

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Search and process movies by keyword')
    parser.add_argument('--keyword', '-k', type=str, help='Keyword to search for (use quotes for multiple words)')
    parser.add_argument('--max-results', '-m', type=int, default=50, help='Maximum number of movies to process')
    args = parser.parse_args()

    # Get keyword from command line or prompt
    keyword = args.keyword if args.keyword else input("Enter a keyword to search for: ")
    keyword_id, title = search_keyword_id(keyword)
    group_id = None

    if keyword_id:
        movies = get_movies_by_keyword(keyword_id, args.max_results)
        if movies:
            print(f"\nSelected keyword '{title.lower()}'")
                    
            # Create Tunarr channel with keyword
            if input("\nCreate a Tunarr channel with this keyword? (y/n): ").lower() == 'y':
                result = create_tunarr_channel(title)

            if input("\nCreate a jellyfin collection with this keyword? (y/n): ").lower() == 'y':              
               # Create a jellyfin collection with the keyword
                group_id =create_jellyfin_collection(title)

            if input(f"\nWould you like to add movies to real-debrid? ({len(movies)}) (y/n): ").lower() == 'y':

                for movie in movies:
                    torrent = search_1337x(movie.get('title') + " " + movie.get('release_date')[:4])
                    if torrent:
                        response, id = add_magnet_to_debrid(torrent['magnet'])
                        if response:
                            start_magnet_in_debrid(id)
                            print(f"- {movie.get('title')} (Id: {movie.get('id')} to real-debrid!)")
                    else:
                        # TODO: scrape a different site for the torrent
                        print(f"Failed to find torrent for {movie.get('title')}")   

                seconds = 20
                for i in range(seconds):
                    print(f"Wait for zurg reload... {i+1}/{seconds}")
                    time.sleep(1)

            if input("\nWould you like to add movies to a collection? (y/n): ").lower() == 'y':

                # Do a library scan to ensure the movies are added to the library
                do_library_scan()   

                seconds = 15
                # wait for the library to update
                for i in range(seconds):
                    print(f"Waiting for library to update... {i+1}/{seconds}")
                    time.sleep(1)
                    
               # Create a jellyfin collection with the keyword
                if not group_id:
                    group_id = create_jellyfin_collection(title)

                for movie in movies:
                    item_id, year = get_jellyfin_item(movie.get('title'))

                    if item_id:
                        add_item_to_collection(group_id, item_id)
                        print(f"- { movie.get('title') } ({year}) (Id: {item_id} added!)")
                        #add_movie_to_channel(movie, item_id)
        else:
            print(f"No movies found with keyword '{keyword}'.")
    else:
        print(f"Keyword '{keyword}' not found.")