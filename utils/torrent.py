import requests
from bs4 import BeautifulSoup
import re
import time
import random
import os
from dotenv import load_dotenv

load_dotenv()

REAL_DEBRID_API_KEY = os.getenv('REAL_DEBRID_API_KEY')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# Rate-limited request function
def rate_limited_request(url, method="get", headers=None, data=None):
    time.sleep(random.uniform(1, 5))  # Random delay between requests
    if method == "get":
        return requests.get(url, headers=headers or HEADERS)
    return requests.post(url, headers=headers, data=data)

# Add magnet to Debrid
def add_magnet_to_debrid(magnet):
    url = "https://api.real-debrid.com/rest/1.0/torrents/addMagnet"
    headers = {"Authorization": f"Bearer {REAL_DEBRID_API_KEY}", "Content-Type": "application/json"}
    
    max_retries = 3
    retry_delay = 15  # seconds
    
    for attempt in range(max_retries):
        try:
            response = rate_limited_request(url, method="post", headers=headers, data={"magnet": magnet})
            response.raise_for_status()
            return response.json(), response.json()['id']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    print(f"Got 503 error, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue

    print("Skipping this magnet to debrid, too many retries")               
    return None, None

# Start magnet in Debrid
def start_magnet_in_debrid(id):
    url = f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{id}"
    headers = {"Authorization": f"Bearer {REAL_DEBRID_API_KEY}", "Content-Type": "application/json"}
    
    max_retries = 3
    retry_delay = 15  # seconds
    
    for attempt in range(max_retries):
        try:
            response = rate_limited_request(url, method="post", headers=headers, data={"files": "all"})
            response.raise_for_status()
            return
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    print(f"Got 503 error, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                    
    print("Failed to start magnet in debrid after max retries")

# Get magnet link from torrent URL
def get_magnet_link(torrent_url):
    response = rate_limited_request(torrent_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    magnet_link = soup.find('a', href=re.compile(r'^magnet:'))['href']
    return magnet_link

# Search 1337x for a torrent
def search_1337x(title):
    print(f"Searching for {title} on 1337x...")
    search_query = title.replace(' ', '+')

    # Use HTTPS and the main domain
    domain = "https://1337x.to"
    url = f"{domain}/search/{search_query}/1/"

    try:
        response = rate_limited_request(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing torrents
        tbody = soup.find('tbody')
        if not tbody:
            print("No results found on 1337x")
            return None
            
        torrent_rows = tbody.find_all('tr')
        if not torrent_rows:
            print("No torrent rows found")
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
                print(f"Error parsing row: {e}")
                continue
        
        if potential_torrents:
            best_torrent = sorted(potential_torrents, reverse=True)[0]
            magnet = get_magnet_link(best_torrent[1])
            
            return {
                'name': best_torrent[2],
                'seeders': best_torrent[0],
                'magnet': magnet
            }
        else:
            print("No suitable torrents found")

    except Exception as e:
        print(f"Error searching 1337x: {e}")
        return None

    return None