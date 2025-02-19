"""
Filename: proxyies.py
Date: 02-17-2025
Author: robinbtw

Description:
This module provides proxy management functionality, including fetching and rotating proxies
from ProxyScrape API.
"""

# Import required libraries
import requests
from typing import Optional
from datetime import datetime, timedelta

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.last_check = None
        self.check_interval = timedelta(minutes=30)
        self.current_index = 0
    
    def _fetch_proxies(self) -> bool:
        """Fetch new proxies from proxyscrape"""
        try:
            response = requests.get(
                "https://api.proxyscrape.com/v2/?"
                "request=getproxies"
                "&protocol=http"
                "&timeout=10000"
                "&country=US"
                "&ssl=all"
                "&anonymity=all",
                timeout=10
            )
            
            if response.status_code == 200:
                self.proxies = [
                    f"http://{proxy}" 
                    for proxy in response.text.split("\n") 
                    if proxy.strip()
                ]
                self.last_check = datetime.now()
                #print(f"✓ Fetched {len(self.proxies)} proxies")
                return True
            return False
        except Exception as e:
            print(f"✗ Failed to fetch proxies: {str(e)}")
            return False
            
    def get_proxy(self) -> Optional[str]:
        """Get next proxy using round-robin"""
        if not self.proxies or (
            self.last_check and 
            datetime.now() - self.last_check > self.check_interval
        ):
            if not self._fetch_proxies():
                return None
                
        if not self.proxies:
            return None
            
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def test_proxies(self) -> int:
        """Test all proxies and return count of working ones"""
        working = 0
        print("Testing proxies...")
        
        if not self._fetch_proxies():
            return 0
            
        for proxy in self.proxies[:]:
            try:
                response = requests.get(
                    'https://httpbin.org/ip',
                    proxies={'http': proxy },
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"✓ {proxy}: is working") 
                    working += 1
                else:
                    self.proxies.remove(proxy)
            except:
                self.proxies.remove(proxy)
                
        print(f"\nSummary: {working}/{len(self.proxies)} proxies working")
        return working