"""
Filename: tunarr.py
Date: 02-17-2025
Author: robinbtw

Description:
This module provides a class to manage interactions with the Tunarr API.
It includes methods to create 24/7 channels, add programming to channels.
"""

# Import standard libraries
import os
import uuid
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from managers.tmdb import TMDBManager
g_tmdb = TMDBManager()

class TunnarEntry:
    """A class to represent a programming entry in Tunarr."""
    def __init__(self, details, jellyfinSourceId):
        self.external_source_type = "Jellyfin"
        self.title = details.get('original_title')
        self.external_key = f"{jellyfinSourceId}"
        self.summary = details.get('overview')
        self.release_date = f"{details.get('release_date')}T00:00:00.0000000Z"
        self.runtime = details.get('runtime') * 60 * 1000
        self.year = self.release_date[:4]
        self.tmdb_id = details.get('id')
        self.imdb_id = details.get('imdb_id')

        production_countries = details.get('production_countries', [])
        self.iso_3166_1 = production_countries[0].get('iso_3166_1') if production_countries else 'US' 
        
        for result in g_tmdb.get_movie_release_dates(self.tmdb_id).get('results'):
            if result.get('iso_3166_1') == self.iso_3166_1:
                self.official_rating = result.get('release_dates')[0].get('certification')
                break

        def __repr__(self):
            return (
                f"TunnarEntry("
                f"external_source_type='{self.external_source_type}', "
                f"title='{self.title}', "
                f"duration={self.duration}, "
                f"external_key='{self.external_key}', "
                f"summary='{self.summary}', "
                f"release_date='{self.release_date}', "
                f"runtime={self.runtime}, "
                f"year={self.year}, "
                f"tmdb_id={self.tmdb_id}, "
                f"imdb_id='{self.imdb_id}', "
                f"iso_3166_1='{self.iso_3166_1}', "
                f"official_rating='{self.official_rating}')"
            )

class TunarrManager():
    def __init__(self):
        """Initializes the TunarrManager"""
        self.server = os.getenv('TUNARR_SERVER')
        self.headers = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        self.transcode_config_id = os.getenv('TUNARR_TRANSCODE_CONFIG_ID')
  
    def _make_request(self, method, endpoint, json=None):
        """Makes an HTTP request and returns the response content."""
        url = f"{self.server}/api{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=json)
            response.raise_for_status()    
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Tunarr API request failed: {e}")
            return None
    
    def _get_channel(self, channel_id):
        """Returns a channel by ID."""
        return self._make_request('GET', f'/channels/{channel_id}')
    
    def _delete_channel(self, channel_id):
        """Deletes a channel from Tunarr."""
        return self._make_request('DELETE', f'/channels/{channel_id}')
    
    def _update_channel(self, channel_id, updates):
        """Updates a channel with the given updates."""
        if (channel := self._get_channel(channel_id)):
            transcoding = { "transcoding": { "targetResolution": "global", "videoBitrate": "global", "videoBufferSize": "global" } }
            channel.update(transcoding)
            channel.update(updates)
            self._make_request('PUT', f'/channels/{channel_id}', json=channel)
    
    def _add_channel(self, name, group):
        """Adds a channel to Tunarr."""
        data = {
            "disableFillerOverlay": True,
            "duration": 0,
            "fillerRepeatCooldown": 30000,
            "groupTitle": group,
            "guideMinimumDuration": 30000,
            "icon": {
                "path": "",
                "width": 0,
                "duration": 0,
                "position": "bottom-right"
            },
            "id": str(uuid.uuid4()),
            "name": f"24/7 {name.upper()}",
            "number": len(self.get_all_channels()) + 1,
            "offline": {
                "picture": "",
                "soundtrack": "",
                "mode": "pic"
            },
            "startTime": int(time.time() * 1000),
            "stealth": False,
            "transcoding": {
                "targetResolution": "global",
                "videoBitrate": "global",
                "videoBufferSize": "global"
            },
            "onDemand": {
                "enabled": False
            },
            "streamMode": "hls",
            "transcodeConfigId": f"{self.transcode_config_id}"
        }

        return self._make_request('POST', '/channels', json=data)
    
    def add_programming(self, channel_id, entry):
        """Adds programming to a channel."""
        data = {
            "type": "manual",
            "lineup": [{
                "duration": entry.runtime,
                "index": 0,
            }],
            "programs": [{
                "externalSourceType": "jellyfin",
                "date": entry.release_date,
                "duration": entry.runtime,
                "externalSourceId": entry.external_source_type,
                "externalKey": entry.external_key,
                "rating": entry.official_rating if hasattr(entry, 'official_rating') else "NR",
                "summary": entry.summary,
                "title": entry.title,
                "type": "content",
                "subtype": "movie",
                "year": int(entry.year),
                "parent": {"externalIds": []},
                "grandparent": {"externalIds": []},
                "externalIds": [
                    {
                        "type": "multi",
                        "id": entry.external_key,
                        "source": entry.external_source_type.lower(),
                        "sourceId": entry.external_source_type
                    },
                    {
                        "id": str(entry.tmdb_id),
                        "source": "tmdb", 
                        "type": "single"
                    },
                    {
                        "id": str(entry.imdb_id),
                        "source": "imdb",
                        "type": "single"
                    }
                ],
                "uniqueId": f"{entry.external_source_type.lower()}|{entry.external_source_type}|{entry.external_key}",
                "id": f"{entry.external_source_type.lower()}|{entry.external_source_type}|{entry.external_key}",
                "externalSourceName": entry.external_source_type,
                "persisted": False,
                "originalIndex": 0,
                "startTimeOffset": 0
            }],
            "append": True
        }
        return self._make_request('POST', f'/channels/{channel_id}/programming', json=data)
    
    def get_all_channels(self):
        """Returns all channels in Tunarr."""
        return self._make_request('GET', '/channels')
    
    def get_channel_programming(self, channel_id):
        """Returns all programmings for a channel."""
        return self._make_request('GET', f'/channels/{channel_id}/programming')
    
    def get_channel_by_name(self, name):
        """Returns a channel by name."""
        channels = self.get_all_channels()
        for channel in channels:
            if name.lower() in channel['name'].lower():
                return channel
  
    def create_tunarr_channel(self, name, group="Movies"):
        """Creates a 24/7 channel in Tunarr."""
        print(f"Creating Tunarr channel: 24/7 {name.upper()}")
        if not self.get_channel_by_name(name):
            return self._add_channel(name, group)
        # Channel already exists
        return self.get_channel_by_name(name)
        
    def normalize_channels(self):
        """Normalizes channel numbers."""
        channels = self.get_all_channels()
        for i, channel in enumerate(channels, start=1):
            if channel.get('number') != i:
                self._update_channel(channel['id'], {"number": i})    
        
