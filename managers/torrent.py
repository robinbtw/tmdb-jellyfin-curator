"""
Filename: torrent.py
Date: 2023-10-05
Author: robinbtw

Description:
This module provides classes to manage torrent searches across multiple sites.
It includes classes to represent search results, and a manager class to search across different torrent sites.
"""

# Import standard libraries
import re
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

class TorrentResult:
    """A class to represent a torrent search result."""
    def __init__(self, title, magnet, seeders, source):
        self.title = title
        self.magnet = magnet
        self.seeders = seeders
        self.source = source

    def __repr__(self):
        return f"TorrentResult(title='{self.title}', seeders={self.seeders}, magnet={self.magnet}, site='{self.source}')"

class TorrentManager:
    """A class to manage searching for torrents across multiple sites."""

    def __init__(self):
        """Initializes the TorrentManager."""
        self.nyaa_url = "https://nyaa.si/?f=0&c=1_0&q={}&s=seeders&o=desc" 
        self.x1337_url = "https://1337x.to/search/{}/1/"
        self.yts_url = "https://yts.mx/api/v2/list_movies.json?query_term={}"
        self.headers = {'User-Agent': 'Mozilla/5.0'}  # Some sites require a User-Agent

    def get_magnet_link(self, torrent_url):
        """Get magnet link from torrent URL."""
        response = requests.get(url=torrent_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        magnet_link = soup.find('a', href=re.compile(r'^magnet:'))['href']
        return magnet_link

    def search_nyaa(self, query, limit=3):
        """Searches Nyaa.si for torrents."""
        try:
            url = self.nyaa_url.format(query)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            # Parse the HTML content
            results = self._parse_nyaa_results(response.text, query, limit)
            return results
        except requests.exceptions.RequestException as e:
            print(f"✗ Nyaa search failed: {e}")
            return []

    def _parse_nyaa_results(self, html, query, limit):
        """Parses Nyaa.si search results from HTML."""
        name = query.replace('+', ' ')

        results = []
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'class': 'torrent-list'})
        if not table:
            return None

        potential_torrents = []
        # Skip header row and limit to 10 results
        for row in table.find_all('tr')[:10]:  
            try:
                # Find all links in the second column (td[1])
                links = row.find_all('td')[1].find_all('a')

                # Get the first link that is not a comment link
                for link in links:
                    if not link.has_attr('class') or 'comments' not in link.get('class', []):
                        break
        
                seeders = int(row.find_all('td')[5].text)      
                name_lower = link.text.lower();

                # Check for 1080p or bluray, and exclude samples, telesync, and cam
                if (seeders >= 5 and "1080p" in name_lower and
                    "sample" not in name_lower and
                    "telesync" not in name_lower and "cam" not in name_lower):

                    torrent_href = "https://nyaa.si" + row.find_all('td')[1].find('a')['href']
                    potential_torrents.append((seeders, torrent_href, name))
            except (IndexError, ValueError):
                continue

        if potential_torrents:
            # Sort by seeders and take our limit
            # print(f"✓ Found {len(potential_torrents)} torrents on Nyaa!")
            top_torrents = sorted(potential_torrents, key=lambda x: x[0], reverse=True)[:limit]
            for torrent in top_torrents:
                magnet = self.get_magnet_link(torrent[1])
                if magnet:
                    results.append(TorrentResult(
                        title=torrent[2],
                        seeders=torrent[0],
                        magnet=magnet,
                        source="Nyaa"
                    ))

        if results:
            return results
        else:
            # print("✗ No torrents found on Nyaa")
            return None

    def search_1337x(self, query, limit=3):
        """Searches 1337x.to for torrents."""

        try:
            url = self.x1337_url.format(query)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            # Parse the HTML content
            results = self._parse_1337x_results(response.text, limit)
            return results
        except requests.exceptions.RequestException as e:
            print(f"✗ 1337x search failed: {e}")
            return []

    def _parse_1337x_results(self, html, limit):
        """Parses 1337x.to search results from HTML."""

        results = []
        soup = BeautifulSoup(html, 'html.parser')
        tbody = soup.find('tbody')
        if not tbody:
            return None

        potential_torrents = []
        for row in tbody.find_all('tr')[:10]:

            name = row.find_all('td')[0].find_all('a')[-1].text
            seeders = int(row.find_all('td')[1].text)       
            name_lower = name.lower()

            if (seeders >= 5 and "1080p" in name_lower and
                "sample" not in name_lower and
                "telesync" not in name_lower and "cam" not in name_lower):
  
                torrent_href = "https://1337x.to" + row.find_all('td')[0].find_all('a')[-1]['href']
                potential_torrents.append((seeders, torrent_href, name))

        # Sort by seeders and take our limit
        if potential_torrents:
            top_torrents = sorted(potential_torrents, key=lambda x: x[0], reverse=True)[:limit]
            # print(f"✓ Found {len(top_torrents)} torrents on 1337x!")
            for torrent in top_torrents:
                magnet = self.get_magnet_link(torrent[1])
                if True:
                    results.append(TorrentResult(
                        title=torrent[2],
                        seeders=torrent[0],
                        magnet=magnet,
                        source="1337x"
                    ))

        if results:
            return results
        else:
            # print("✗ No torrents found on 1337x")
            return None

    def search_yts(self, query, limit=3):
        """Searches YTS.mx for torrents."""
        try:
            url = self.yts_url.format(query)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            # Parse the HTML content
            results = self._parse_yts_results(response.json(), query, limit)
            return results
        except requests.exceptions.RequestException as e:
            print(f"✗ YTS search failed: {e}")
            return []

    def _parse_yts_results(self, json, query, limit):
        """Parses YTS.mx search results from HTML."""
        name = query.replace('+', ' ')

        results = []
        # Check if the response has the expected structure
        if not json.get('status') == 'ok':
            print("✗ YTS API returned invalid response")
            return None
        
        movies = json.get('data', {}).get('movies', [])
        if not movies:
            return None
        
        # Find the best matching movie
        for movie in movies:
            movie_title = movie['title'].lower()

            # Check if the movie title matches the query
            if movie_title == name.lower() or movie_title in name.lower():
                torrents = movie.get('torrents', [])
                
                # Get all 1080p torrents
                potential_torrents = [t for t in torrents if t['quality'] == '1080p']
                
                # print(f"✓ Found {len(potential_torrents)} torrents on YTS!")
                for torrent in potential_torrents:
                    hash = torrent.get('hash')
                    if hash:
                        # Construct magnet link
                        magnet = (
                            f"magnet:?xt=urn:btih:{hash}"
                            f"&dn={requests.utils.quote(movie['title'])}"
                            "&tr=udp://open.demonii.com:1337/announce"
                            "&tr=udp://tracker.openbittorrent.com:80"
                            "&tr=udp://tracker.coppersurfer.tk:6969"
                            "&tr=udp://glotorrents.pw:6969/announce"
                            "&tr=udp://tracker.opentrackr.org:1337/announce"
                            "&tr=udp://torrent.gresille.org:80/announce"
                            "&tr=udp://p4p.arenabg.com:1337"
                            "&tr=udp://tracker.leechers-paradise.org:6969"
                        )
                        
                        results.append(TorrentResult(
                            title=f"{movie['title']}",
                            seeders=torrent.get('seeds', 0),
                            magnet=magnet,
                            source="YTS"
                        ))

        if results:
            return results
        else:
            # print("✗ No torrents found on YTS")
            return None
        
    def search_all_sites(self, query):
        """Searches all configured torrent sites and returns a sorted list of results."""
        # Clean query: remove special characters except '+', convert to lowercase
        result = re.sub(r'[^a-zA-Z0-9\s+]', '', query)
        result = result.replace(' ', '+')

        torrent_results = []
        for site in [self.search_1337x, self.search_yts]:
            # print(f"Searching on {site.__name__.split('_')[1]}...")
            site_results = site(result)
            if site_results:
                torrent_results.extend(site_results)

        # Sort by seeders in descending order
        torrent_results.sort(key=lambda x: x.seeders, reverse=True)
        return torrent_results
