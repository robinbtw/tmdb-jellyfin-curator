"""
Movie automation script for TMDB, Real-Debrid, and Jellyfin integration.

This script allows you to search for movies by keyword or person on TMDB,
process them using torrent sites, add them to Real-Debrid, and organize
them in Jellyfin collections.

Author: robinbtw
Date: 02-17-2025
"""

# Standard library imports
import time
import argparse
import random
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Dict, Optional, Any

# Local imports
from managers.tmdb import TMDBManager
from managers.jellyfin import JellyfinManager
from managers.debrid import RealDebridManager
from managers.torrent import TorrentManager
from managers.tunarr import TunarrManager, TunnarEntry
from managers.proxies import ProxyManager

# Constants
GENRE_KEYWORDS = [
    "horror", "comedy", "drama", "adventure", "fantasy",
    "mystery", "crime", "thriller", "romance", "animation", 
    "documentary", "family", "western", "history", 
    "biography", "sport", "reality"
]

THEME_KEYWORDS = [
    "antihero", "female protagonist", "superhero", "mcu", 
    "disaster", "live action", "based on young adult novel",
    "based on video game", "based on comic", "based on novel", 
    "based on true story", "time travel", "space", "alien", 
    "zombie", "vampire", "werewolf", "robot", "dystopia",
    "post-apocalyptic", "heist", "con artist", "spy", 
    "mafia", "gangster", "interspecies romance",
]

# Default values
DEFAULT_MOVIE_LIMIT = 40
DEFAULT_WORKERS = 10

# Real-Debrid API rate limit
MAX_REAL_DEBRID_WORKERS = 1 

# Initialize service managers
g_tmdb = TMDBManager()
g_torrent = TorrentManager()
g_debrid = RealDebridManager()
g_jellyfin = JellyfinManager()
g_tunarr = TunarrManager()
g_proxies = ProxyManager()

# Custom exceptions
class MovieProcessingError(Exception):
    """Custom exception for movie processing errors."""
    pass

def show_spinner(message: str, delay: float = 0.1, iterations: int = 3) -> None:
    """Display an animated spinner with a message."""
    chars = ['|', '/', '-', '\\']
    iterations_per_cycle = len(chars)
    total_steps = iterations * iterations_per_cycle
    
    for i in range(total_steps):
        spin = chars[i % iterations_per_cycle]
        print(f"\r{message} {spin} ({i}/{total_steps})", end="", flush=True)
        time.sleep(delay)
    print()

# Core functionality class
class MovieProcessor:
    """Helper class to manage movie processing state and operations."""
    
    def __init__(self, movies: List[Dict[str, Any]], name: str, workers: int, is_person_search: bool):
        self.movies = movies
        self.name = name
        self.workers = workers
        self.collection_id = None
        self.is_person_search = is_person_search

    def process_debrid(self) -> int:
        """Process movies through Real-Debrid."""
        print("Adding movies to real-debrid...")
        successful = process_movies_parallel(self.movies, self.workers)
        print(f"\n✓ Processed {successful}/{len(self.movies)} movies successfully!")
        show_spinner("Waiting for zurg sync", delay=0.1, iterations=75)
        return successful

    def process_collection(self) -> Optional[str]:
        """Create and populate a Jellyfin collection."""
        self.collection_id = process_collection_creation(self.movies, self.name, self.workers)
        return self.collection_id

    def process_channel(self) -> None:
        """Create and populate a Tunarr channel."""
        g_tunarr.normalize_channels()
        channel_type = "Filmography" if self.is_person_search else "Movies"
        
        channel = g_tunarr.create_tunarr_channel(self.name, channel_type)
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [executor.submit(add_program, movie, channel) for movie in self.movies]
            concurrent.futures.wait(futures)
            successful = sum(1 for future in futures if future.result())
            print(f"\n✓ Added {successful}/{len(self.movies)} movies to Tunarr channel!")

# Search functions
def search_for_a_keyword(keyword: str, title: str = "") -> Tuple[Optional[int], Optional[str]]:
    """Search for a keyword on TMDB and return its ID and name."""
    results = g_tmdb.get_keyword(keyword).get("results", [])

    if not results:
        print("✗ No results found. Try:")
        print(f"`{random.choice(THEME_KEYWORDS)}`, `{random.choice(GENRE_KEYWORDS)}`")
        return None, None
  
    if title:
        try:
            return results[0].get("id"), title
        except Exception:
            return None, None

    print("\nFound these keyword matches:")
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

def search_for_a_person(person: str) -> Tuple[Optional[int], Optional[str]]:
    """Search for a person on TMDB and return their ID and name."""
    print(f"Searching for {person}...")
    results = g_tmdb.get_person(person).get("results", [])[:8] 
    if not results:
        return None, None

    print("Filtering out less popular people...")
    # Get movie count for each person
    people_with_counts = []
    for result in results:
        person_id = result.get("id")
        movie_credits = g_tmdb.get_movie_credits(person_id)
        movie_count = len(movie_credits.get("cast", []))
        people_with_counts.append((result, movie_count))
    print("Think we found our match!")

    # Sort by movie count and get the person with most movies
    top = sorted(people_with_counts, key=lambda x: x[1], reverse=True)
    return top[0][0].get("id"), top[0][0].get("name")

def get_movies_by_person(id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get movies by person ID from TMDB."""
    response = g_tmdb.get_movie_credits(id)
    credits = response.get("cast", [])
 
    # Sort all results by popularity before returning
    return sorted(credits[:limit], key=lambda x: x.get('popularity', 0), reverse=True)

def get_movies_by_keyword(id: int, limit: int) -> List[Dict[str, Any]]:
    """Get movies by keyword ID from TMDB."""
    results = []
    page = 1
    
    while True:
        response, _ = g_tmdb.get_movies_by_keyword(id, page=page)
        current_results = response.get("results", [])
        if not current_results:
            break
            
        results.extend(current_results)
        if len(results) >= limit:
            break
            
        page += 1
        if page > response.get("total_pages", 1):
            break

    return sorted(results[:limit], key=lambda x: x.get('popularity', 0),  reverse=True)

# Processing functions
def process_movie(movie: Dict[str, Any]) -> bool:
    """Process a movie by adding it to Real-Debrid."""
    title = movie.get("title")
    release_date = movie.get("release_date", "")[:4]
    search_term = f"{title} {release_date}"

    # Check if movie already exists in Jellyfin
    if g_jellyfin.get_movie(title):
        print(f"• Skipping {title} ({release_date}): already in jellyfin!")
        return True

    print(f"• Processing {title} ({release_date})...")
    torrents = g_torrent.search_all_sites(search_term)

    if not torrents:
        print(f"✗ Failed to process {title}: no torrents found!")
        return False

    for torrent in torrents:
        result, id = g_debrid.add_magnet_to_debrid(torrent.magnet)
        if result:
            g_debrid.start_magnet_in_debrid(id)
            print(f"✓ Added {title} ({release_date}) to debrid!")
            return True
    
    return False

def process_movies_parallel(movies: List[Dict[str, Any]], workers: int) -> int:
    """Process multiple movies in parallel using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=min(MAX_REAL_DEBRID_WORKERS, workers)) as executor:
        futures = [executor.submit(process_movie, movie) for movie in movies]
        concurrent.futures.wait(futures)
        return sum(1 for future in futures if future.result())

def process_collection_creation(movies: List[Dict[str, Any]], collection_name: str, workers: int) -> Optional[str]:
    """Create a Jellyfin collection and add movies to it."""
    id = g_jellyfin.create_collection(collection_name.lower())
    g_jellyfin.do_library_scan()
    show_spinner("Waiting for library to update", delay=0.1, iterations=50)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(add_movie_to_collection, movie, id) for movie in movies]
        concurrent.futures.wait(futures)
        successful = sum(1 for future in futures if future.result())
        print(f"\n✓ Added {successful}/{len(movies)} movies to collection successfully!")

    return id

def add_movie_to_collection(movie: Dict[str, Any], collection_id: str) -> bool:
    """Add a movie to a Jellyfin collection."""
    title = movie.get("title")
    year = movie.get("release_date", "")[:4]
    jellyfin_movie = g_jellyfin.get_movie(title)

    if jellyfin_movie:
        id = jellyfin_movie.get('Id')
        g_jellyfin.add_movie_to_collection(id, collection_id)
        print(f"✓ Added {title} {year} to collection!")
        return True
    
    print(f"✗ Failed to add {title} {year} to collection!")
    return False

def add_program(movie: Dict[str, Any], channel: Dict[str, Any]) -> bool:
    """Add a movie to Tunarr channel programming."""
    title = movie.get("title")

    # First check if movie already exists in channel programming
    programs = g_tunarr.get_channel_programs(channel['id'])

    if any(prog.get('title') == title for prog in programs):
        print(f"• Skipping {title}: already in channel programming")
        return True

    source = g_jellyfin.get_movie(title)
    if source:
        details = g_tmdb.get_movie_details(movie.get("id"))
        if details:
            g_tunarr.add_programming(channel['id'], TunnarEntry(details, source.get("Id")))
            print(f"✓ Added {movie.get('title')} to Tunarr channel!")
            return True
        
    print(f"✗ Failed to add {movie.get('title')} to Tunarr channel!")
    return False

def process_results(movies: List[Dict[str, Any]], name: str, args: argparse.Namespace) -> None:
    """Process movie search results based on user preferences."""
    processor = MovieProcessor(movies, name, args.workers, args.person is not None)

    if should_process_debrid(args, movies):
        processor.process_debrid()

    if should_add_to_collection(args):
        if not processor.collection_id:
            processor.process_collection()

    if should_create_channel(args, name):
        processor.process_channel()

# Cleanup functions
def delete_jellyfin_movie(movie: Dict[str, Any]) -> bool:
    """Delete a movie from Jellyfin."""
    id = movie.get('duplicate_id')
    name = movie.get('name')
    if g_jellyfin.delete_movie(id):
        print(f"✓ Deleted {name} from jellyfin!")
    return True

def delete_debrid_torrent(movie: Dict[str, Any]) -> bool:
    """Delete a movie from Real-Debrid."""
    id = movie.get('duplicate_id')
    name = movie.get('name')
    if g_debrid.delete_torrent(id):
        print(f"✓ Deleted {name} from real-debrid!")
    return True

def handle_cleanup(workers: int) -> None:
    """Clean up duplicate movies and torrents."""
    print("Cleaning up libraries...")

    # Clean up duplicate movies
    movies = g_jellyfin.get_all_duplicate_movies()
    if movies:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(delete_jellyfin_movie, movie) for movie in movies]
            concurrent.futures.wait(futures)
            successful = sum(1 for future in futures if future.result())
            print(f"✓ Deleted {successful}/{len(movies)} duplicate movies!")

    # Clean up duplicate torrents
    torrents = g_debrid.get_all_duplicate_torrents()
    if torrents:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(delete_debrid_torrent, torrent) for torrent in torrents]
            concurrent.futures.wait(futures)
            successful = sum(1 for future in futures if future.result())
            print(f"✓ Deleted {successful}/{len(torrents)} duplicate torrents!")

    print("Cleanup finished!")

# User interaction functions
def should_process_debrid(args: argparse.Namespace, movies: List[Dict[str, Any]]) -> bool:
    """Check if movies should be processed in Real-Debrid."""
    return args.bypass or input(f"\nAdd movies to real-debrid? ({len(movies)}) (y/n): ").lower() == 'y'

def should_add_to_collection(args: argparse.Namespace) -> bool:
    """Check if movies should be added to collection."""
    return args.bypass or input("\nAdd movies to the collection? (y/n): ").lower() == 'y'

def should_create_channel(args: argparse.Namespace, name: str) -> bool:
    """Check if Tunarr channel should be created."""
    return args.bypass or input(f"\nCreate a tunarr channel? ({name}) (y/n): ").lower() == 'y'

# CLI interface functions
def parse_arguments() -> argparse.Namespace:
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser(description="Search for movies by keyword or person!")

    # Search group
    search_group = parser.add_mutually_exclusive_group()
    search_group.add_argument("-k", "--keyword", type=str, help="Search for movies by keyword!")
    search_group.add_argument("-p", "--person", type=str, help="Search for movies by person!")

    # Processing options
    parser.add_argument("-l", "--limit", type=int, default=DEFAULT_MOVIE_LIMIT, help="Limit the number of movies to search for!")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help="Number of workers to use for processing!")
    
    # Action flags
    parser.add_argument("-b", "--bypass", action="store_true", help="Bypass all input prompts and default to 'yes'!")

    # Maintenance
    parser.add_argument("-c", "--cleanup", action="store_true", help="Cleanup libraries!")
    parser.add_argument("-t", "--test", action="store_true", help="Test proxy connections!")
    return parser.parse_args()

def handle_proxy_test() -> None:
    """Handle proxy testing."""
    working_count = g_proxies.test_proxies()
    if working_count == 0:
        print("✗ No working proxies found!")
    quit()

def get_movies_from_args(args: argparse.Namespace) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Get movies based on command line arguments."""

    try:
        if args.person:
            return get_movies_by_person_search(args.person, args.limit)
        else:
            return get_movies_by_keyword_search(args.keyword, args.limit)
    except Exception as e:
        print(f"✗ Error during movie search: {e}")
        return None, None

def get_movies_by_person_search(person: Optional[str], limit: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Search for movies by person name."""
    if not person:
        person = input("Enter a person to search for: ")
    
    person_id, name = search_for_a_person(person)
    if person_id:
        return get_movies_by_person(person_id, limit), name
    return None, None

def get_movies_by_keyword_search(keyword: Optional[str], limit: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Search for movies by keyword."""
    if not keyword:
        keyword = input("Enter a keyword to search for: ")
    
    keyword_id, name = search_for_a_keyword(keyword)
    if keyword_id:
        return get_movies_by_keyword(keyword_id, limit), name
    return None, None

# Main entry point
def main():
    """Main entry point for the movie automation script."""
    args = parse_arguments()
    
    try:
        if args.test:
            if g_proxies.test_proxies() == 0:
                print("✗ No working proxies found!")
            return
            
        if args.cleanup:
            handle_cleanup(args.workers)
            return
            
        # Handle movie search and processing
        movies, name = get_movies_from_args(args)
        if not movies:
            print("✗ Error: No movies found, quitting program!")
            return

        process_results(movies, name, args)
        
    except MovieProcessingError as e:
        print(f"✗ Error during processing: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    main()




