# Standard library imports
import os
import re
import time

# Third-party imports
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

REAL_DEBRID_API_KEY = os.getenv('REAL_DEBRID_API_KEY')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Authorization': f'Bearer {REAL_DEBRID_API_KEY}'
}

def extract_hash_from_magnet(magnet):
    """Extract hash from magnet link."""
    hash_match = re.search(r'btih:([a-fA-F0-9]{40})', magnet)
    if hash_match:
        return hash_match.group(1).lower()
    return None    

def check_for_duplicate_hash(magnet_hash):
    """Check if a torrent with the given hash already exists in Debrid."""
    endpoint = "https://api.real-debrid.com/rest/1.0/torrents"
    response = requests.get(endpoint, headers=HEADERS)
    response.raise_for_status()

    torrents = response.json()
    if torrents:
        for torrent in torrents:
            # Compare hashes (case-insensitive)
            if torrent.get('hash', '').lower() == magnet_hash.lower():
                print(f"! Torrent already exists in real-debrid (Id: {torrent.get('id')})")
                return True
    return False

def add_magnet_to_debrid(magnet):
    """Add magnet to Debrid."""
    url = "https://api.real-debrid.com/rest/1.0/torrents/addMagnet"

    # Extract hash from magnet link
    magnet_hash = extract_hash_from_magnet(magnet)
    if not magnet_hash:
        print("✗ Invalid magnet link - could not extract hash!")
        return None, None

    # Check if torrent exists in Debrid
    if check_for_duplicate_hash(magnet_hash):
        return None, None

    # If not found, add the new magnet
    try:
        response = requests.post(url, headers=HEADERS, data={"magnet": magnet}, timeout=3)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 503:
            print("✗ Service unavailable (503). Please try again later.")
        else:
            print(f"✗ HTTP error occurred: {http_err}")
        return None, None
    except Exception as e:
        print(f"✗ Failed to add magnet: {e}")
        return None, None

    if response and response.status_code in [200, 201]:
        result = response.json()
        return result, result.get('id')

    return None, None

def start_magnet_in_debrid(id):
    """Start magnet in Debrid."""
    url = f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{id}"

    try:
        response = requests.post(url, headers=HEADERS, data={"files": "all"}, timeout=3)
        response.raise_for_status()
    except Exception as e:
        print(f"✗ Starting magnet in debrid failed: {e}")

def get_magnet_link(torrent_url):
    """Get magnet link from torrent URL."""
    response = requests.get(url=torrent_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    magnet_link = soup.find('a', href=re.compile(r'^magnet:'))['href']
    return magnet_link

def search_torrents(title: str):
    """Search for torrents across multiple sites."""
    from .torrent_manager import TorrentManager
    
    manager = TorrentManager()
    results = manager.search_all(title)
    return results