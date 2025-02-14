"""
Filename: main.py
Date: 2023-10-05
Author: robinbtw

Description:
This script allows you to search for movies by keyword or person on TMDB, process them using torrent sites,
add them to Real-Debrid, and add them to a Jellyfin collection.
"""

# Import standard libraries
import time
import argparse
import random
import concurrent.futures

# Import managers
from managers.tmdb import TMDBManager
from managers.jellyfin import JellyfinManager
from managers.debrid import RealDebridManager
from managers.torrent import TorrentManager

# Define generic keywords
g_generic_keywords = [
    "horror", "comedy", 
    "drama", "adventure", "fantasy",
    "mystery", "crime", "thriller", "romance",
    "animation", "documentary", "family", "horror", "western", "war",
    "history", "biography", "sport", "reality"]

# Define specific keywords
g_specific_keywords  = [
    "antihero", "female protagonist", "superhero", 
    "mcu", "disaster", "live action", "based on young adult novel",
    "based on video game"]

# Initialize managers
g_tmdb = TMDBManager()
g_torrent = TorrentManager()
g_debrid = RealDebridManager()
g_jellyfin = JellyfinManager()

def search_for_a_keyword(keyword, title=""):
    """Search for a keyword on TMDB and return the ID and name."""
    results = g_tmdb.get_keyword(keyword).get("results", [])

    if not results:
        print("No results found. Try:")
        print(f"`{random.choice(g_specific_keywords)}`, `{random.choice(g_generic_keywords)}`")
        quit()

    print("Found these keyword matches:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('name')}")

    while True:
        try:
            choice = int(input(f"\nSelect a keyword (1-{len(results)}): "))
            if 1 <= choice <= len(results):
                return results[choice-1].get("id"), results[choice-1].get("name") or title
            print("Please enter a valid number.")
        except ValueError:
            print("Please enter a valid number.")

def get_movies_by_person(id, limit=50):
    """Get movies by person ID from TMDB."""
    response = g_tmdb.get_combined_credits(id)
    credits = response.get("cast", [])

    # Get only movies
    movies = [credit for credit in credits if credit.get("media_type") == "movie"]
 
    # Sort by vote average and return top movies
    return sorted(movies, key=lambda x: x.get('vote_average', 0), reverse=True)[:limit]
    
def get_movies_by_keyword(id, limit=50):
    """Get movies by keyword ID from TMDB."""
    results = []
    response, params = g_tmdb.get_movies_by_keyword(id)

    pages = response.get("total_pages", 1) # Get total pages
    results.extend(response.get("results", [])) # Get first page results

    for page in range(2, pages + 1):
        params["page"] = page
        response = g_tmdb.get_movies_by_keyword(id, page=page)
        results.extend(response.get("results", [])) # Append results from next pages

        if len(results) >= limit:
            return sorted(results[:limit], key=lambda x: x.get('vote_average', 0), reverse=True)

    # Sort all results by vote average before returning
    return sorted(results, key=lambda x: x.get('vote_average', 0), reverse=True)

def process_movie_parallel(movie):
    """Process a movie in parallel by adding it to real-debrid."""
    title = movie.get("title")
    release_date = movie.get("release_date")[:4]
    search_term = f"{title} {release_date}"

    print(f"Processing {title} {release_date}...")
    torrents = g_torrent.search_all_sites(search_term)

    if torrents:
        for torrent in torrents:
            magnet = torrent.magnet
            result = g_debrid.add_magnet_to_debrid(magnet)
            if result:
                print(f"✓ Added {title} {release_date} to debrid!")
                return True
    else:
        print(f"✗ Failed to proccess {title}")
        return False
    
def add_movie_to_collection_parallel(movie, collection_id):
    """Add a movie to a jellyfin collection in parallel."""
    title = movie.get("title")
    year = movie.get("release_date")[:4]
    movie_id = g_jellyfin.get_jellyfin_movie(title)

    if movie_id:
        g_jellyfin.add_movie_to_collection(movie_id, collection_id)
        print(f"✓ Added {title} {year} to collection!")
        return True
    
    print(f"✗ Failed to add {title} {year} to collection!")
    return False

def waiting_animation_spinner(message="Processing", delay=0.1, iterations=3):
    """Display a waiting animation with a spinning cursor."""
    spinner = ['|', '/', '-', '\\']
    iterations_per_cycle = len(spinner)
    
    for i in range(iterations * iterations_per_cycle):
        spin = spinner[i % iterations_per_cycle]
        print(f"\r{message} {spin} ({i}/{iterations * iterations_per_cycle})", end="", flush=True)
        time.sleep(delay)

    print()

def main():
    movies = None
    group_id = None

    # Set up argumaent parser
    parser = argparse.ArgumentParser(description="Search for movies by keyword or person!")
    parser.add_argument("-k", "--keyword", type=str, help="Search for movies by keyword!")
    parser.add_argument("-p", "--person", type=str, help="Search for movies by person!")
    parser.add_argument("-l", "--limit", type=int, default=50, help="Limit the number of movies to search for!")

    # Warning: Increasing workers may cause rate limiting on some APIs
    parser.add_argument("-w", "--workers", type=int, default=1, help="Number of workers to use for processing!")
    args = parser.parse_args()

    if args.person:
        movies = get_movies_by_person(args.person, args.limit)
    else:
        keyword = args.keyword if args.keyword else input("Enter a keyword to search for: ")
        keyword_id, name = search_for_a_keyword(keyword)

        if keyword_id:
            movies = get_movies_by_keyword(keyword_id, args.limit)

    if movies:

        if input("\nCreate a jellyfin collection with this collection? (y/n): ").lower() == 'y':
            group_id = g_jellyfin.create_jellyfin_collection(name)

        if input(f"\nWould you like to add movies to real-debrid? ({len(movies)}) (y/n): ").lower() == 'y':

            # Process movies in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(process_movie_parallel, movie) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"\nProcessed {successful}/{len(movies)} movies successfully")

        if input("\nWould you like to add movies to a collection? (y/n): ").lower() == 'y':

            # Do a library scan to ensure the movies are added to the library
            g_jellyfin.do_library_scan()   

            # wait for the library to update
            waiting_animation_spinner(f"Waiting for library to update", delay=0.1, iterations=50) 

            # Create a jellyfin collection with the keyword if not already created
            if not group_id:
                group_id = g_jellyfin.create_jellyfin_collection(name)        

                        # Add movies to collection in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(add_movie_to_collection_parallel, movie, group_id) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"\nAdded {successful}/{len(movies)} movies to collection successfully")
    else:
        print("✗ Error: No movies found quiting program!")
        quit()          
        
if __name__ == "__main__":
    main()