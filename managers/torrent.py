"""
Filename: torrent.py
Date: 02-17-2025
Author: robinbtw

Description:
This module provides classes to manage torrent searches across multiple sites.
It includes classes to represent search results, and a manager class to search across different torrent sites.
"""

# Import standard libraries
import re
import os
import unicodedata
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Import custom libraries
from managers.proxies import ProxyManager
MOVIE_QUALITY = "1080p" # 720p, 1080p, 2160p

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
        self.x1337_url = "https://1337x.to/search/{}/1/"
        self.yts_url = "https://yts.mx/api/v2/list_movies.json?query_term={}"
        self.lime_url = "https://limetorrent.net/search.php?catname=&q={}&orderby=DESC&order=seeders"
        self.tpb_url = "https://tpb.party/search/{}/1/99/0"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.quality = MOVIE_QUALITY
        self.proxy_manager = ProxyManager()

    def _make_request(self, method, url, is_json=False):
        """Internal helper function to make web requests."""
        try:
            proxy = self.proxy_manager.get_proxy()
            response = requests.request(method, url, headers=self.headers, timeout=8, proxies={'http': proxy })
            response.raise_for_status()
            return response.json() if is_json else response.text
        except requests.exceptions.RequestException as e:
            print(f"✗ Web request failed: {e}")
            return None

    def _get_magnet_link(self, torrent_url):
        """Get magnet link from torrent URL."""
        html = self._make_request('GET', torrent_url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            magnet_link = soup.find('a', href=re.compile(r'^magnet:'))
            return magnet_link['href'] if magnet_link else None   
        return None
    
    def search_tpb(self, query, limit=3):
        """Searches The Pirate Bay for torrents."""
        html = self._make_request('GET', self.tpb_url.format(query))
        return self._parse_tpb_results(html, limit) if html else []

    def _parse_tpb_results(self, html, limit):
        """Parses The Pirate Bay search results from HTML."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'id': 'searchResult'})
        if not table:
            return None
        
        # Find all rows in the search results table
        for row in table.find_all('tr')[1:8]:
            try:
                cells = row.find_all('td')
                if len(cells) < 6:  # Make sure we have enough cells
                    continue
                    
                # Name is in the 2nd td's first anchor tag
                name = cells[1].find('a').text.strip()
                name_lower = name.lower()
                
                # Magnet link is in the 4th td
                magnet = cells[3].find('a', href=re.compile(r'^magnet:'))
                if not magnet:
                    continue
                                    
                # Seeders is in the 6th td
                seeders = int(cells[5].text.strip())

                if (seeders >= 5 and 
                    self.quality in name_lower and 
                    "sample" not in name_lower and 
                    "hdts" not in name_lower and
                    "telesync" not in name_lower and 
                    "cam" not in name_lower):
                    
                    results.append(TorrentResult(
                        title=name,
                        seeders=seeders,
                        magnet=magnet['href'],
                        source="TPB"
                    ))
                    
            except (AttributeError, IndexError, ValueError) as e:
                continue
                    
        return results[:limit] if results else None

    def search_1337x(self, query, limit=3):
        """Searches 1337x.to for torrents."""
        html = self._make_request('GET', self.x1337_url.format(query))
        return self._parse_1337x_results(html, limit) if html else []

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
                    
            if (seeders >= 5 and 
                self.quality in name_lower 
                and "sample" not in name_lower and "hdts" not in name_lower
                and "telesync" not in name_lower and "cam" not in name_lower):

                torrent_href = "https://1337x.to" + row.find_all('td')[0].find_all('a')[-1]['href']
                potential_torrents.append((seeders, torrent_href, name))

        # Sort by seeders and take our limit
        if potential_torrents:
            top_torrents = sorted(potential_torrents, key=lambda x: x[0], reverse=True)[:limit]
            for torrent in top_torrents:
                magnet = self._get_magnet_link(torrent[1])
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
        json_response = self._make_request('GET', self.yts_url.format(query), is_json=True)
        return self._parse_yts_results(json_response, query, limit) if json_response else []

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
                potential_torrents = [t for t in torrents if t['quality'] == self.quality]
                
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
    
    def search_lime(self, query, limit=3):
        """Searches LimeTorrents for torrents."""
        html = self._make_request('GET', self.lime_url.format(query))
        return self._parse_lime_results(html, limit) if html else []

    def _parse_lime_results(self, html, limit):
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the table containing search results
        table = soup.find('table', class_='table2')
        if not table:
            return None
            
        for row in table.find_all('tr')[1:4]:
            try:
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue
                    
                name_elem = cells[0].find('a', class_='csprite_dl14')
                name = cells[0].find('div', class_='tt-name').text.strip().lower()
                link = name_elem['href']
                seeders = int(cells[3].text.strip())       
                name_lower = name.lower()

                if (seeders >= 5 and 
                    self.quality in name_lower 
                    and "sample" not in name_lower and "hdts" not in name_lower
                    and "telesync" not in name_lower and "cam" not in name_lower):
                    
                    magnet = self._get_magnet_link(link)
                    if magnet:
                        results.append(TorrentResult(
                            title=name,
                            seeders=seeders,
                            magnet=magnet,
                            source="LimeTorrents"
                        ))
            except (AttributeError, IndexError, ValueError):
                continue
                
        return results[:limit] if results else None
        
    def search_all_sites(self, query):
        """Searches all configured torrent sites and returns a sorted list of results."""
        # Normalize accented characters and clean query
        result = unicodedata.normalize('NFKD', query).encode('ASCII', 'ignore').decode('utf-8')
        result = re.sub(r'[^a-zA-Z0-9\s+]', '', result)
        result = result.replace(' ', '+')

        torrent_results = []
        for site in [self.search_1337x, self.search_lime, self.search_yts, self.search_tpb]:
            if site == self.search_tpb:
                result = result.replace('+', '%20')

            site_results = site(result)
            if site_results:
                torrent_results.extend(site_results)

        # Sort by seeders in descending order
        torrent_results.sort(key=lambda x: x.seeders, reverse=True)
        return torrent_results
