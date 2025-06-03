#!/usr/bin/env python3
"""
Enhanced Collection Monitoring System

Provides real-time monitoring and analysis of collection activities including:
- Live collection metrics and performance tracking
- Source health and reliability assessment  
- Collection efficiency and success rate analysis
- Real-time alerts for collection issues
- Historical performance trending

Usage:
    python scripts/analysis/collection_monitoring.py
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

class CollectionMonitor:
    """
    Advanced monitoring system for collection activities and performance analysis.
    Provides real-time insights into collection health, source performance, and operational metrics.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.quality_ranker = DocumentQualityRanker()
        self.artifacts = []
        self.collection_metrics = {}
        
    def load_recent_data(self, hours: int = 24):
        """Load recent collection data for analysis."""
        print(f"Loading collection data from the last {hours} hours...")
        
        # Calculate time threshold
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        # Get all artifacts
        self.artifacts = self.db.get_artifacts(limit=1000)
        
        # Filter to recent artifacts
        recent_artifacts = []
        for artifact in self.artifacts:
            if artifact.get('collected_at'):
                try:
                    if isinstance(artifact['collected_at'], str):
                        collected_time = datetime.fromisoformat(artifact['collected_at'].replace('Z', '+00:00'))
                    else:
                        collected_time = artifact['collected_at']
                    
                    if collected_time >= time_threshold:
                        recent_artifacts.append(artifact)
                except:
                    continue
        
        self.artifacts = recent_artifacts
        print(f"   Found {len(self.artifacts)} articles collected in the last {hours} hours")
        
        return len(self.artifacts)
    
    def analyze_collection_velocity(self) -> Dict[str, Any]:
        """Analyze collection rate and velocity over time."""
        print("\n📈 Analyzing Collection Velocity...")
        
        # Group by hour
        hourly_collections = defaultdict(int)
        source_type_velocity = defaultdict(int)
        
        for artifact in self.artifacts:
            if artifact.get('collected_at'):
                try:
                    if isinstance(artifact['collected_at'], str):
                        collected_time = datetime.fromisoformat(artifact['collected_at'].replace('Z', '+00:00'))
                    else:
                        collected_time = artifact['collected_at']
                    
                    hour_key = collected_time.strftime('%Y-%m-%d %H:00')
                    hourly_collections[hour_key] += 1
                    
                    source_type = artifact.get('source_type', 'unknown')
                    source_type_velocity[source_type] += 1
                    
                except:
                    continue
        
        # Calculate metrics
        total_collections = len(self.artifacts)
        hours_active = len(hourly_collections) if hourly_collections else 1
        avg_per_hour = total_collections / hours_active if hours_active > 0 else 0
        
        # Find peak collection hours
        peak_hour = max(hourly_collections.items(), key=lambda x: x[1]) if hourly_collections else ("N/A", 0)
        
        velocity_analysis = {
            'total_collections': total_collections,
            'hours_active': hours_active,
            'avg_per_hour': round(avg_per_hour, 2),
            'peak_hour': peak_hour[0],
            'peak_collections': peak_hour[1],
            'hourly_breakdown': dict(sorted(hourly_collections.items())),
            'source_type_velocity': dict(sorted(source_type_velocity.items(), key=lambda x: x[1], reverse=True))
        }
        
        print(f"   📊 Collection Rate: {avg_per_hour:.1f} articles/hour")
        print(f"   🔥 Peak Hour: {peak_hour[0]} ({peak_hour[1]} articles)")
        print(f"   ⚡ Most Active Source: {max(source_type_velocity.items(), key=lambda x: x[1])[0] if source_type_velocity else 'None'}")
        
        return velocity_analysis
    
    def analyze_source_health(self) -> Dict[str, Any]:
        """Analyze health and reliability of collection sources."""
        print("\n🏥 Analyzing Source Health...")
        
        source_metrics = defaultdict(lambda: {
            'total_attempts': 0,
            'successful_collections': 0,
            'avg_quality': 0,
            'quality_scores': [],
            'last_successful': None,
            'collection_times': []
        })
        
        for artifact in self.artifacts:
            try:
                # Extract domain from URL
                domain = 'unknown'
                if artifact.get('url'):
                    parsed_url = urlparse(artifact['url'])
                    domain = parsed_url.netloc.lower()
                
                # Calculate quality score
                quality_score, _ = self.quality_ranker.calculate_document_score(artifact)
                
                # Update metrics
                source_metrics[domain]['total_attempts'] += 1
                source_metrics[domain]['successful_collections'] += 1
                source_metrics[domain]['quality_scores'].append(quality_score)
                
                if artifact.get('collected_at'):
                    collection_time = artifact['collected_at']
                    if isinstance(collection_time, str):
                        collection_time = datetime.fromisoformat(collection_time.replace('Z', '+00:00'))
                    
                    source_metrics[domain]['collection_times'].append(collection_time)
                    
                    if (source_metrics[domain]['last_successful'] is None or 
                        collection_time > source_metrics[domain]['last_successful']):
                        source_metrics[domain]['last_successful'] = collection_time
                        
            except Exception as e:
                print(f"   ⚠️  Error processing artifact: {e}")
                continue
        
        # Calculate health scores
        source_health = {}
        for domain, metrics in source_metrics.items():
            if metrics['quality_scores']:
                avg_quality = statistics.mean(metrics['quality_scores'])
                quality_consistency = 1 - (statistics.stdev(metrics['quality_scores']) 
                                         if len(metrics['quality_scores']) > 1 else 0)
                
                # Calculate collection frequency (collections per hour)
                if len(metrics['collection_times']) > 1:
                    time_span = (max(metrics['collection_times']) - min(metrics['collection_times'])).total_seconds() / 3600
                    frequency = len(metrics['collection_times']) / max(time_span, 1)
                else:
                    frequency = 0
                
                # Calculate overall health score (0-1)
                health_score = (avg_quality * 0.4 + quality_consistency * 0.3 + min(frequency/10, 1) * 0.3)
                
                source_health[domain] = {
                    'collections': metrics['successful_collections'],
                    'avg_quality': round(avg_quality, 3),
                    'quality_consistency': round(quality_consistency, 3),
                    'frequency_per_hour': round(frequency, 2),
                    'health_score': round(health_score, 3),
                    'health_grade': self._get_health_grade(health_score),
                    'last_successful': metrics['last_successful'].strftime('%Y-%m-%d %H:%M') if metrics['last_successful'] else 'Never'
                }
        
        # Sort by health score
        healthy_sources = sorted(source_health.items(), key=lambda x: x[1]['health_score'], reverse=True)
        
        print("   🏆 Top Healthy Sources:")
        for domain, health in healthy_sources[:5]:
            print(f"   {domain:30} | Health: {health['health_score']:.3f} | Quality: {health['avg_quality']:.3f} | Collections: {health['collections']}")
        
        return {
            'source_health_scores': dict(healthy_sources),
            'total_sources': len(source_health),
            'healthy_sources': len([s for s in source_health.values() if s['health_score'] >= 0.7]),
            'concerning_sources': len([s for s in source_health.values() if s['health_score'] < 0.5])
        }
    
    def analyze_collection_efficiency(self) -> Dict[str, Any]:
        """Analyze collection efficiency and success patterns."""
        print("\n⚡ Analyzing Collection Efficiency...")
        
        # Analyze by AI impact category
        category_efficiency = defaultdict(lambda: {
            'total': 0,
            'quality_scores': [],
            'processing_success': 0
        })
        
        # Analyze by time periods
        time_period_efficiency = defaultdict(lambda: {
            'collections': 0,
            'avg_quality': 0,
            'quality_scores': []
        })
        
        for artifact in self.artifacts:
            try:
                # Parse metadata
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                category = metadata.get('ai_impact_category', 'unknown')
                
                # Calculate quality score
                quality_score, _ = self.quality_ranker.calculate_document_score(artifact)
                
                # Update category metrics
                category_efficiency[category]['total'] += 1
                category_efficiency[category]['quality_scores'].append(quality_score)
                
                if metadata.get('ai_impact_category'):  # Successfully processed
                    category_efficiency[category]['processing_success'] += 1
                
                # Update time period metrics
                if artifact.get('collected_at'):
                    collection_time = artifact['collected_at']
                    if isinstance(collection_time, str):
                        collection_time = datetime.fromisoformat(collection_time.replace('Z', '+00:00'))
                    
                    hour_of_day = collection_time.hour
                    time_period = self._get_time_period(hour_of_day)
                    
                    time_period_efficiency[time_period]['collections'] += 1
                    time_period_efficiency[time_period]['quality_scores'].append(quality_score)
                    
            except Exception as e:
                continue
        
        # Calculate efficiency metrics
        efficiency_analysis = {
            'category_performance': {},
            'time_period_performance': {},
            'overall_efficiency': {}
        }
        
        # Category performance
        for category, metrics in category_efficiency.items():
            if metrics['quality_scores']:
                avg_quality = statistics.mean(metrics['quality_scores'])
                processing_rate = metrics['processing_success'] / metrics['total'] if metrics['total'] > 0 else 0
                
                efficiency_analysis['category_performance'][category] = {
                    'collections': metrics['total'],
                    'avg_quality': round(avg_quality, 3),
                    'processing_success_rate': round(processing_rate, 3),
                    'efficiency_score': round((avg_quality * 0.6 + processing_rate * 0.4), 3)
                }
        
        # Time period performance
        for period, metrics in time_period_efficiency.items():
            if metrics['quality_scores']:
                avg_quality = statistics.mean(metrics['quality_scores'])
                efficiency_analysis['time_period_performance'][period] = {
                    'collections': metrics['collections'],
                    'avg_quality': round(avg_quality, 3)
                }
        
        # Overall efficiency
        all_quality_scores = [s for metrics in category_efficiency.values() for s in metrics['quality_scores']]
        total_processed = sum(metrics['processing_success'] for metrics in category_efficiency.values())
        total_attempted = sum(metrics['total'] for metrics in category_efficiency.values())
        
        if all_quality_scores:
            overall_avg_quality = statistics.mean(all_quality_scores)
            overall_processing_rate = total_processed / total_attempted if total_attempted > 0 else 0
            
            efficiency_analysis['overall_efficiency'] = {
                'avg_quality': round(overall_avg_quality, 3),
                'processing_success_rate': round(overall_processing_rate, 3),
                'total_collections': len(self.artifacts),
                'efficiency_grade': self._get_efficiency_grade(overall_avg_quality, overall_processing_rate)
            }
        
        print(f"   📊 Overall Processing Rate: {efficiency_analysis['overall_efficiency'].get('processing_success_rate', 0):.1%}")
        print(f"   🎯 Average Quality: {efficiency_analysis['overall_efficiency'].get('avg_quality', 0):.3f}")
        print(f"   📈 Efficiency Grade: {efficiency_analysis['overall_efficiency'].get('efficiency_grade', 'Unknown')}")
        
        return efficiency_analysis
    
    def detect_collection_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies and potential issues in collection patterns."""
        print("\n🚨 Detecting Collection Anomalies...")
        
        anomalies = {
            'quality_drops': [],
            'source_failures': [],
            'volume_anomalies': [],
            'processing_issues': []
        }
        
        # Quality drop detection
        recent_quality_scores = []
        for artifact in self.artifacts[-20:]:  # Last 20 articles
            try:
                quality_score, _ = self.quality_ranker.calculate_document_score(artifact)
                recent_quality_scores.append(quality_score)
            except:
                continue
        
        if len(recent_quality_scores) >= 10:
            recent_avg = statistics.mean(recent_quality_scores[-10:])
            overall_avg = statistics.mean(recent_quality_scores)
            
            if recent_avg < overall_avg - 0.1:  # Quality drop threshold
                anomalies['quality_drops'].append({
                    'type': 'Recent Quality Drop',
                    'recent_avg': round(recent_avg, 3),
                    'overall_avg': round(overall_avg, 3),
                    'severity': 'High' if recent_avg < overall_avg - 0.2 else 'Medium'
                })
        
        # Source failure detection
        source_last_success = {}
        for artifact in self.artifacts:
            if artifact.get('url'):
                domain = urlparse(artifact['url']).netloc.lower()
                if artifact.get('collected_at'):
                    collection_time = artifact['collected_at']
                    if isinstance(collection_time, str):
                        collection_time = datetime.fromisoformat(collection_time.replace('Z', '+00:00'))
                    
                    if domain not in source_last_success or collection_time > source_last_success[domain]:
                        source_last_success[domain] = collection_time
        
        # Check for sources not seen recently
        time_threshold = datetime.now() - timedelta(hours=6)
        for domain, last_seen in source_last_success.items():
            if last_seen < time_threshold:
                hours_ago = (datetime.now() - last_seen).total_seconds() / 3600
                anomalies['source_failures'].append({
                    'source': domain,
                    'last_seen': last_seen.strftime('%Y-%m-%d %H:%M'),
                    'hours_ago': round(hours_ago, 1)
                })
        
        # Volume anomaly detection
        hourly_counts = defaultdict(int)
        for artifact in self.artifacts:
            if artifact.get('collected_at'):
                try:
                    collection_time = artifact['collected_at']
                    if isinstance(collection_time, str):
                        collection_time = datetime.fromisoformat(collection_time.replace('Z', '+00:00'))
                    
                    hour_key = collection_time.strftime('%H')
                    hourly_counts[hour_key] += 1
                except:
                    continue
        
        if hourly_counts:
            avg_hourly = statistics.mean(hourly_counts.values())
            for hour, count in hourly_counts.items():
                if count < avg_hourly * 0.3:  # Very low collection hour
                    anomalies['volume_anomalies'].append({
                        'hour': hour,
                        'collections': count,
                        'expected': round(avg_hourly, 1),
                        'type': 'Low Volume'
                    })
        
        print(f"   🔍 Found {len(anomalies['quality_drops'])} quality issues")
        print(f"   📡 Found {len(anomalies['source_failures'])} source issues")
        print(f"   📉 Found {len(anomalies['volume_anomalies'])} volume anomalies")
        
        return anomalies
    
    def generate_monitoring_report(self) -> str:
        """Generate comprehensive monitoring report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Run all analyses
        velocity = self.analyze_collection_velocity()
        source_health = self.analyze_source_health()
        efficiency = self.analyze_collection_efficiency()
        anomalies = self.detect_collection_anomalies()
        
        report = f"""
# 📊 Collection Monitoring Report

**Generated:** {timestamp}
**Monitoring Period:** Last 24 hours
**Total Collections Analyzed:** {len(self.artifacts)}

## 🚀 Collection Velocity Analysis

- **Average Rate:** {velocity['avg_per_hour']} articles/hour
- **Peak Performance:** {velocity['peak_hour']} ({velocity['peak_collections']} articles)
- **Active Collection Hours:** {velocity['hours_active']}
- **Most Active Source Type:** {max(velocity['source_type_velocity'].items(), key=lambda x: x[1])[0] if velocity['source_type_velocity'] else 'None'}

### Hourly Collection Pattern
| Hour | Collections |
|------|-------------|"""

        for hour, count in list(velocity['hourly_breakdown'].items())[-12:]:  # Last 12 hours
            report += f"""
| {hour} | {count} |"""

        report += f"""

## 🏥 Source Health Dashboard

- **Total Active Sources:** {source_health['total_sources']}
- **Healthy Sources (≥0.7):** {source_health['healthy_sources']}
- **Concerning Sources (<0.5):** {source_health['concerning_sources']}

### Top Performing Sources
| Source | Health Score | Quality | Collections | Last Success |
|--------|--------------|---------|-------------|--------------|"""

        for domain, health in list(source_health['source_health_scores'].items())[:5]:
            report += f"""
| {domain} | {health['health_score']:.3f} | {health['avg_quality']:.3f} | {health['collections']} | {health['last_successful']} |"""

        report += f"""

## ⚡ Collection Efficiency Metrics

- **Overall Quality:** {efficiency['overall_efficiency'].get('avg_quality', 0):.3f}
- **Processing Success Rate:** {efficiency['overall_efficiency'].get('processing_success_rate', 0):.1%}
- **Efficiency Grade:** {efficiency['overall_efficiency'].get('efficiency_grade', 'Unknown')}

### Performance by AI Impact Category
| Category | Collections | Avg Quality | Success Rate | Efficiency |
|----------|-------------|-------------|--------------|------------|"""

        for category, metrics in efficiency['category_performance'].items():
            report += f"""
| {category} | {metrics['collections']} | {metrics['avg_quality']:.3f} | {metrics['processing_success_rate']:.1%} | {metrics['efficiency_score']:.3f} |"""

        report += f"""

## 🚨 Anomaly Detection

### Quality Issues
"""
        if anomalies['quality_drops']:
            for issue in anomalies['quality_drops']:
                report += f"- **{issue['type']}**: Recent avg {issue['recent_avg']:.3f} vs overall {issue['overall_avg']:.3f} (Severity: {issue['severity']})\n"
        else:
            report += "- ✅ No quality issues detected\n"

        report += f"""
### Source Issues
"""
        if anomalies['source_failures']:
            for issue in anomalies['source_failures'][:5]:  # Top 5 issues
                report += f"- **{issue['source']}**: Last seen {issue['hours_ago']:.1f} hours ago\n"
        else:
            report += "- ✅ All sources active\n"

        report += f"""
### Volume Anomalies
"""
        if anomalies['volume_anomalies']:
            for issue in anomalies['volume_anomalies']:
                report += f"- **Hour {issue['hour']}**: Only {issue['collections']} collections (expected ~{issue['expected']})\n"
        else:
            report += "- ✅ Normal collection volumes\n"

        report += f"""

## 📈 Real-Time Recommendations

"""

        # Generate smart recommendations
        recommendations = self._generate_recommendations(velocity, source_health, efficiency, anomalies)
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"

        report += f"""

---

*This monitoring report provides real-time insights into collection performance. Use these metrics to optimize collection strategies and maintain system health.*
"""

        return report

    def _get_health_grade(self, score: float) -> str:
        """Convert health score to grade."""
        if score >= 0.8:
            return 'Excellent'
        elif score >= 0.6:
            return 'Good'
        elif score >= 0.4:
            return 'Fair'
        else:
            return 'Poor'
    
    def _get_efficiency_grade(self, quality: float, processing_rate: float) -> str:
        """Calculate efficiency grade from quality and processing rate."""
        combined_score = quality * 0.6 + processing_rate * 0.4
        if combined_score >= 0.8:
            return 'Excellent'
        elif combined_score >= 0.6:
            return 'Good'
        elif combined_score >= 0.4:
            return 'Fair'
        else:
            return 'Poor'
    
    def _get_time_period(self, hour: int) -> str:
        """Get time period for hour of day."""
        if 6 <= hour < 12:
            return 'Morning'
        elif 12 <= hour < 18:
            return 'Afternoon'
        elif 18 <= hour < 24:
            return 'Evening'
        else:
            return 'Night'
    
    def _generate_recommendations(self, velocity, source_health, efficiency, anomalies) -> List[str]:
        """Generate smart recommendations based on monitoring results."""
        recommendations = []
        
        # Velocity recommendations
        if velocity['avg_per_hour'] < 5:
            recommendations.append("🚀 Collection rate is low (<5/hour). Consider increasing collection frequency or adding more sources.")
        
        # Source health recommendations
        if source_health['concerning_sources'] > 0:
            recommendations.append(f"🏥 {source_health['concerning_sources']} sources showing poor health. Review and potentially replace underperforming sources.")
        
        # Quality recommendations
        overall_quality = efficiency['overall_efficiency'].get('avg_quality', 0)
        if overall_quality < 0.7:
            recommendations.append("📈 Overall quality below 0.7. Focus collection on higher-quality sources identified in health analysis.")
        
        # Anomaly-based recommendations
        if anomalies['quality_drops']:
            recommendations.append("⚠️ Recent quality drop detected. Investigate recent collection changes or source issues.")
        
        if anomalies['source_failures']:
            recommendations.append("📡 Some sources haven't been active recently. Check collection system and source availability.")
        
        # Efficiency recommendations
        processing_rate = efficiency['overall_efficiency'].get('processing_success_rate', 0)
        if processing_rate < 0.8:
            recommendations.append("⚡ Processing success rate below 80%. Review categorization and processing pipeline.")
        
        # Default recommendation if all is well
        if not recommendations:
            recommendations.append("✅ Collection system operating optimally. Continue current collection strategy.")
        
        return recommendations

def main():
    """Run the collection monitoring analysis."""
    print("Starting Enhanced Collection Monitoring...")
    print("=" * 60)
    
    monitor = CollectionMonitor()
    
    # Load recent data (last 24 hours)
    data_count = monitor.load_recent_data(hours=24)
    
    if data_count == 0:
        print("No recent collection data available for monitoring")
        return
    
    # Generate comprehensive monitoring report
    report = monitor.generate_monitoring_report()
    
    # Save report
    report_dir = Path('data/reports')
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f'collection_monitoring_{timestamp}.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nMonitoring complete!")
    print(f"Report saved to: {report_file}")
    print(f"Analyzed {data_count} recent collections")
    
    # Print executive summary
    print("\n" + "=" * 60)
    print("COLLECTION HEALTH SUMMARY")
    print("=" * 60)
    
    # Quick health check
    velocity = monitor.analyze_collection_velocity()
    source_health = monitor.analyze_source_health()
    efficiency = monitor.analyze_collection_efficiency()
    
    print(f"Collection Rate: {velocity['avg_per_hour']:.1f} articles/hour")
    print(f"Source Health: {source_health['healthy_sources']}/{source_health['total_sources']} sources healthy")
    print(f"Quality Score: {efficiency['overall_efficiency'].get('avg_quality', 0):.3f}")
    print(f"Efficiency: {efficiency['overall_efficiency'].get('efficiency_grade', 'Unknown')}")

if __name__ == "__main__":
    main() 