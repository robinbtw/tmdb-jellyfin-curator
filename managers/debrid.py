"""
Filename: debrid.py
Date: 02-17-2025
Author: robinbtw

Description:
This module provides a class to manage interactions with the Real-Debrid API.
It includes methods to check user info, premium status, torrent list, downloads, and more.
"""

# Import required libraries
import os
import re
import time
import requests
from dotenv import load_dotenv

# Import custom libraries
from managers.proxies import ProxyManager

# Load environment variables
load_dotenv()

class RealDebridManager:
    """A class to manage Real-Debrid API interactions."""

    def __init__(self):
        """Initializes the RealDebridManager with API credentials."""
        self.api_url = os.getenv('REAL_DEBRID_API_URL')
        self.api_key = os.getenv('REAL_DEBRID_API_KEY')
        self.headers = { 'Authorization': f'Bearer {self.api_key}' }
        self.proxy_manager = ProxyManager()

    def _inform_user(self):
        if self._get_user():
            print("✓ Real-Debrid API credentials found!")
            print(f"- Premium status: {self._get_premium_status()}")
            print(f"- Days left: {self._get_premium_status_days_left()}")
            print()
        else:
            print("✗ Real-Debrid API credentials not found! Please check your .env file.")
            print()

    def _make_request(self, method, endpoint, params=None, data=None, timeout=8):
        """Internal helper function to make API requests."""
        url = f"{self.api_url}{endpoint}"
        try:
            proxy = self.proxy_manager.get_proxy()
            response = requests.request(method, url, headers=self.headers, params=params, data=data, timeout=timeout, proxies={'http': proxy })
            response.raise_for_status()  

            # Return True for successful DELETE requests (204 No Content)
            if response.status_code == 204:
                return True

            # Parse JSON for other successful responses
            return response.json() if response.text else None
        except requests.exceptions.RequestException as e:
            print(f"✗ API request failed: {e}")
            return None

    def _get_user(self):
        """Get current user info from real-debrid."""
        return self._make_request('GET', "/user")

    def _get_premium_status(self):
        """Check if user has premium status."""
        user = self._get_user()
        if user:
            return user.get('type') == 'premium'
        return False

    def _get_premium_status_days_left(self):
        """Get time left for premium status."""
        user = self._get_user()
        if user:
            seconds_left = user.get('premium')
            return seconds_left // 86400
        return None

    def _get_torrent_list(self, limit=5000):
        """Get torrent list from real-debrid."""
        params = {'limit': limit}
        return self._make_request('GET', "/torrents", params=params)

    def _get_downloads(self, limit=100):
        """Get downloads from real-debrid."""
        params = {'limit': limit}
        return self._make_request('GET', "/downloads", params=params)

    def _get_torrent_info(self, torrent_id):
        """Get torrent info from real-debrid."""
        return self._make_request('GET', f"/torrents/info/{torrent_id}")
    
    def _delete_download(self, id):
        """Delete download in real-debrid."""
        return self._make_request('DELETE', f"/downloads/delete/{id}")
    
    def _extract_hash_from_magnet(self, magnet):
        """Extract hash from magnet link."""
        hash_match = re.search(r'btih:([a-fA-F0-9]{40})', magnet)
        if hash_match:
            return hash_match.group(1).lower()
        return None
    
    def _check_for_duplicate_hash(self, magnet_hash):    
        """Check if a torrent with the given hash already exists in Debrid."""
        torrents = self._get_torrent_list()
        if torrents:
            for torrent in torrents:
                if torrent.get('hash') == magnet_hash:
                    #print("✗ Torrent already exists in debrid!")
                    return True
        return False
       
    def delete_torrent(self, id):
        """Delete torrent in Real-Debrid."""
        return self._make_request('DELETE', f"/torrents/delete/{id}")

    def add_magnet_hash_to_debrid(self, hash):
        """Add magnet by hash to Real-Debrid."""
        magnet = (
            f"magnet:?xt=urn:btih:{hash}"
            "&tr=udp://open.demonii.com:1337/announce"
            "&tr=udp://tracker.openbittorrent.com:80"
            "&tr=udp://tracker.coppersurfer.tk:6969"
            "&tr=udp://glotorrents.pw:6969/announce"
            "&tr=udp://tracker.opentrackr.org:1337/announce"
            "&tr=udp://torrent.gresille.org:80/announce"
            "&tr=udp://p4p.arenabg.com:1337"
            "&tr=udp://tracker.leechers-paradise.org:6969"
        )
        return self.add_magnet_to_debrid(magnet)
    
    def start_magnet_in_debrid(self, id) -> bool:
        """Start magnet in Real-Debrid."""
        result =  self._make_request('POST', f"/torrents/selectFiles/{id}", data={"files": "all"}, timeout=3)
        if result:
            return True
        return False

    def add_magnet_to_debrid(self, magnet):
        """Add magnet to Real-Debrid."""

        magnet_hash = self._extract_hash_from_magnet(magnet)
        if not magnet_hash:
            print("✗ Invalid magnet link - could not extract hash!")
            return None, None

        if self._check_for_duplicate_hash(magnet_hash):
            return None, None

        result = self._make_request('POST', "/torrents/addMagnet", data={"magnet": magnet}, timeout=3)
    
        if result and 'id' in result:
            return result, result['id']
        return None, None
    
    def get_all_duplicate_torrents(self):
        """Retrieves duplicate torrents from Real-Debrid by hash."""
        torrents = self._get_torrent_list()
        if not torrents:
            print("No torrents found in Real-Debrid")
            return []

        seen = {}
        duplicates = []

        for torrent in torrents:
            torrent_hash = torrent.get('hash')
            if not torrent_hash:
                continue

            if torrent_hash in seen:
                duplicates.append({
                    'name': torrent.get('filename', 'Unknown'),
                    'hash': torrent_hash,
                    'original_id': seen[torrent_hash],
                    'duplicate_id': torrent.get('id')
                })
            else:
                seen[torrent_hash] = torrent.get('id')

        return duplicates





