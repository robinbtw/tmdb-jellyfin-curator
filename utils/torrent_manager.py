from typing import List, Optional
from .torrent_sites import TorrentSite, TorrentResult, Site1337x, SiteYTS, SiteNyaa

class TorrentManager:
    def __init__(self):
        self.sites: List[TorrentSite] = [
            Site1337x(),
            SiteYTS(), 
            SiteNyaa(),
        ]

    def search_all(self, title: str) -> Optional[TorrentResult]:
        """Search all configured torrent sites and return the best result."""
        all_results = []
        
        for site in self.sites:
            try:
                result = site.search(title)
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"✗ Error searching {site.__class__.__name__}: {e}")
        
        # Sort results by number of seeders
        all_results.sort(key=lambda x: x.seeders, reverse=True)
        return all_results[0] if all_results else None