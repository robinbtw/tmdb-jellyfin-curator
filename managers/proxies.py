"""
Filename: proxyies.py
Date: 02-17-2025
Author: robinbtw

Description:
This module provides proxy management functionality, including fetching and rotating proxies
from ProxyScrape API.
"""

# Import required libraries
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ProxyManager:
    """Manages proxy fetching and rotation from ProxyScrape."""
    
    def __init__(self):
        """Initialize the ProxyManager."""
        self.proxies: List[Dict[str, str]] = []
        self.last_update: Optional[datetime] = None
        self.update_interval = timedelta(hours=1)
        self.current_index = 0
        self.proxies = []

    def fetch_proxies(self) -> bool:
        """Fetch fresh proxies from ProxyScrape API."""

        if (self.last_update and 
            datetime.now() - self.last_update < self.update_interval):
            return True

        try:
            url = (
                "https://api.proxyscrape.com/v2/?"
                "request=getproxies"
                "&protocol=http"
                "&timeout=10000"
                "&country=US"
                "&ssl=all"
                "&anonymity=all"
            )
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            proxy_list = response.text.strip().split('\n')

            if proxy_list:
                for proxy_line in proxy_list[:100]:
                    try:
                        ip, port = proxy_line.strip().split(':')
                        proxy_url = f"http://{ip}:{port}"
                        self.proxies.append({'http': proxy_url })
                    except ValueError:
                        continue
                
                self.last_update = datetime.now()
                self.current_index = 0
                return True
            
            print("✗ Failed to fetch proxies: Empty response")
            return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to fetch proxies: {str(e)}")
            return False
        except Exception as e:
            print(f"✗ Failed to parse proxy data: {str(e)}")
            return False

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get current proxy and rotate to next one."""
        if not self.proxies:
            self.fetch_proxies()
            if not self.proxies:
                return None

        current_proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return current_proxy

    def test_proxy(self, proxy: Dict[str, str]) -> bool:
        """Test if a proxy is working."""
        try:
            response = requests.get(
                'https://api.ipify.org?format=json',
                proxies=proxy,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False