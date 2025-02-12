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

def make_request(url, method="get", headers=None, data=None, timeout=10):
    """Make a request to the specified URL with optional headers and data."""

    try:
        if method == "get":
            response = requests.get(url, headers=headers or HEADERS, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, data=data, timeout=timeout)
        return response
    except requests.Timeout:
        print(f"✗ Request to {url} timed out after {timeout} seconds")
        return None
    except requests.RequestException as e:
        print(f"✗ Request failed: {e}")
        return None

def add_magnet_to_debrid(magnet):
    """Add magnet to Debrid."""
    url = "https://api.real-debrid.com/rest/1.0/torrents/addMagnet"

    try:
        response = make_request(url, method="post", headers=HEADERS, data={"magnet": magnet}, timeout=3)
        if response and response.status_code in [200, 201]:
            result = response.json()
            return result, result.get('id')
        else:
            print(f"✗ Failed to add magnet: {response.status_code if response else 'no response'}")
            return None, None

    except Exception as e:
        print(f"✗ No response from debrid for adding magnet: {e}")
        return None, None

def start_magnet_in_debrid(id):
    """Start magnet in Debrid."""
    url = f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{id}"

    try:
        response = make_request(url, method="post", headers=HEADERS, data={"files": "all"}, timeout=3)
        response.raise_for_status()
    except Exception as e:
        print(f"✗ Starting magnet in debrid failed: {e}")

def get_magnet_link(torrent_url):
    """Get magnet link from torrent URL."""
    response = make_request(torrent_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    magnet_link = soup.find('a', href=re.compile(r'^magnet:'))['href']
    return magnet_link

def search_1337x(title):
    """Search 1337x for a torrent."""
    print(f"Searching for {title} on 1337x")
    search_query = title.replace(' ', '+')

    # Use HTTPS and the main domain
    domain = "https://1337x.to"
    url = f"{domain}/search/{search_query}/1/"

    try:
        response = make_request(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table containing torrents
        tbody = soup.find('tbody')
        if not tbody:
            print(f"✗ No results found for {title} on 1337x")
            return None

        torrent_rows = tbody.find_all('tr')
        if not torrent_rows:
            print("✗ No torrent rows found")
            return None

        # First filter and sort by seeders before getting magnet links
        potential_torrents = []

        for row in torrent_rows[:10]:  # Check first 10 results
            try:
                name = row.find_all('td')[0].find_all('a')[-1].text
                seeders = int(row.find_all('td')[1].text)

                # Check for desired quality and exclude unwanted releases
                name_lower = name.lower()
                if (seeders >= 5 and  # Minimum seeders
                    ("1080p" in name_lower or "bluray" in name_lower) and # Quality check
                    "sample" not in name_lower and # Exclude samples
                    "telesync" not in name_lower and "cam" not in name_lower): # Exclude telesyncs and cams

                    torrent_href = domain + row.find_all('td')[0].find_all('a')[-1]['href']
                    potential_torrents.append((seeders, torrent_href, name))
            except (IndexError, ValueError) as e:
                print(f"✗ Error parsing row: {e}")
                continue

        if potential_torrents:
            best_torrent = sorted(potential_torrents, reverse=True)[0]
            magnet = get_magnet_link(best_torrent[1])

            result = {
                'name': best_torrent[2],
                'seeders': best_torrent[0],
                'magnet': magnet
            }
            return result
        else:
            print("✗ No suitable torrents found")

    except Exception as e:
        print(f"✗ Error searching 1337x: {e}")
        return None

    return None