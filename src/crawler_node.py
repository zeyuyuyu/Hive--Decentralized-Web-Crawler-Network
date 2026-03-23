import time
import random
from urllib.parse import urlparse
from collections import defaultdict
import aiohttp
import asyncio

class CrawlerNode:
    def __init__(self, node_id, max_requests_per_domain=10):
        self.node_id = node_id
        self.max_requests_per_domain = max_requests_per_domain
        self.domain_requests = defaultdict(int)
        self.domain_timestamps = defaultdict(list)
        self.backoff_times = defaultdict(lambda: 1)

    async def fetch_url(self, url, session):
        domain = urlparse(url).netloc
        
        # Check domain request limits
        if self.domain_requests[domain] >= self.max_requests_per_domain:
            await self._wait_for_slot(domain)
        
        # Apply exponential backoff if needed
        if self.backoff_times[domain] > 1:
            await asyncio.sleep(self.backoff_times[domain])
        
        try:
            async with session.get(url) as response:
                if response.status == 429:  # Too Many Requests
                    self.backoff_times[domain] = min(self.backoff_times[domain] * 2, 60)
                    return None
                    
                self.backoff_times[domain] = max(1, self.backoff_times[domain] / 2)
                content = await response.text()
                
                # Update rate limiting trackers
                now = time.time()
                self.domain_timestamps[domain].append(now)
                self.domain_requests[domain] += 1
                
                return {
                    'url': url,
                    'status': response.status,
                    'content': content,
                    'headers': dict(response.headers)
                }
                
        except Exception as e:
            print(f'Error fetching {url}: {str(e)}')
            self.backoff_times[domain] = min(self.backoff_times[domain] * 2, 60)
            return None

    async def _wait_for_slot(self, domain):
        """Wait until a request slot becomes available for the domain"""
        now = time.time()
        while True:
            # Remove timestamps older than 60 seconds
            self.domain_timestamps[domain] = [
                ts for ts in self.domain_timestamps[domain]
                if now - ts <= 60
            ]
            
            if len(self.domain_timestamps[domain]) < self.max_requests_per_domain:
                self.domain_requests[domain] = len(self.domain_timestamps[domain])
                break
                
            await asyncio.sleep(random.uniform(0.1, 1.0))

    async def crawl_urls(self, urls):
        """Crawl multiple URLs with rate limiting and backoff"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                task = asyncio.create_task(self.fetch_url(url, session))
                tasks.append(task)
                
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]

    def get_stats(self):
        """Return current crawler stats"""
        return {
            'node_id': self.node_id,
            'active_domains': len(self.domain_requests),
            'total_requests': sum(self.domain_requests.values()),
            'backoff_domains': len([d for d, t in self.backoff_times.items() if t > 1])
        }
