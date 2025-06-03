#!/usr/bin/env python3
"""
Quality Distribution Analysis Tool

Analyzes the distribution and trends of document quality scores across:
- AI impact categories (replace, augment, new_tasks, human_only)
- Source types and domains
- Collection timeline
- Content characteristics

Provides actionable insights for improving collection quality and identifying
the most valuable sources and categories.

Usage:
    python scripts/analysis/quality_distribution_analysis.py
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Any
import statistics

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.utils.database import DatabaseManager
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

class QualityDistributionAnalyzer:
    """
    Analyzes quality score distribution across multiple dimensions to provide
    insights into content quality patterns and collection effectiveness.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.quality_ranker = DocumentQualityRanker()
        self.artifacts = []
        self.quality_data = []
        
    def load_data(self):
        """Load all artifacts and calculate quality scores."""
        print("Loading artifacts and calculating quality scores...")
        
        self.artifacts = self.db.get_artifacts(limit=1000)  # Get all artifacts
        print(f"   Found {len(self.artifacts)} total artifacts")
        
        # Calculate quality scores for all artifacts
        for i, artifact in enumerate(self.artifacts):
            try:
                quality_score, detailed_scores = self.quality_ranker.calculate_document_score(artifact)
                
                # Parse metadata
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                
                # Extract domain from URL
                domain = 'unknown'
                try:
                    parsed_url = urlparse(artifact.get('url', ''))
                    domain = parsed_url.netloc.lower()
                except:
                    pass
                
                quality_item = {
                    'artifact_id': artifact.get('id'),
                    'title': artifact.get('title', '')[:100],
                    'url': artifact.get('url', ''),
                    'domain': domain,
                    'source_type': artifact.get('source_type', 'unknown'),
                    'category': metadata.get('ai_impact_category', 'unknown'),
                    'content_length': len(artifact.get('content', '')),
                    'collected_at': artifact.get('collected_at'),
                    'quality_score': round(quality_score, 3),
                    'detailed_scores': detailed_scores,
                    'quality_grade': self._get_quality_grade(quality_score)
                }
                
                self.quality_data.append(quality_item)
                
                if (i + 1) % 20 == 0:
                    print(f"   Processed {i + 1}/{len(self.artifacts)} artifacts...")
                    
            except Exception as e:
                print(f"   Error processing artifact {artifact.get('id', 'unknown')}: {e}")
                continue
        
        print(f"Quality analysis complete for {len(self.quality_data)} artifacts")
        
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to grade."""
        if score >= 0.8:
            return 'Excellent'
        elif score >= 0.6:
            return 'Good'
        elif score >= 0.4:
            return 'Fair'
        else:
            return 'Poor'
    
    def analyze_category_distribution(self) -> Dict[str, Any]:
        """Analyze quality distribution by AI impact category."""
        print("\nAnalyzing quality by AI impact category...")
        
        category_stats = defaultdict(list)
        
        for item in self.quality_data:
            category = item['category']
            category_stats[category].append(item['quality_score'])
        
        analysis = {}
        for category, scores in category_stats.items():
            if scores:
                analysis[category] = {
                    'count': len(scores),
                    'avg_quality': round(statistics.mean(scores), 3),
                    'median_quality': round(statistics.median(scores), 3),
                    'min_quality': round(min(scores), 3),
                    'max_quality': round(max(scores), 3),
                    'std_dev': round(statistics.stdev(scores) if len(scores) > 1 else 0, 3),
                    'excellent_count': len([s for s in scores if s >= 0.8]),
                    'good_count': len([s for s in scores if 0.6 <= s < 0.8]),
                    'fair_count': len([s for s in scores if 0.4 <= s < 0.6]),
                    'poor_count': len([s for s in scores if s < 0.4])
                }
        
        # Sort by average quality
        sorted_categories = sorted(analysis.items(), key=lambda x: x[1]['avg_quality'], reverse=True)
        
        print("   Category Quality Rankings:")
        for category, stats in sorted_categories:
            print(f"   {category:12} | Avg: {stats['avg_quality']:.3f} | Count: {stats['count']:3d} | Excellent: {stats['excellent_count']:2d}")
        
        return dict(sorted_categories)
    
    def analyze_source_quality(self) -> Dict[str, Any]:
        """Analyze quality by source domain and type."""
        print("\nAnalyzing quality by source...")
        
        # Group by domain
        domain_stats = defaultdict(list)
        source_type_stats = defaultdict(list)
        
        for item in self.quality_data:
            domain_stats[item['domain']].append(item['quality_score'])
            source_type_stats[item['source_type']].append(item['quality_score'])
        
        # Analyze domains (only those with 3+ articles)
        domain_analysis = {}
        for domain, scores in domain_stats.items():
            if len(scores) >= 3:  # Only analyze domains with sufficient data
                domain_analysis[domain] = {
                    'count': len(scores),
                    'avg_quality': round(statistics.mean(scores), 3),
                    'median_quality': round(statistics.median(scores), 3),
                    'consistency': round(1 - (statistics.stdev(scores) if len(scores) > 1 else 0), 3)
                }
        
        # Sort by average quality
        top_domains = sorted(domain_analysis.items(), key=lambda x: x[1]['avg_quality'], reverse=True)[:10]
        
        print("   Top Quality Domains (3+ articles):")
        for domain, stats in top_domains:
            print(f"   {domain:30} | Avg: {stats['avg_quality']:.3f} | Count: {stats['count']:2d} | Consistency: {stats['consistency']:.3f}")
        
        # Analyze source types
        source_analysis = {}
        for source_type, scores in source_type_stats.items():
            if scores:
                source_analysis[source_type] = {
                    'count': len(scores),
                    'avg_quality': round(statistics.mean(scores), 3),
                    'median_quality': round(statistics.median(scores), 3)
                }
        
        return {
            'domains': dict(top_domains),
            'source_types': source_analysis
        }
    
    def analyze_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends over time."""
        print("\nAnalyzing quality trends over time...")
        
        # Group by collection date (by day)
        daily_stats = defaultdict(list)
        
        for item in self.quality_data:
            if item.get('collected_at'):
                try:
                    # Parse date and group by day
                    if isinstance(item['collected_at'], str):
                        date_obj = datetime.fromisoformat(item['collected_at'].replace('Z', '+00:00'))
                    else:
                        date_obj = item['collected_at']
                    
                    date_key = date_obj.strftime('%Y-%m-%d')
                    daily_stats[date_key].append(item['quality_score'])
                except:
                    continue
        
        # Calculate daily averages
        daily_averages = {}
        for date, scores in daily_stats.items():
            if scores:
                daily_averages[date] = {
                    'avg_quality': round(statistics.mean(scores), 3),
                    'count': len(scores),
                    'date': date
                }
        
        # Sort by date
        sorted_dates = sorted(daily_averages.items())
        
        # Calculate trend
        if len(sorted_dates) >= 2:
            first_week_avg = statistics.mean([stats['avg_quality'] for date, stats in sorted_dates[:7]])
            last_week_avg = statistics.mean([stats['avg_quality'] for date, stats in sorted_dates[-7:]])
            trend = "Improving" if last_week_avg > first_week_avg else "Declining" if last_week_avg < first_week_avg else "Stable"
        else:
            trend = "Insufficient data"
        
        print(f"   Quality trend: {trend}")
        if sorted_dates:
            print(f"   Recent daily averages:")
            for date, stats in sorted_dates[-5:]:  # Last 5 days
                print(f"   {date} | Avg: {stats['avg_quality']:.3f} | Count: {stats['count']:2d}")
        
        return {
            'daily_averages': dict(sorted_dates),
            'trend': trend,
            'total_days': len(sorted_dates)
        }
    
    def analyze_content_characteristics(self) -> Dict[str, Any]:
        """Analyze relationship between content characteristics and quality."""
        print("\nAnalyzing content characteristics vs quality...")
        
        # Group by content length ranges
        length_ranges = {
            'Very Short (0-500)': (0, 500),
            'Short (500-1500)': (500, 1500),
            'Medium (1500-5000)': (1500, 5000),
            'Long (5000-15000)': (5000, 15000),
            'Very Long (15000+)': (15000, float('inf'))
        }
        
        length_analysis = {}
        for range_name, (min_len, max_len) in length_ranges.items():
            scores = [item['quality_score'] for item in self.quality_data 
                     if min_len <= item['content_length'] < max_len]
            
            if scores:
                length_analysis[range_name] = {
                    'count': len(scores),
                    'avg_quality': round(statistics.mean(scores), 3),
                    'median_quality': round(statistics.median(scores), 3)
                }
        
        print("   Quality by Content Length:")
        for range_name, stats in length_analysis.items():
            print(f"   {range_name:20} | Avg: {stats['avg_quality']:.3f} | Count: {stats['count']:3d}")
        
        return length_analysis
    
    def generate_recommendations(self, category_analysis: Dict, source_analysis: Dict, 
                               trend_analysis: Dict, content_analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Category recommendations
        if category_analysis:
            best_category = max(category_analysis.items(), key=lambda x: x[1]['avg_quality'])
            worst_category = min(category_analysis.items(), key=lambda x: x[1]['avg_quality'])
            
            recommendations.append(f"🎯 Focus more collection on '{best_category[0]}' category (avg quality: {best_category[1]['avg_quality']:.3f})")
            
            if worst_category[1]['avg_quality'] < 0.5:
                recommendations.append(f"⚠️  Review collection strategy for '{worst_category[0]}' category (avg quality: {worst_category[1]['avg_quality']:.3f})")
        
        # Source recommendations
        if source_analysis.get('domains'):
            top_domain = max(source_analysis['domains'].items(), key=lambda x: x[1]['avg_quality'])
            recommendations.append(f"🌟 Prioritize content from '{top_domain[0]}' (avg quality: {top_domain[1]['avg_quality']:.3f})")
        
        # Content length recommendations
        if content_analysis:
            best_length = max(content_analysis.items(), key=lambda x: x[1]['avg_quality'])
            recommendations.append(f"📄 Target {best_length[0].lower()} content for better quality (avg: {best_length[1]['avg_quality']:.3f})")
        
        # Quality distribution recommendations
        total_excellent = sum(stats['excellent_count'] for stats in category_analysis.values())
        total_articles = sum(stats['count'] for stats in category_analysis.values())
        
        if total_articles > 0:
            excellent_percentage = (total_excellent / total_articles) * 100
            if excellent_percentage < 30:
                recommendations.append(f"📈 Only {excellent_percentage:.1f}% of content is excellent quality - consider stricter source curation")
            else:
                recommendations.append(f"✅ {excellent_percentage:.1f}% excellent quality content - good collection standards")
        
        # Trend recommendations
        if trend_analysis['trend'] == 'Declining':
            recommendations.append("📉 Quality trend is declining - review recent collection sources and strategies")
        elif trend_analysis['trend'] == 'Improving':
            recommendations.append("📈 Quality trend is improving - continue current collection approach")
        
        return recommendations
    
    def generate_report(self) -> str:
        """Generate a comprehensive quality distribution report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Run all analyses
        category_analysis = self.analyze_category_distribution()
        source_analysis = self.analyze_source_quality()
        trend_analysis = self.analyze_quality_trends()
        content_analysis = self.analyze_content_characteristics()
        recommendations = self.generate_recommendations(category_analysis, source_analysis, 
                                                      trend_analysis, content_analysis)
        
        # Calculate overall statistics
        all_scores = [item['quality_score'] for item in self.quality_data]
        overall_avg = statistics.mean(all_scores) if all_scores else 0
        overall_median = statistics.median(all_scores) if all_scores else 0
        
        grade_counts = Counter(item['quality_grade'] for item in self.quality_data)
        
        report = f"""
# 📊 Quality Distribution Analysis Report

**Generated:** {timestamp}
**Total Articles Analyzed:** {len(self.quality_data)}

## 🎯 Overall Quality Summary

- **Average Quality Score:** {overall_avg:.3f}
- **Median Quality Score:** {overall_median:.3f}
- **Quality Distribution:**
  - Excellent (0.8+): {grade_counts.get('Excellent', 0)} articles ({grade_counts.get('Excellent', 0)/len(self.quality_data)*100:.1f}%)
  - Good (0.6-0.8): {grade_counts.get('Good', 0)} articles ({grade_counts.get('Good', 0)/len(self.quality_data)*100:.1f}%)
  - Fair (0.4-0.6): {grade_counts.get('Fair', 0)} articles ({grade_counts.get('Fair', 0)/len(self.quality_data)*100:.1f}%)
  - Poor (0.0-0.4): {grade_counts.get('Poor', 0)} articles ({grade_counts.get('Poor', 0)/len(self.quality_data)*100:.1f}%)

## 📈 Key Insights

### By AI Impact Category
| Category | Avg Quality | Count | Excellent | Good | Fair | Poor |
|----------|-------------|-------|-----------|------|------|------|"""

        for category, stats in category_analysis.items():
            report += f"""
| {category} | {stats['avg_quality']:.3f} | {stats['count']} | {stats['excellent_count']} | {stats['good_count']} | {stats['fair_count']} | {stats['poor_count']} |"""

        report += f"""

### Top Quality Sources
| Domain | Avg Quality | Count | Consistency |
|--------|-------------|--------|-------------|"""

        for domain, stats in list(source_analysis.get('domains', {}).items())[:5]:
            report += f"""
| {domain} | {stats['avg_quality']:.3f} | {stats['count']} | {stats['consistency']:.3f} |"""

        report += f"""

### Quality by Content Length
| Length Range | Avg Quality | Count |
|--------------|-------------|-------|"""

        for range_name, stats in content_analysis.items():
            report += f"""
| {range_name} | {stats['avg_quality']:.3f} | {stats['count']} |"""

        report += f"""

## 🎯 Actionable Recommendations

"""
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"

        report += f"""

## 📊 Quality Trend Analysis

- **Overall Trend:** {trend_analysis['trend']}
- **Data Points:** {trend_analysis['total_days']} days of collection data
- **Collection Consistency:** {'Good' if trend_analysis['total_days'] > 5 else 'Limited data available'}

---

*This analysis helps optimize collection strategies by identifying high-quality sources and content patterns. Use these insights to improve the overall quality of the AI-Horizon intelligence database.*
"""

        return report

def main():
    """Run the quality distribution analysis."""
    print("Starting Quality Distribution Analysis...")
    print("=" * 60)
    
    analyzer = QualityDistributionAnalyzer()
    
    # Load and analyze data
    analyzer.load_data()
    
    if not analyzer.quality_data:
        print("No quality data available for analysis")
        return
    
    # Generate comprehensive report
    report = analyzer.generate_report()
    
    # Save report
    report_dir = Path('data/reports')
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f'quality_distribution_analysis_{timestamp}.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nAnalysis complete!")
    print(f"Report saved to: {report_file}")
    print(f"Analyzed {len(analyzer.quality_data)} articles across {len(set(item['category'] for item in analyzer.quality_data))} categories")
    
    # Print summary to console
    print("\n" + "=" * 60)
    print("EXECUTIVE SUMMARY")
    print("=" * 60)
    
    all_scores = [item['quality_score'] for item in analyzer.quality_data]
    avg_quality = statistics.mean(all_scores)
    excellent_count = len([s for s in all_scores if s >= 0.8])
    
    print(f"Overall Quality: {avg_quality:.3f} ({'Excellent' if avg_quality >= 0.8 else 'Good' if avg_quality >= 0.6 else 'Fair' if avg_quality >= 0.4 else 'Poor'})")
    print(f"Excellent Articles: {excellent_count}/{len(all_scores)} ({excellent_count/len(all_scores)*100:.1f}%)")
    print(f"Collection Quality: {'High standards maintained' if excellent_count/len(all_scores) > 0.3 else 'Room for improvement'}")

if __name__ == "__main__":
    main() 