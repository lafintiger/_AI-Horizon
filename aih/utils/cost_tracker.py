#!/usr/bin/env python3
"""
Cost Tracking Utility

Tracks API usage costs across different services for budget monitoring.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class CostTracker:
    """Track API usage costs across different services."""
    
    # API Pricing (per 1000 tokens unless specified)
    PRICING = {
        "perplexity": {
            "sonar_small": 0.0002,      # $0.2 per 1M tokens
            "sonar_large": 0.001,       # $1.0 per 1M tokens  
            "sonar_huge": 0.005,        # $5.0 per 1M tokens
            "default": 0.001            # Default to sonar_large pricing
        },
        "openai": {
            "gpt-4": 0.03,              # $30 per 1M tokens
            "gpt-3.5-turbo": 0.002,     # $2 per 1M tokens
            "default": 0.002
        },
        "anthropic": {
            "claude-3": 0.015,          # $15 per 1M tokens
            "default": 0.015
        }
    }
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize cost tracker with optional storage path."""
        self.storage_path = storage_path or "data/costs/cost_tracking.json"
        self.costs_file = Path(self.storage_path)
        self.costs_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Global status tracker for real-time updates
        self.status_tracker = None
        
        # Load existing costs
        self.costs = self._load_costs()
    
    def set_status_tracker(self, tracker):
        """Set the global status tracker for real-time updates."""
        self.status_tracker = tracker
    
    def _load_costs(self) -> Dict:
        """Load cost data from storage."""
        if self.costs_file.exists():
            try:
                with open(self.costs_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "total_cost": 0.0,
            "daily_costs": {},
            "api_usage": {
                "perplexity": {"calls": 0, "tokens": 0, "cost": 0.0},
                "openai": {"calls": 0, "tokens": 0, "cost": 0.0},
                "anthropic": {"calls": 0, "tokens": 0, "cost": 0.0}
            },
            "sessions": []
        }
    
    def _save_costs(self):
        """Save cost data to storage."""
        try:
            with open(self.costs_file, 'w') as f:
                json.dump(self.costs, f, indent=2)
        except Exception as e:
            print(f"Error saving costs: {e}")
    
    def track_api_call(self, api_name: str, model: str = "default", 
                      tokens: int = 1000, custom_cost: Optional[float] = None) -> float:
        """
        Track an API call and calculate cost.
        
        Args:
            api_name: Name of API service (perplexity, openai, anthropic)
            model: Specific model used
            tokens: Number of tokens processed
            custom_cost: Custom cost override
            
        Returns:
            float: Cost of this API call
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate cost
        if custom_cost is not None:
            cost = custom_cost
        else:
            api_pricing = self.PRICING.get(api_name.lower(), {"default": 0.001})
            rate = api_pricing.get(model, api_pricing["default"])
            cost = (tokens / 1000) * rate
        
        # Update tracking data
        if api_name not in self.costs["api_usage"]:
            self.costs["api_usage"][api_name] = {"calls": 0, "tokens": 0, "cost": 0.0}
        
        self.costs["api_usage"][api_name]["calls"] += 1
        self.costs["api_usage"][api_name]["tokens"] += tokens
        self.costs["api_usage"][api_name]["cost"] += cost
        
        # Update daily costs
        if today not in self.costs["daily_costs"]:
            self.costs["daily_costs"][today] = 0.0
        self.costs["daily_costs"][today] += cost
        
        # Update total cost
        self.costs["total_cost"] += cost
        
        # Update status tracker if available
        if self.status_tracker:
            self.status_tracker.add_api_cost(api_name, cost, 1)
        
        # Save costs
        self._save_costs()
        
        return cost
    
    def get_daily_cost(self, date: Optional[str] = None) -> float:
        """Get cost for a specific day (defaults to today)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.costs["daily_costs"].get(date, 0.0)
    
    def get_monthly_cost(self, year: int, month: int) -> float:
        """Get total cost for a specific month."""
        month_prefix = f"{year:04d}-{month:02d}"
        return sum(
            cost for date, cost in self.costs["daily_costs"].items()
            if date.startswith(month_prefix)
        )
    
    def estimate_collection_cost(self, articles: int = 80, queries_per_article: int = 3,
                                tokens_per_query: int = 1000) -> Dict:
        """Estimate cost for a collection run."""
        total_queries = articles * queries_per_article
        total_tokens = total_queries * tokens_per_query
        
        # Estimate for each API
        estimates = {}
        for api_name, pricing in self.PRICING.items():
            default_rate = pricing["default"]
            estimated_cost = (total_tokens / 1000) * default_rate
            estimates[api_name] = {
                "cost": estimated_cost,
                "queries": total_queries,
                "tokens": total_tokens
            }
        
        return estimates
    
    def get_budget_analysis(self, monthly_budget: float = 100.0) -> Dict:
        """Analyze current spending against budget."""
        now = datetime.now()
        current_month_cost = self.get_monthly_cost(now.year, now.month)
        daily_average = current_month_cost / now.day if now.day > 0 else 0
        
        # Project monthly cost
        days_in_month = 31  # Rough estimate
        projected_monthly = daily_average * days_in_month
        
        return {
            "monthly_budget": monthly_budget,
            "current_month_cost": current_month_cost,
            "daily_average": daily_average,
            "projected_monthly": projected_monthly,
            "budget_remaining": monthly_budget - current_month_cost,
            "budget_utilization": (current_month_cost / monthly_budget) * 100,
            "days_remaining": int((monthly_budget - current_month_cost) / daily_average) if daily_average > 0 else 999
        }
    
    def reset_session_tracking(self):
        """Reset session-specific tracking."""
        if self.status_tracker:
            self.status_tracker.reset_session_cost()

# Global cost tracker instance
cost_tracker = CostTracker() 