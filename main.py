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
from managers.tunarr import TunarrManager, TunnarEntry

# Generic movie keywords
g_generic_keywords = [
    "horror", "comedy", 
    "drama", "adventure", "fantasy",
    "mystery", "crime", "thriller", "romance",
    "animation", "documentary", "family", "horror", "western", "war",
    "history", "biography", "sport", "reality"
]

# Specific movie keywords
g_specific_keywords = [
    "antihero", "female protagonist", "superhero", 
    "mcu", "disaster", "live action", "based on young adult novel",
    "based on video game", "based on comic", "based on novel", "based on true story",
    "time travel", "space", "alien", "zombie", "vampire", "werewolf", "robot", "dystopia",
    "post-apocalyptic", "heist", "con artist", "spy", "mafia", "gangster", "interspecies romance",
]

# Initialize managers
g_tmdb = TMDBManager()
g_torrent = TorrentManager()
g_debrid = RealDebridManager()
g_jellyfin = JellyfinManager()
g_tunarr = TunarrManager()

def search_for_a_keyword(keyword, title=""):
    """Search for a keyword on TMDB and return the ID and name."""
    results = g_tmdb.get_keyword(keyword).get("results", [])

    if not results:
        print("✗ No results found. Try:")
        print(f"`{random.choice(g_specific_keywords)}`, `{random.choice(g_generic_keywords)}`")
        return None, None
  
    try:
        if title:
            return results[0].get("id"), title
    except Exception as e:
        return None, None

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

def search_for_a_person(person):
    """Search for a person on TMDB and return the ID and name."""
    print(f"Searching for {person}...")
    results = g_tmdb.get_person(person).get("results", [])[:8] 
    if not results:
        return None, None

    print("Getting most popular person...")
    # Get movie count for each person
    people_with_counts = []
    for result in results:
        person_id = result.get("id")
        movie_credits = g_tmdb.get_movie_credits(person_id)
        movie_count = len(movie_credits.get("cast", []))
        people_with_counts.append((result, movie_count))

    # Sort by movie count and get the person with most movies
    top = sorted(people_with_counts, key=lambda x: x[1], reverse=True)
    return top[0][0].get("id"), top[0][0].get("name")

def get_movies_by_person(id, limit=50):
    """Get movies by person ID from TMDB."""
    response = g_tmdb.get_movie_credits(id)
    credits = response.get("cast", [])
 
    # Sort all results by popularity before returning
    return sorted(credits[:limit], key=lambda x: x.get('popularity', 0), reverse=True)

def get_movies_by_keyword(id, limit=50):
    """Get movies by keyword ID from TMDB."""
    results = []
    response, params = g_tmdb.get_movies_by_keyword(id)

    pages = response.get("total_pages", 1) # Get total pages
    results.extend(response.get("results", [])) # Get first page results

    for page in range(2, pages + 1):
        params["page"] = page
        response, *_ = g_tmdb.get_movies_by_keyword(id, page=page)
        results.extend(response.get("results", [])) # Append results from next pages

        if len(results) >= limit:
            return sorted(results[:limit], key=lambda x: x.get('popularity', 0), reverse=True)

    # Sort all results by popularity before returning
    return sorted(results, key=lambda x: x.get('popularity', 0), reverse=True)

def process_movie_parallel(movie):
    """Process a movie in parallel by adding it to real-debrid."""
    title = movie.get("title")
    release_date = movie.get("release_date")[:4]
    search_term = f"{title} {release_date}"

    print(f"• Processing {title} ({release_date})...")
    torrents = g_torrent.search_all_sites(search_term)

    if torrents:
        for torrent in torrents:
            magnet = torrent.magnet
            result, id = g_debrid.add_magnet_to_debrid(magnet)
            if result:
                g_debrid.start_magnet_in_debrid(id)
                print(f"✓ Added {title} ({release_date}) to debrid!")
                return True
    else:
        print(f"✗ Failed to proccess {title}: no torrents found!")
        return False
    
def add_movie_to_collection_parallel(movie, collection_id):
    """Add a movie to a jellyfin collection in parallel."""
    title = movie.get("title")
    year = movie.get("release_date")[:4]
    jellyfin_movie = g_jellyfin.get_movie(title)

    if jellyfin_movie:
        id = jellyfin_movie.get('Id')
        g_jellyfin.add_movie_to_collection(id, collection_id)
        print(f"✓ Added {title} {year} to collection!")
        return True
    
    print(f"✗ Failed to add {title} {year} to collection!")
    return False

def add_program_parallel(movie, channel):
    """Add a movie to Tunarr channel programming in parallel."""
    source = g_jellyfin.get_movie(movie.get("title"))
    if source:
        details = g_tmdb.get_movie_details(movie.get("id"))
        if details:
            g_tunarr.add_programming(channel['id'], TunnarEntry(details, source.get("Id")))
            print(f"✓ Added {movie.get('title')} to Tunarr channel!")
            return True
    print(f"✗ Failed to add {movie.get('title')} to Tunarr channel!")
    return False

def delete_jellyfin_movie_parallel(movie):
    """Delete a movie from Jellyfin in parallel."""
    id = movie.get('duplicate_id')
    name = movie.get('name')
    if g_jellyfin.delete_movie(id):
        print(f"✓ Deleted {name} from jellyfin!")
    return True

def delete_debrid_torrent_parallel(movie):
    """Delete a movie from Real-Debrid in parallel."""
    id = movie.get('duplicate_id')
    name = movie.get('name')
    if g_debrid.delete_torrent(id):
        print(f"✓ Deleted {name} from real-debrid!")
    return True

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
    name = None
    movies = None
    group_id = None
    person_id = None

    # Set up argumaent parser
    parser = argparse.ArgumentParser(description="Search for movies by keyword or person!")
    parser.add_argument("-k", "--keyword", type=str, help="Search for movies by keyword!")
    parser.add_argument("-p", "--person", type=str, help="Search for movies by person!")
    parser.add_argument("-l", "--limit", type=int, default=50, help="Limit the number of movies to search for!")
    parser.add_argument("-b", "--bypass", action="store_true", help="Bypass all input prompts and default to 'yes'")
    parser.add_argument("-c", "--cleanup", action="store_true", help="Cleanup libraries!")

    # Warning: Increasing workers may cause rate limiting on some APIs
    parser.add_argument("-w", "--workers", type=int, default=3, help="Number of workers to use for processing!")
    args = parser.parse_args()

    if args.cleanup:
        print("Cleaning up libraries...")

        movies = g_jellyfin.get_all_duplicate_movies()
        if len(movies) > 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(delete_jellyfin_movie_parallel, movie) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"✓ Deleted {successful}/{len(movies)} movies successfully!")

        torrents = g_debrid.get_all_duplicate_torrents()
        if len(torrents) > 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(delete_debrid_torrent_parallel, torrent) for torrent in torrents]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"✓ Deleted {successful}/{len(torrents)} torrents successfully!")

        print("Cleaning session finished!")
        quit()
        
    if args.person:
        person_id, name = search_for_a_person(args.person)
        if person_id:
            movies = get_movies_by_person(person_id, args.limit)
    else:
        keyword = args.keyword if args.keyword else input("Enter a keyword to search for: ")
        keyword_id, name = search_for_a_keyword(keyword)

        if keyword_id:
            movies = get_movies_by_keyword(keyword_id, args.limit)

    if movies:

        if args.bypass or input(f"\nCreate a jellyfin collection for {name.lower()}? (y/n): ").lower() == 'y':
            group_id = g_jellyfin.create_collection(name.lower())

        if args.bypass or input(f"\nWould you like to add movies to real-debrid? ({len(movies)}) (y/n): ").lower() == 'y':
            print("Adding movies to real-debrid...")
            # Process movies in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(process_movie_parallel, movie) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"\n✓ Processed {successful}/{len(movies)} movies successfully!")

            # Wait for zurg to refresh/sync movies
            waiting_animation_spinner(f"Waiting for zurg sync", delay=0.1, iterations=75)

        if args.bypass or input(f"\nWould you like to add movies to the collection? (y/n): ").lower() == 'y':

            # Do a library scan to ensure the movies are added to the library
            g_jellyfin.do_library_scan()   

            # wait for the library to update
            waiting_animation_spinner(f"Waiting for library to update", delay=0.1, iterations=50) 

            # Create a jellyfin collection with the keyword if not already created
            if not group_id:
                group_id = g_jellyfin.create_collection(name.lower())        

            # Add movies to collection in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(add_movie_to_collection_parallel, movie, group_id) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"\n✓ Added {successful}/{len(movies)} movies to collection successfully!")

        if args.bypass or input(f"\nCreate a tunarr channel for movies? ({name}) (y/n): ").lower() == 'y':
            # Normalize channel numbers
            g_tunarr.normalize_channels() 
            # Create a tunarr channel for the keyword
            channel = g_tunarr.create_tunarr_channel(name, "Filmography" if person_id else "Movies")

            # Process programming additions in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = [executor.submit(add_program_parallel, movie, channel) for movie in movies]
                
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
                successful = sum(1 for future in futures if future.result())
                print(f"\n✓ Added {successful}/{len(movies)} movies to Tunarr channel successfully!")
        
    else:
        print("✗ Error: No movies found quiting program!")
        quit()      
        
if __name__ == "__main__":
    main()