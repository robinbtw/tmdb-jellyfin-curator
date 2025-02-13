from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import re
from bs4 import BeautifulSoup
import requests

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

@dataclass
class TorrentResult:
    name: str
    seeders: int
    magnet: str
    source: str

class TorrentSite(ABC):
    @abstractmethod
    def search(self, title: str) -> Optional[TorrentResult]:
        pass

    def get_magnet_link(self, torrent_url: str) -> Optional[str]:
        response = requests.get(url=torrent_url, headers=HEADERS)
        if not response:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        magnet_link = soup.find('a', href=re.compile(r'^magnet:'))
        return magnet_link['href'] if magnet_link else None
    
class SiteNyaa(TorrentSite):
    def search(self, title: str) -> Optional[TorrentResult]:
        #print(f"Searching for {title} on Nyaa")
        search_query = title.replace(' ', '+')
        url = f"https://nyaa.si/?f=0&c=0_0&q={search_query}&s=seeders&o=desc"

        try:
            response = requests.get(url, headers=HEADERS)
            if not response:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
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
                    name = None
                    for link in links:
                        if not link.has_attr('class') or 'comments' not in link.get('class', []):
                            name = link.text
                            break
          
                    seeders = int(row.find_all('td')[5].text)      
                    name_lower = name.lower()

                    if (seeders >= 5 and
                        ("1080p" in name_lower or "bluray" in name_lower) and
                        "sample" not in name_lower and
                        "telesync" not in name_lower and "cam" not in name_lower):

                        torrent_href = "https://nyaa.si" + row.find_all('td')[1].find('a')['href']
                        potential_torrents.append((seeders, torrent_href, name))
                except (IndexError, ValueError):
                    continue

            if potential_torrents:
                best_torrent = sorted(potential_torrents, reverse=True)[0]
                magnet = self.get_magnet_link(best_torrent[1])
                if magnet:
                    return TorrentResult(
                        name=best_torrent[2],
                        seeders=best_torrent[0],
                        magnet=magnet,
                        source="Nyaa"
                    )
        except Exception as e:
            print(f"✗ Error searching Nyaa: {e}")

        print("✗ No torrents found on Nyaa")
        return None

class Site1337x(TorrentSite):
    def search(self, title: str) -> Optional[TorrentResult]:
        #print(f"Searching for {title} on 1337x")
        search_query = title.replace(' ', '+')
        domain = "https://1337x.to"
        url = f"{domain}/search/{search_query}/1/"

        try:
            response = requests.get(url, headers=HEADERS)
            if not response:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tbody = soup.find('tbody')
            if not tbody:
                return None

            potential_torrents = []
            for row in tbody.find_all('tr')[:10]:
                try:
                    name = row.find_all('td')[0].find_all('a')[-1].text
                    seeders = int(row.find_all('td')[1].text)
                    
                    name_lower = name.lower()
                    if (seeders >= 5 and
                        ("1080p" in name_lower or "bluray" in name_lower) and
                        "sample" not in name_lower and
                        "telesync" not in name_lower and "cam" not in name_lower):
                        
                        torrent_href = domain + row.find_all('td')[0].find_all('a')[-1]['href']
                        potential_torrents.append((seeders, torrent_href, name))
                except (IndexError, ValueError):
                    continue

            if potential_torrents:
                best_torrent = sorted(potential_torrents, reverse=True)[0]
                magnet = self.get_magnet_link(best_torrent[1])
                if magnet:
                    return TorrentResult(
                        name=best_torrent[2],
                        seeders=best_torrent[0],
                        magnet=magnet,
                        source="1337x"
                    )
        except Exception as e:
            print(f"✗ Error searching 1337x: {e}")
        
        print("✗ No torrents found on 1337x")
        return None

class SiteYTS(TorrentSite):
    def search(self, title: str) -> Optional[TorrentResult]:
        #print(f"Searching for {title} on YTS")
        search_query = title.replace(' ', '+').lower()

        search_url = f"https://yts.mx/api/v2/list_movies.json?query_term={search_query}"
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            print(f"✗ YTS API returned status code: {response.status_code}")
            return None
        
        data = response.json()
        
        # Check if the response has the expected structure
        if not data.get('status') == 'ok':
            print("✗ YTS API returned invalid response")
            return None
        
        movies = data.get('data', {}).get('movies', [])
        if not movies:
            print("✗ No movies found on YTS")
            return None
        
        # Find the best matching movie
        for movie in movies:
            movie_title = movie['title'].lower()
            if movie_title == title.lower() or movie_title in title.lower():
                torrents = movie.get('torrents', [])
                
                # Find the best quality 1080p torrent
                best_torrent = None
                for torrent in torrents:
                    if torrent['quality'] == '1080p':
                        if not best_torrent or torrent['seeds'] > best_torrent['seeds']:
                            best_torrent = torrent
                
                if best_torrent:
                    hash = best_torrent.get('hash')
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
                        
                        return TorrentResult(
                            name=f"{movie['title']} (1080p)",
                            seeders=best_torrent.get('seeds', 0),
                            magnet=magnet,
                            source="YTS"
                        )
        
        print("✗ No torrents found on YTS")     
        return None