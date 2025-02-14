"""
Filename: debrid.py
Date: 2023-10-05
Author: robinbtw

Description:
This module provides a class to manage interactions with the Real-Debrid API.
It includes methods to check user info, premium status, torrent list, downloads, and more.
"""

# Import required libraries
import os
import re
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RealDebridManager:
    """A class to manage Real-Debrid API interactions."""

    def __init__(self):
        """Initializes the RealDebridManager with API credentials."""
        self.api_url = os.getenv('REAL_DEBRID_API_URL')
        self.api_key = os.getenv('REAL_DEBRID_API_KEY')
        self.headers = { 'Authorization': f'Bearer {self.api_key}' }
        self._inform_user()

    def _inform_user(self):
        if self.get_real_debrid_user():
            print("✓ Real-Debrid API credentials found!")
            print(f"- Premium status: {self.get_premium_status()}")
            print(f"- Days left: {self.get_premium_status_days_left()}")
            print()
        else:
            print("✗ Real-Debrid API credentials not found! Please check your .env file.")
            print()

        if not self.get_premium_status():
            print("✗ No premium: premium is highly recommended!")
            print()

    def _make_request(self, method, endpoint, params=None, data=None, timeout=5):
        """Internal helper function to make API requests."""
        url = f"{self.api_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, data=data, timeout=timeout)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ API request failed: {e}")
            return None

    def get_real_debrid_user(self):
        """Get current user info from Real-Debrid."""
        return self._make_request('GET', "/user")

    def get_premium_status(self):
        """Check if user has premium status."""
        user = self.get_real_debrid_user()
        if user:
            return user.get('type') == 'premium'
        return False

    def get_premium_status_days_left(self):
        """Get time left for premium status."""
        user = self.get_real_debrid_user()
        if user:
            seconds_left = user.get('premium')
            return seconds_left // 86400
        return None

    def get_torrent_list(self, limit=100):
        """Get torrent list from Real-Debrid."""
        params = {'limit': limit}
        return self._make_request('GET', "/torrents", params=params)

    def get_downloads(self, limit=100):
        """Get downloads from Real-Debrid."""
        params = {'limit': limit}
        return self._make_request('GET', "/downloads", params=params)

    def get_torrent_info(self, torrent_id):
        """Get torrent info from Real-Debrid."""
        return self._make_request('GET', f"/torrents/info/{torrent_id}")

    def is_torrent_cached(self, torrent_id):
        """Check if torrent is cached in Real-Debrid."""
        torrent_info = self.get_torrent_info(torrent_id)
        if torrent_info:
            return torrent_info.get('status') == 'downloaded'
        return False

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

    def add_magnet_to_debrid(self, magnet):
        """Add magnet to Real-Debrid."""

        magnet_hash = self.extract_hash_from_magnet(magnet)
        if not magnet_hash:
            print("✗ Invalid magnet link - could not extract hash!")
            return None, None

        if self.check_for_duplicate_hash(magnet_hash):
            return None, None

        result = self._make_request('POST', "/torrents/addMagnet", data={"magnet": magnet}, timeout=3)
    
        if result and 'id' in result:
            return result, result['id']
        return None, None

    def start_magnet_in_debrid(self, id):
        """Start magnet in Real-Debrid."""
        result =  self._make_request('POST', f"/torrents/selectFiles/{id}", data={"files": "all"}, timeout=3)
        if result:
            return True
        return False

    def delete_download(self, id):
        """Delete download in Real-Debrid."""
        result = self._make_request('DELETE', f"/downloads/delete/{id}")
        if result:
            return True
        return False

    def delete_torrent(self, id):
        """Delete torrent in Real-Debrid."""
        result = self._make_request('DELETE', f"/torrents/delete/{id}")
        if result:
            return True
        return False
    
    def extract_hash_from_magnet(self, magnet):
        """Extract hash from magnet link."""
        hash_match = re.search(r'btih:([a-fA-F0-9]{40})', magnet)
        if hash_match:
            return hash_match.group(1).lower()
        return None
    
    def check_for_duplicate_hash(self, magnet_hash):    
        """Check if a torrent with the given hash already exists in Debrid."""
        torrents = self.get_torrent_list()
        if torrents:
            for torrent in torrents:
                if torrent.get('hash') == magnet_hash:
                    print("✗ Torrent already exists in debrid!")
                    return True
        return False



