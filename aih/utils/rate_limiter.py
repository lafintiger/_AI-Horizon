"""
Rate limiting utility for API calls.

Prevents exceeding API rate limits and manages request timing.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional
from threading import Lock

from aih.utils.logging import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """
    Rate limiter for API calls with per-service limits.
    
    Uses a sliding window approach to track requests.
    """
    
    def __init__(self):
        """Initialize rate limiter with empty tracking."""
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._locks: Dict[str, Lock] = defaultdict(Lock)
        
        # Default rate limits (requests per minute)
        self._limits = {
            'perplexity': 60,
            'openai': 10,
            'anthropic': 10,
            'default': 10
        }
    
    def set_limit(self, service: str, requests_per_minute: int) -> None:
        """
        Set rate limit for a specific service.
        
        Args:
            service: Name of the service (e.g., 'perplexity', 'openai')
            requests_per_minute: Maximum requests allowed per minute
        """
        self._limits[service] = requests_per_minute
        logger.info(f"Set rate limit for {service}: {requests_per_minute} req/min")
    
    def wait_if_needed(self, service: str) -> None:
        """
        Wait if necessary to respect rate limits.
        
        Args:
            service: Name of the service making the request
        """
        with self._locks[service]:
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            # Remove old requests outside the window
            while self._requests[service] and self._requests[service][0] < window_start:
                self._requests[service].popleft()
            
            # Check if we're at the limit
            limit = self._limits.get(service, self._limits['default'])
            if len(self._requests[service]) >= limit:
                # Calculate wait time until oldest request falls outside window
                oldest_request = self._requests[service][0]
                wait_time = (oldest_request + 60) - now
                
                if wait_time > 0:
                    logger.info(f"Rate limit reached for {service}. Waiting {wait_time:.2f} seconds")
                    time.sleep(wait_time)
                    # Remove the old request that just expired
                    self._requests[service].popleft()
            
            # Record this request
            self._requests[service].append(now)
    
    def get_current_usage(self, service: str) -> Dict[str, int]:
        """
        Get current usage statistics for a service.
        
        Args:
            service: Name of the service
            
        Returns:
            Dictionary with current usage info
        """
        with self._locks[service]:
            now = time.time()
            window_start = now - 60
            
            # Count requests in current window
            current_requests = sum(1 for req_time in self._requests[service] 
                                 if req_time > window_start)
            
            limit = self._limits.get(service, self._limits['default'])
            
            return {
                'current_requests': current_requests,
                'limit': limit,
                'remaining': max(0, limit - current_requests),
                'window_reset_in': 60 - (now % 60)
            }
    
    def can_make_request(self, service: str) -> bool:
        """
        Check if a request can be made without waiting.
        
        Args:
            service: Name of the service
            
        Returns:
            True if request can be made immediately
        """
        usage = self.get_current_usage(service)
        return usage['remaining'] > 0

# Global rate limiter instance
rate_limiter = RateLimiter() 