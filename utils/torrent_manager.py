from typing import List, Optional
from .torrent_sites import TorrentSite, TorrentResult, Site1337x, SiteYTS, SiteNyaa

class TorrentManager:
    def __init__(self):
        self.sites: List[TorrentSite] = [
            Site1337x(),
            SiteYTS(), 
            SiteNyaa(),
        ]

    def search_all(self, title: str) -> List[TorrentResult]:
        """Search all configured torrent sites and return the best result."""
        all_results = []
        
        print(f"Searching for: {title}")
        for site in self.sites:
            try:
                result = site.search(title)
                if result:
                    print(f"✓ Found {len(result)} torrents on {site.__class__.__name__}")
                    all_results.append(result)
            except Exception as e:
                print(f"✗ Error searching {site.__class__.__name__}: {e}")
        
        # Sort results by number of seeders
        top = sorted(all_results, key=lambda x: x[0].seeders, reverse=True)
        return top if top else None