import time
import random
from urllib.parse import urlparse
from collections import defaultdict

class CrawlerNode:
    def __init__(self, node_id, max_requests_per_domain=10):
        self.node_id = node_id
        self.max_requests = max_requests_per_domain
        self.domain_timestamps = defaultdict(list)
        self.backoff_times = defaultdict(lambda: 1)
        
    def can_crawl_url(self, url):
        """Check if we can crawl this URL based on rate limits"""
        domain = urlparse(url).netloc
        now = time.time()
        
        # Clean old timestamps
        self.domain_timestamps[domain] = [
            ts for ts in self.domain_timestamps[domain]
            if now - ts < 60  # Only keep last minute
        ]
        
        # Check rate limit
        if len(self.domain_timestamps[domain]) >= self.max_requests:
            return False
            
        return True

    def record_crawl_attempt(self, url, success):
        """Record crawl attempt and update backoff"""
        domain = urlparse(url).netloc
        now = time.time()
        
        self.domain_timestamps[domain].append(now)
        
        if success:
            # Reset backoff on success
            self.backoff_times[domain] = 1
        else:
            # Exponential backoff on failure
            self.backoff_times[domain] = min(300, self.backoff_times[domain] * 2)

    def get_backoff_time(self, url):
        """Get current backoff time for domain"""
        domain = urlparse(url).netloc
        jitter = random.uniform(0.5, 1.5)
        return self.backoff_times[domain] * jitter

    async def crawl(self, url):
        """Main crawl method with rate limiting and backoff"""
        if not self.can_crawl_url(url):
            return None
            
        try:
            # Add actual crawling logic here
            success = True  # Based on crawl result
            
        except Exception as e:
            success = False
            
        self.record_crawl_attempt(url, success)
        
        if not success:
            backoff = self.get_backoff_time(url)
            await asyncio.sleep(backoff)
            
        return None

    def get_stats(self):
        """Get node statistics"""
        return {
            'node_id': self.node_id,
            'domains_tracked': len(self.domain_timestamps),
            'total_requests': sum(len(times) for times in self.domain_timestamps.values()),
            'backoff_domains': len([d for d,t in self.backoff_times.items() if t > 1])
        }
