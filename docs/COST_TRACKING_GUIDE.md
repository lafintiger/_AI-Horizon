# 💰 AI-Horizon Cost Tracking Guide

The AI-Horizon system now includes comprehensive cost tracking for all API usage, helping you monitor spending and optimize collection strategies.

## 🎯 Cost Tracking Features

### Real-Time Dashboard Monitoring
- **Session Cost**: Cost accumulation for current session
- **Total Cost**: Historical cost across all time
- **Cost per Article**: Average cost for each article collected
- **Estimated Full Run**: Projected cost for 80-article collection
- **Runs per $100**: How many collections you can afford monthly

### API Cost Breakdown
- **Perplexity API**: ~$0.001 per 1000 tokens (primary service)
- **OpenAI API**: ~$0.002 per 1000 tokens (if integrated)
- **Anthropic API**: ~$0.015 per 1000 tokens (if integrated)

## 📊 Using the Cost Tracker

### 1. Web Dashboard
Navigate to the status dashboard at `http://localhost:5000` to see:
- Real-time cost updates during collection
- Session vs. total cost tracking
- Budget analysis and recommendations

### 2. Cost Analysis Tool
Run detailed cost analysis from command line:

```bash
# Basic analysis with $100 monthly budget
python analyze_costs.py

# Custom budget analysis
python analyze_costs.py --budget 50

# Advanced budget scenarios
python analyze_costs.py --budget 200
```

### 3. API Endpoints
- `POST /api/reset_session_cost` - Reset session cost tracking
- `GET /api/database_stats` - Includes cost information
- `POST /api/add_cost` - Manually add cost (for testing)

## 💡 Budget Recommendations

### Typical Collection Costs (80 articles)
- **Standard Collection**: ~$0.24 using Perplexity
- **Targeted Collection**: ~$0.15-0.30 depending on complexity
- **Student Intelligence**: ~$0.20-0.35 for specialized queries

### Monthly Budget Scenarios
| Budget | Collections/Month | Frequency | Best For |
|--------|------------------|-----------|----------|
| $25    | ~104             | Daily     | Development/Testing |
| $50    | ~208             | Multiple Daily | Regular Monitoring |
| $100   | ~416             | Continuous | Full Research Operation |
| $200   | ~833             | High Frequency | Enterprise Usage |

### Cost Optimization Tips
1. **Use Targeted Collections**: Focus on specific categories to reduce redundant queries
2. **Monitor Cost per Article**: Aim for <$0.003 per article
3. **Reset Session Costs**: Track individual run costs for optimization
4. **Batch Collections**: Run larger collections less frequently vs. small frequent ones

## 📈 Understanding Cost Analysis Output

### Current Costs Section
```
📊 CURRENT COSTS:
   Total Historical Cost: $12.34    # All-time API spending
   Today's Cost:         $2.45      # Today's spending
   This Month's Cost:    $15.67     # Current month total
```

### API Usage Breakdown
```
🔌 API USAGE BREAKDOWN:
   PERPLEXITY:
     • Calls:    150           # Number of API calls made
     • Tokens:   125,000       # Total tokens processed
     • Cost:     $0.125        # Total cost for this API
     • Per Call: $0.0008       # Average cost per call
```

### Budget Analysis
```
💡 BUDGET ANALYSIS ($100/month):
   Monthly Budget:       $100.00    # Your set budget
   Current Usage:        $15.67     # Spent so far this month
   Budget Remaining:     $84.33     # Available budget
   Budget Utilization:   15.7%      # Percentage used
   Daily Average:        $0.78      # Average daily spend
   Projected Monthly:    $24.18     # Projected month total
```

### Collection Frequency Recommendations
```
🎯 COLLECTION FREQUENCY RECOMMENDATIONS:
   With $100.0 budget:
     • ~416 full collections per month     # Maximum possible
     • ~104.0 collections per week         # Weekly allocation
     • One collection every 0.1 days      # Frequency
```

## 🔧 Advanced Features

### Historical Cost Tracking
All costs are stored in `data/costs/cost_tracking.json`:
- Daily cost breakdowns
- API-specific usage patterns
- Token consumption trends
- Cost per collection metrics

### Integration with Collection Scripts
Cost tracking is automatically integrated with:
- `collect_comprehensive.py`
- `collect_targeted_sources.py`
- `collect_student_intelligence.py`

### Real-Time Updates
The status dashboard receives real-time cost updates via Server-Sent Events (SSE), showing:
- Live cost accumulation during collection
- Updated budget analysis
- Cost efficiency metrics

## 🚨 Budget Monitoring Alerts

### Dashboard Indicators
- **Green**: Well within budget (< 50% utilization)
- **Yellow**: Moderate usage (50-80% utilization)
- **Red**: High usage (> 80% utilization)

### Automated Recommendations
The system provides automatic recommendations based on:
- Current spending velocity
- Historical efficiency
- Budget constraints
- Collection goals

## 📝 Best Practices

### 1. Budget Setting
- **Development**: $25-50/month
- **Research**: $100-200/month
- **Production**: $200-500/month

### 2. Cost Monitoring
- Check dashboard before major collections
- Run cost analysis weekly
- Reset session costs between projects
- Monitor cost per article trends

### 3. Optimization Strategies
- Use targeted collections for focused research
- Avoid overlapping queries
- Monitor duplicate detection effectiveness
- Adjust query complexity based on cost efficiency

## 🔍 Troubleshooting

### Common Issues
1. **Cost not updating**: Restart the status server
2. **High cost per article**: Review query complexity and duplication
3. **Budget alerts**: Check `analyze_costs.py` for detailed breakdown

### Support Commands
```bash
# Reset all cost tracking
rm data/costs/cost_tracking.json

# View raw cost data
cat data/costs/cost_tracking.json

# Test cost tracking
python -c "from aih.utils.cost_tracker import cost_tracker; print(cost_tracker.costs)"
```

## 📊 Cost Tracking Integration

The cost tracking system integrates seamlessly with:
- **Status Dashboard**: Real-time updates
- **Collection Scripts**: Automatic tracking
- **Report Generation**: Cost analysis in reports
- **Budget Management**: Automated recommendations

---

*For questions about cost tracking, check the logs or run `python analyze_costs.py --help`* 