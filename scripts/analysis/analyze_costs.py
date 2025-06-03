#!/usr/bin/env python3
"""
Cost Analysis Script

Analyzes API usage costs and provides budget recommendations for AI-Horizon collections.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from aih.utils.cost_tracker import cost_tracker

def analyze_costs(monthly_budget: float = 100.0):
    """Analyze current costs and provide budget recommendations."""
    
    print("💰 AI-HORIZON COST ANALYSIS")
    print("=" * 50)
    
    # Current cost summary
    print(f"\n📊 CURRENT COSTS:")
    print(f"   Total Historical Cost: ${cost_tracker.costs['total_cost']:.2f}")
    
    today = datetime.now()
    today_cost = cost_tracker.get_daily_cost()
    monthly_cost = cost_tracker.get_monthly_cost(today.year, today.month)
    
    print(f"   Today's Cost:         ${today_cost:.2f}")
    print(f"   This Month's Cost:    ${monthly_cost:.2f}")
    
    # API breakdown
    print(f"\n🔌 API USAGE BREAKDOWN:")
    for api_name, usage in cost_tracker.costs["api_usage"].items():
        if usage["calls"] > 0:
            print(f"   {api_name.upper()}:")
            print(f"     • Calls:    {usage['calls']:,}")
            print(f"     • Tokens:   {usage['tokens']:,}")
            print(f"     • Cost:     ${usage['cost']:.4f}")
            if usage["tokens"] > 0:
                print(f"     • Per Call: ${usage['cost']/usage['calls']:.4f}")
    
    # Collection cost estimates
    print(f"\n📈 COLLECTION COST ESTIMATES:")
    estimates = cost_tracker.estimate_collection_cost()
    
    for api_name, estimate in estimates.items():
        print(f"   {api_name.upper()} (80 articles):")
        print(f"     • Estimated Cost: ${estimate['cost']:.2f}")
        print(f"     • Queries: {estimate['queries']}")
        print(f"     • Tokens: {estimate['tokens']:,}")
    
    # Budget analysis
    print(f"\n💡 BUDGET ANALYSIS (${monthly_budget}/month):")
    budget_analysis = cost_tracker.get_budget_analysis(monthly_budget)
    
    print(f"   Monthly Budget:       ${budget_analysis['monthly_budget']:.2f}")
    print(f"   Current Usage:        ${budget_analysis['current_month_cost']:.2f}")
    print(f"   Budget Remaining:     ${budget_analysis['budget_remaining']:.2f}")
    print(f"   Budget Utilization:   {budget_analysis['budget_utilization']:.1f}%")
    print(f"   Daily Average:        ${budget_analysis['daily_average']:.2f}")
    print(f"   Projected Monthly:    ${budget_analysis['projected_monthly']:.2f}")
    
    if budget_analysis['budget_remaining'] > 0:
        print(f"   Days Remaining:       {budget_analysis['days_remaining']} days")
    else:
        print(f"   ⚠️  OVER BUDGET by ${abs(budget_analysis['budget_remaining']):.2f}")
    
    # Collection frequency recommendations
    print(f"\n🎯 COLLECTION FREQUENCY RECOMMENDATIONS:")
    
    # Use Perplexity estimate (most commonly used)
    perplexity_cost = estimates.get("perplexity", {}).get("cost", 0.24)
    
    runs_per_budget = int(monthly_budget / perplexity_cost) if perplexity_cost > 0 else 0
    print(f"   With ${monthly_budget} budget:")
    print(f"     • ~{runs_per_budget} full collections per month")
    print(f"     • ~{runs_per_budget/4:.1f} collections per week")
    print(f"     • One collection every {30/runs_per_budget:.1f} days" if runs_per_budget > 0 else "     • Cannot afford monthly collections")
    
    # Different budget scenarios
    print(f"\n💰 BUDGET SCENARIOS:")
    budgets = [25, 50, 100, 200, 500]
    for budget in budgets:
        runs = int(budget / perplexity_cost) if perplexity_cost > 0 else 0
        frequency = f"Every {30/runs:.1f} days" if runs > 0 else "Not feasible"
        print(f"   ${budget:3d}/month: {runs:2d} runs, {frequency}")
    
    # Optimization recommendations
    print(f"\n🔧 OPTIMIZATION RECOMMENDATIONS:")
    
    if cost_tracker.costs["total_cost"] > 0:
        # Calculate actual cost per article from historical data
        total_articles = sum(
            usage.get("calls", 0) * 3  # Rough estimate: 3 articles per API call
            for usage in cost_tracker.costs["api_usage"].values()
        )
        if total_articles > 0:
            actual_cost_per_article = cost_tracker.costs["total_cost"] / total_articles
            print(f"   • Historical cost per article: ${actual_cost_per_article:.4f}")
            
            # Compare to estimates
            estimated_cost_per_article = perplexity_cost / 80
            efficiency = (estimated_cost_per_article / actual_cost_per_article) * 100 if actual_cost_per_article > 0 else 100
            print(f"   • Collection efficiency: {efficiency:.1f}%")
            
            if efficiency < 80:
                print(f"   ⚠️  Consider optimizing queries to reduce cost")
            elif efficiency > 120:
                print(f"   ✅ Collection is very cost-efficient!")
    
    print(f"\n   • Use targeted collections for specific insights")
    print(f"   • Reset session costs between major runs for tracking")
    print(f"   • Monitor cost per article to optimize queries")
    print(f"   • Consider running smaller collections more frequently")
    
    # Return key metrics for programmatic use
    return {
        "monthly_cost": monthly_cost,
        "budget_remaining": budget_analysis["budget_remaining"],
        "runs_per_budget": runs_per_budget,
        "cost_per_run": perplexity_cost,
        "over_budget": budget_analysis["budget_remaining"] < 0
    }

def main():
    """Main function to run cost analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze AI-Horizon API costs and budget')
    parser.add_argument('--budget', type=float, default=100.0, 
                       help='Monthly budget in USD (default: $100)')
    
    args = parser.parse_args()
    
    try:
        metrics = analyze_costs(args.budget)
        
        # Print summary recommendation
        print(f"\n📋 SUMMARY RECOMMENDATION:")
        if metrics["over_budget"]:
            print(f"   🚨 REDUCE USAGE: Over budget by ${abs(metrics['budget_remaining']):.2f}")
        elif metrics["budget_remaining"] > metrics["cost_per_run"]:
            print(f"   ✅ OPTIMAL: Can run {metrics['runs_per_budget']} collections per month")
        else:
            print(f"   ⚠️  CAUTIOUS: Budget tight, monitor usage closely")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during cost analysis: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 