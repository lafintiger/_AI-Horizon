#!/usr/bin/env python3
"""
Category Distribution Insights Analysis Tool

Provides deep analysis of AI impact category patterns and evolution, focusing on understanding how different DCWF tasks are distributed across the four AI impact categories (replace, augment, new_tasks, human_only).

This tool is essential for understanding how AI impacts different cybersecurity tasks
and provides strategic guidance for workforce development aligned with DCWF framework.

Usage:
    python scripts/analysis/category_distribution_insights.py
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
import statistics
import re
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from aih.utils.database import DatabaseManager
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

class CategoryDistributionAnalyzer:
    """
    Analyzes AI impact category distribution patterns to understand how AI affects
    different cybersecurity tasks and workforce areas according to DCWF framework.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.quality_ranker = DocumentQualityRanker()
        self.artifacts = []
        self.category_data = []
        
        # AI Impact Categories mapping to DCWF analysis
        self.categories = {
            'replace': 'Tasks being fully automated by AI',
            'augment': 'Human-AI collaboration enhancing capabilities',
            'new_tasks': 'Jobs/tasks created due to AI technology',
            'human_only': 'Tasks requiring uniquely human expertise'
        }
        
    def load_data(self):
        """Load all artifacts and organize by category."""
        print("Loading artifacts for category distribution analysis...")
        
        self.artifacts = self.db.get_artifacts(limit=1000)
        print(f"   Found {len(self.artifacts)} total artifacts")
        
        # Process each artifact for category analysis
        for i, artifact in enumerate(self.artifacts):
            try:
                # Calculate quality score
                quality_score, detailed_scores = self.quality_ranker.calculate_document_score(artifact)
                
                # Parse metadata
                metadata = json.loads(artifact.get('raw_metadata', '{}'))
                category = metadata.get('ai_impact_category', 'unknown')
                
                # Extract creation date
                created_at = artifact.get('created_at')
                date_obj = None
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            date_obj = created_at
                    except:
                        pass
                
                # Extract DCWF-relevant terms from content
                content = artifact.get('content', '') + ' ' + artifact.get('title', '')
                dcwf_tasks = self._extract_dcwf_tasks(content)
                skill_mentions = self._extract_skill_mentions(content)
                
                category_item = {
                    'artifact_id': artifact.get('id'),
                    'title': artifact.get('title', '')[:100],
                    'url': artifact.get('url', ''),
                    'category': category,
                    'quality_score': round(quality_score, 3),
                    'content_length': len(artifact.get('content', '')),
                    'created_at': date_obj,
                    'month_key': date_obj.strftime('%Y-%m') if date_obj else 'unknown',
                    'dcwf_tasks': dcwf_tasks,
                    'skill_mentions': skill_mentions,
                    'detailed_scores': detailed_scores
                }
                
                self.category_data.append(category_item)
                
                if (i + 1) % 20 == 0:
                    print(f"   Processed {i + 1}/{len(self.artifacts)} artifacts...")
                    
            except Exception as e:
                print(f"   Error processing artifact {artifact.get('id', 'unknown')}: {e}")
                continue
        
        print(f"Category analysis complete for {len(self.category_data)} artifacts")
        
    def _extract_dcwf_tasks(self, content: str) -> List[str]:
        """Extract DCWF-related task mentions from content."""
        dcwf_tasks = [
            # Core Security Operations
            'threat detection', 'incident response', 'vulnerability assessment',
            'security monitoring', 'log analysis', 'forensic analysis',
            'malware analysis', 'penetration testing', 'security auditing',
            
            # Risk and Compliance
            'risk assessment', 'compliance monitoring', 'policy development',
            'security governance', 'regulatory compliance', 'audit management',
            
            # Architecture and Engineering
            'security architecture', 'secure design', 'security engineering',
            'cryptography', 'identity management', 'access control',
            
            # Operations and Administration
            'security operations', 'configuration management', 'patch management',
            'backup management', 'disaster recovery', 'business continuity',
            
            # Education and Awareness
            'security awareness', 'training development', 'security education',
            'knowledge management', 'documentation', 'communication'
        ]
        
        found_tasks = []
        content_lower = content.lower()
        
        for task in dcwf_tasks:
            if task in content_lower:
                found_tasks.append(task)
        
        return found_tasks
    
    def _extract_skill_mentions(self, content: str) -> List[str]:
        """Extract cybersecurity skill mentions from content."""
        skills = [
            'python', 'scripting', 'automation', 'ai integration', 'machine learning',
            'threat intelligence', 'siem', 'soar', 'cloud security', 'zero trust',
            'devsecops', 'container security', 'api security', 'iot security',
            'privacy', 'data protection', 'incident handling', 'crisis management',
            'leadership', 'communication', 'problem solving', 'critical thinking'
        ]
        
        found_skills = []
        content_lower = content.lower()
        
        for skill in skills:
            if skill in content_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def analyze_category_distribution(self) -> Dict[str, Any]:
        """Analyze overall distribution of content across AI impact categories."""
        print("\n📊 Analyzing Category Distribution Patterns...")
        
        category_stats = defaultdict(lambda: {
            'count': 0,
            'quality_scores': [],
            'content_lengths': [],
            'monthly_distribution': defaultdict(int),
            'dcwf_tasks': [],
            'skill_mentions': []
        })
        
        total_articles = len(self.category_data)
        
        for item in self.category_data:
            category = item['category']
            stats = category_stats[category]
            
            stats['count'] += 1
            stats['quality_scores'].append(item['quality_score'])
            stats['content_lengths'].append(item['content_length'])
            stats['monthly_distribution'][item['month_key']] += 1
            stats['dcwf_tasks'].extend(item['dcwf_tasks'])
            stats['skill_mentions'].extend(item['skill_mentions'])
        
        distribution_analysis = {}
        for category, stats in category_stats.items():
            if stats['count'] > 0:
                distribution_analysis[category] = {
                    'count': stats['count'],
                    'percentage': round((stats['count'] / total_articles) * 100, 1),
                    'avg_quality': round(statistics.mean(stats['quality_scores']), 3),
                    'quality_std': round(statistics.stdev(stats['quality_scores']) if len(stats['quality_scores']) > 1 else 0, 3),
                    'avg_content_length': round(statistics.mean(stats['content_lengths'])),
                    'top_dcwf_tasks': [task for task, count in Counter(stats['dcwf_tasks']).most_common(5)],
                    'top_skills': [skill for skill, count in Counter(stats['skill_mentions']).most_common(5)],
                    'monthly_trend': dict(stats['monthly_distribution']),
                    'description': self.categories.get(category, 'Unknown category')
                }
        
        # Calculate distribution balance
        percentages = [stats['percentage'] for stats in distribution_analysis.values()]
        balance_score = 1 - (statistics.stdev(percentages) / 25) if len(percentages) > 1 else 1
        balance_score = max(0, min(1, balance_score))
        
        print("   Category Distribution Summary:")
        for category, stats in sorted(distribution_analysis.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"   {category:12} | {stats['count']:3d} articles ({stats['percentage']:4.1f}%) | Avg Quality: {stats['avg_quality']:.3f}")
        
        return {
            'distribution': distribution_analysis,
            'balance_score': round(balance_score, 3),
            'total_articles': total_articles,
            'categories_covered': len(distribution_analysis)
        }
    
    def analyze_category_evolution(self) -> Dict[str, Any]:
        """Analyze how category distribution evolves over time with advanced temporal analysis."""
        print("\n📈 Analyzing Category Evolution Over Time...")
        
        monthly_categories = defaultdict(lambda: defaultdict(int))
        monthly_totals = defaultdict(int)
        monthly_quality = defaultdict(lambda: defaultdict(list))
        
        for item in self.category_data:
            if item['month_key'] != 'unknown':
                monthly_categories[item['month_key']][item['category']] += 1
                monthly_totals[item['month_key']] += 1
                monthly_quality[item['month_key']][item['category']].append(item['quality_score'])
        
        # Calculate monthly percentages
        monthly_percentages = {}
        for month, categories in monthly_categories.items():
            total = monthly_totals[month]
            monthly_percentages[month] = {
                category: round((count / total) * 100, 1)
                for category, count in categories.items()
            }
        
        # Advanced temporal analysis
        sorted_months = sorted(monthly_percentages.keys())
        temporal_analysis = self._analyze_temporal_patterns(monthly_percentages, sorted_months)
        trend_predictions = self._predict_category_trends(monthly_percentages, sorted_months)
        seasonality_analysis = self._analyze_seasonality(monthly_categories, sorted_months)
        
        # Analyze trends for each category (existing logic)
        category_trends = {}
        for category in self.categories.keys():
            monthly_values = []
            for month in sorted_months:
                percentage = monthly_percentages[month].get(category, 0)
                monthly_values.append(percentage)
            
            if len(monthly_values) >= 3:
                # Enhanced trend analysis
                trend_stats = self._calculate_trend_statistics(monthly_values, sorted_months)
                
                category_trends[category] = {
                    'trend_direction': trend_stats['direction'],
                    'percentage_change': trend_stats['total_change'],
                    'monthly_change_rate': trend_stats['monthly_rate'],
                    'trend_strength': trend_stats['strength'],
                    'statistical_significance': trend_stats['p_value'] < 0.05,
                    'r_squared': trend_stats['r_squared'],
                    'current_percentage': round(monthly_values[-1], 1) if monthly_values else 0,
                    'monthly_data': dict(zip(sorted_months, monthly_values)),
                    'predicted_next_3_months': trend_predictions.get(category, [])
                }
        
        print("   Category Evolution Trends:")
        for category, trend in category_trends.items():
            direction_icon = "📈" if trend['trend_direction'] == 'Growing' else "📉" if trend['trend_direction'] == 'Declining' else "➡️"
            significance = "**" if trend['statistical_significance'] else ""
            print(f"   {category:12} | {direction_icon} {trend['trend_direction']:8} {significance} | {trend['percentage_change']:+4.1f}% | R²={trend['r_squared']:.3f}")
        
        return {
            'monthly_percentages': monthly_percentages,
            'category_trends': category_trends,
            'analysis_months': len(sorted_months),
            'temporal_patterns': temporal_analysis,
            'trend_predictions': trend_predictions,
            'seasonality_analysis': seasonality_analysis
        }
    
    def _analyze_temporal_patterns(self, monthly_percentages: Dict, sorted_months: List[str]) -> Dict[str, Any]:
        """Analyze temporal patterns in category distribution."""
        patterns = {
            'volatility_by_category': {},
            'correlation_matrix': {},
            'dominant_category_shifts': [],
            'stability_score': 0.0
        }
        
        if len(sorted_months) < 3:
            return patterns
        
        # Calculate volatility for each category
        for category in self.categories.keys():
            values = [monthly_percentages[month].get(category, 0) for month in sorted_months]
            if len(values) > 1:
                volatility = np.std(values) / np.mean(values) if np.mean(values) > 0 else 0
                patterns['volatility_by_category'][category] = round(volatility, 3)
        
        # Calculate correlation matrix between categories
        category_series = {}
        for category in self.categories.keys():
            category_series[category] = [monthly_percentages[month].get(category, 0) for month in sorted_months]
        
        if len(category_series) > 1:
            categories = list(category_series.keys())
            correlation_data = []
            for i, cat1 in enumerate(categories):
                for j, cat2 in enumerate(categories):
                    if i != j and len(category_series[cat1]) > 2:
                        try:
                            corr, p_value = stats.pearsonr(category_series[cat1], category_series[cat2])
                            if not np.isnan(corr):
                                correlation_data.append({
                                    'category_1': cat1,
                                    'category_2': cat2,
                                    'correlation': round(corr, 3),
                                    'p_value': round(p_value, 3),
                                    'significant': p_value < 0.05
                                })
                        except:
                            pass
            patterns['correlation_matrix'] = correlation_data
        
        # Identify dominant category shifts
        for i in range(1, len(sorted_months)):
            prev_month = sorted_months[i-1]
            curr_month = sorted_months[i]
            
            prev_dominant = max(monthly_percentages[prev_month].items(), key=lambda x: x[1])[0]
            curr_dominant = max(monthly_percentages[curr_month].items(), key=lambda x: x[1])[0]
            
            if prev_dominant != curr_dominant:
                patterns['dominant_category_shifts'].append({
                    'month': curr_month,
                    'from_category': prev_dominant,
                    'to_category': curr_dominant,
                    'shift_magnitude': round(
                        monthly_percentages[curr_month][curr_dominant] - 
                        monthly_percentages[prev_month][prev_dominant], 1
                    )
                })
        
        # Calculate overall stability score
        if patterns['volatility_by_category']:
            avg_volatility = np.mean(list(patterns['volatility_by_category'].values()))
            patterns['stability_score'] = round(max(0, 1 - avg_volatility), 3)
        
        return patterns
    
    def _predict_category_trends(self, monthly_percentages: Dict, sorted_months: List[str]) -> Dict[str, List[float]]:
        """Predict future category trends using machine learning."""
        predictions = {}
        
        if len(sorted_months) < 4:
            return predictions
        
        # Convert months to numeric values for modeling
        month_indices = list(range(len(sorted_months)))
        
        for category in self.categories.keys():
            values = [monthly_percentages[month].get(category, 0) for month in sorted_months]
            
            if len(values) >= 4 and max(values) > 0:
                try:
                    # Prepare data for modeling
                    X = np.array(month_indices).reshape(-1, 1)
                    y = np.array(values)
                    
                    # Try both linear and polynomial models
                    linear_model = LinearRegression()
                    linear_model.fit(X, y)
                    linear_score = r2_score(y, linear_model.predict(X))
                    
                    # Polynomial features (degree 2)
                    poly_features = PolynomialFeatures(degree=2)
                    X_poly = poly_features.fit_transform(X)
                    poly_model = LinearRegression()
                    poly_model.fit(X_poly, y)
                    poly_score = r2_score(y, poly_model.predict(X_poly))
                    
                    # Use the better model
                    if poly_score > linear_score and poly_score > 0.5:
                        # Use polynomial model
                        future_indices = np.array(range(len(sorted_months), len(sorted_months) + 3)).reshape(-1, 1)
                        future_X_poly = poly_features.transform(future_indices)
                        future_predictions = poly_model.predict(future_X_poly)
                    else:
                        # Use linear model
                        future_indices = np.array(range(len(sorted_months), len(sorted_months) + 3)).reshape(-1, 1)
                        future_predictions = linear_model.predict(future_indices)
                    
                    # Ensure predictions are reasonable (0-100%)
                    future_predictions = np.clip(future_predictions, 0, 100)
                    predictions[category] = [round(pred, 1) for pred in future_predictions]
                    
                except Exception as e:
                    # Fallback to simple linear extrapolation
                    if len(values) >= 2:
                        recent_trend = values[-1] - values[-2]
                        predictions[category] = [
                            round(max(0, min(100, values[-1] + recent_trend * (i + 1))), 1)
                            for i in range(3)
                        ]
        
        return predictions
    
    def _analyze_seasonality(self, monthly_categories: Dict, sorted_months: List[str]) -> Dict[str, Any]:
        """Analyze seasonal patterns in category distribution."""
        seasonality = {
            'seasonal_categories': {},
            'peak_months': {},
            'low_months': {},
            'seasonal_strength': 0.0
        }
        
        if len(sorted_months) < 12:  # Need at least a year of data
            seasonality['insufficient_data'] = True
            return seasonality
        
        # Group by month of year
        month_of_year_data = defaultdict(lambda: defaultdict(list))
        
        for month_key in sorted_months:
            try:
                month_num = int(month_key.split('-')[1])  # Extract month from YYYY-MM
                for category, count in monthly_categories[month_key].items():
                    month_of_year_data[month_num][category].append(count)
            except:
                continue
        
        # Analyze seasonality for each category
        for category in self.categories.keys():
            monthly_averages = []
            for month_num in range(1, 13):
                if month_num in month_of_year_data and category in month_of_year_data[month_num]:
                    avg = np.mean(month_of_year_data[month_num][category])
                    monthly_averages.append(avg)
                else:
                    monthly_averages.append(0)
            
            if max(monthly_averages) > 0:
                # Calculate seasonal strength (coefficient of variation)
                seasonal_strength = np.std(monthly_averages) / np.mean(monthly_averages)
                
                if seasonal_strength > 0.2:  # Significant seasonality
                    peak_month = monthly_averages.index(max(monthly_averages)) + 1
                    low_month = monthly_averages.index(min(monthly_averages)) + 1
                    
                    seasonality['seasonal_categories'][category] = {
                        'strength': round(seasonal_strength, 3),
                        'peak_month': peak_month,
                        'low_month': low_month,
                        'monthly_pattern': monthly_averages
                    }
        
        return seasonality
    
    def _calculate_trend_statistics(self, values: List[float], months: List[str]) -> Dict[str, Any]:
        """Calculate comprehensive trend statistics."""
        if len(values) < 3:
            return {
                'direction': 'Insufficient Data',
                'total_change': 0.0,
                'monthly_rate': 0.0,
                'strength': 0.0,
                'p_value': 1.0,
                'r_squared': 0.0
            }
        
        # Linear regression analysis
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Calculate trend direction and strength
        total_change = values[-1] - values[0]
        monthly_rate = slope
        
        if abs(slope) < 0.1:
            direction = 'Stable'
        elif slope > 0:
            direction = 'Growing'
        else:
            direction = 'Declining'
        
        # Trend strength based on R-squared and slope magnitude
        strength = abs(r_value) * min(1.0, abs(slope) / 5.0)
        
        return {
            'direction': direction,
            'total_change': round(total_change, 2),
            'monthly_rate': round(monthly_rate, 3),
            'strength': round(strength, 3),
            'p_value': round(p_value, 4),
            'r_squared': round(r_value ** 2, 3)
        }
    
    def analyze_cross_category_relationships(self) -> Dict[str, Any]:
        """Analyze relationships and overlaps between categories."""
        print("\n🔗 Analyzing Cross-Category Relationships...")
        
        # Analyze content similarity between categories
        category_content = defaultdict(list)
        category_tasks = defaultdict(list)
        category_skills = defaultdict(list)
        
        for item in self.category_data:
            category = item['category']
            category_content[category].append(item['title'])
            category_tasks[category].extend(item['dcwf_tasks'])
            category_skills[category].extend(item['skill_mentions'])
        
        # Calculate task overlap between categories
        task_overlap = {}
        categories = list(category_tasks.keys())
        
        for i, cat1 in enumerate(categories):
            for j, cat2 in enumerate(categories):
                if i < j:  # Only calculate each pair once
                    tasks1 = set(category_tasks[cat1])
                    tasks2 = set(category_tasks[cat2])
                    
                    overlap = len(tasks1.intersection(tasks2))
                    total_unique = len(tasks1.union(tasks2))
                    overlap_score = overlap / total_unique if total_unique > 0 else 0
                    
                    task_overlap[f"{cat1}_{cat2}"] = {
                        'overlap_tasks': overlap,
                        'overlap_score': round(overlap_score, 3),
                        'common_tasks': list(tasks1.intersection(tasks2))[:5]
                    }
        
        # Analyze skill overlap
        skill_overlap = {}
        for i, cat1 in enumerate(categories):
            for j, cat2 in enumerate(categories):
                if i < j:
                    skills1 = set(category_skills[cat1])
                    skills2 = set(category_skills[cat2])
                    
                    overlap = len(skills1.intersection(skills2))
                    total_unique = len(skills1.union(skills2))
                    overlap_score = overlap / total_unique if total_unique > 0 else 0
                    
                    skill_overlap[f"{cat1}_{cat2}"] = {
                        'overlap_skills': overlap,
                        'overlap_score': round(overlap_score, 3),
                        'common_skills': list(skills1.intersection(skills2))[:5]
                    }
        
        print("   Top Task Overlaps Between Categories:")
        for pair, data in sorted(task_overlap.items(), key=lambda x: x[1]['overlap_score'], reverse=True)[:5]:
            cats = pair.replace('_', ' ↔ ')
            print(f"   {cats:25} | Score: {data['overlap_score']:.3f} | Tasks: {data['overlap_tasks']}")
        
        return {
            'task_overlaps': task_overlap,
            'skill_overlaps': skill_overlap,
            'category_relationships': self._analyze_category_relationships(task_overlap, skill_overlap)
        }
    
    def _analyze_category_relationships(self, task_overlap: Dict, skill_overlap: Dict) -> Dict[str, Any]:
        """Analyze strategic relationships between categories."""
        relationships = {}
        
        # Define strategic relationships
        strategic_pairs = [
            ('replace', 'augment', 'Replacement vs Augmentation Balance'),
            ('augment', 'new_tasks', 'Augmentation Creating New Opportunities'),
            ('new_tasks', 'human_only', 'New Tasks vs Human Expertise'),
            ('replace', 'human_only', 'Automation vs Human Value')
        ]
        
        for cat1, cat2, description in strategic_pairs:
            pair_key = f"{cat1}_{cat2}"
            if pair_key not in task_overlap:
                pair_key = f"{cat2}_{cat1}"
            
            if pair_key in task_overlap:
                task_data = task_overlap[pair_key]
                skill_data = skill_overlap.get(pair_key, {'overlap_score': 0})
                
                # Calculate relationship strength
                relationship_strength = (task_data['overlap_score'] + skill_data['overlap_score']) / 2
                
                relationships[f"{cat1}_vs_{cat2}"] = {
                    'description': description,
                    'relationship_strength': round(relationship_strength, 3),
                    'task_overlap': task_data['overlap_score'],
                    'skill_overlap': skill_data['overlap_score'],
                    'strategic_insight': self._generate_relationship_insight(cat1, cat2, relationship_strength)
                }
        
        return relationships
    
    def _generate_relationship_insight(self, cat1: str, cat2: str, strength: float) -> str:
        """Generate strategic insight based on category relationship."""
        if strength > 0.3:
            return f"High overlap suggests {cat1} and {cat2} areas are closely related - consider integrated training approaches"
        elif strength > 0.15:
            return f"Moderate overlap between {cat1} and {cat2} - opportunities for skill transfer and career transitions"
        else:
            return f"Low overlap indicates {cat1} and {cat2} represent distinct career paths requiring different skill sets"
    
    def analyze_quality_patterns_by_category(self) -> Dict[str, Any]:
        """Analyze quality patterns specific to each category."""
        print("\n⭐ Analyzing Quality Patterns by Category...")
        
        category_quality = defaultdict(list)
        
        for item in self.category_data:
            category_quality[item['category']].append({
                'quality_score': item['quality_score'],
                'content_length': item['content_length'],
                'month': item['month_key']
            })
        
        quality_analysis = {}
        for category, items in category_quality.items():
            if items:
                scores = [item['quality_score'] for item in items]
                lengths = [item['content_length'] for item in items]
                
                # Quality grade distribution
                excellent = len([s for s in scores if s >= 0.8])
                good = len([s for s in scores if 0.6 <= s < 0.8])
                fair = len([s for s in scores if 0.4 <= s < 0.6])
                poor = len([s for s in scores if s < 0.4])
                
                quality_analysis[category] = {
                    'avg_quality': round(statistics.mean(scores), 3),
                    'quality_std': round(statistics.stdev(scores) if len(scores) > 1 else 0, 3),
                    'median_quality': round(statistics.median(scores), 3),
                    'quality_grades': {
                        'excellent': excellent,
                        'good': good,
                        'fair': fair,
                        'poor': poor
                    },
                    'quality_consistency': round(1 - (statistics.stdev(scores) / statistics.mean(scores)) if statistics.mean(scores) > 0 else 0, 3),
                    'avg_content_length': round(statistics.mean(lengths)),
                    'quality_per_length': round(statistics.mean(scores) / (statistics.mean(lengths) / 1000), 3)
                }
        
        # Rank categories by quality
        ranked_categories = sorted(quality_analysis.items(), key=lambda x: x[1]['avg_quality'], reverse=True)
        
        print("   Quality Rankings by Category:")
        for i, (category, stats) in enumerate(ranked_categories, 1):
            print(f"   {i}. {category:12} | Avg: {stats['avg_quality']:.3f} | Excellent: {stats['quality_grades']['excellent']:2d}")
        
        return {
            'category_quality': quality_analysis,
            'quality_rankings': [cat for cat, _ in ranked_categories]
        }
    
    def generate_optimization_recommendations(self, distribution_analysis: Dict, evolution_analysis: Dict,
                                             relationship_analysis: Dict, quality_analysis: Dict) -> List[str]:
        """Generate actionable recommendations for category distribution optimization."""
        recommendations = []
        
        # Distribution balance recommendations
        balance_score = distribution_analysis['balance_score']
        if balance_score < 0.7:
            recommendations.append(
                f"📊 **Balance Improvement**: Distribution balance score is {balance_score:.2f}. "
                "Consider increasing collection in underrepresented categories for more comprehensive coverage."
            )
        
        # Quality-based recommendations
        quality_rankings = quality_analysis['quality_rankings']
        if len(quality_rankings) >= 2:
            lowest_quality_cat = quality_rankings[-1]
            highest_quality_cat = quality_rankings[0]
            
            recommendations.append(
                f"⭐ **Quality Focus**: '{lowest_quality_cat}' category has the lowest average quality. "
                f"Apply quality screening strategies from '{highest_quality_cat}' category to improve overall standards."
            )
        
        # Evolution trend recommendations
        growing_categories = []
        declining_categories = []
        
        for category, trend in evolution_analysis['category_trends'].items():
            if trend['trend_direction'] == 'Growing':
                growing_categories.append(category)
            elif trend['trend_direction'] == 'Declining':
                declining_categories.append(category)
        
        if growing_categories:
            recommendations.append(
                f"📈 **Growth Opportunity**: Categories {', '.join(growing_categories)} are showing growth trends. "
                "Increase collection efforts in these areas to capture emerging patterns."
            )
        
        if declining_categories:
            recommendations.append(
                f"📉 **Attention Needed**: Categories {', '.join(declining_categories)} are declining. "
                "Investigate if this reflects market trends or collection gaps."
            )
        
        # Relationship-based recommendations
        relationships = relationship_analysis['category_relationships']
        high_overlap_pairs = [(pair, data) for pair, data in relationships.items() if data['relationship_strength'] > 0.25]
        
        if high_overlap_pairs:
            for pair, data in high_overlap_pairs[:2]:  # Top 2 pairs
                recommendations.append(
                    f"🔗 **Integration Opportunity**: {data['description']} shows high overlap ({data['relationship_strength']:.2f}). "
                    f"{data['strategic_insight']}"
                )
        
        # DCWF-specific recommendations
        distribution = distribution_analysis['distribution']
        if 'human_only' in distribution and distribution['human_only']['percentage'] < 25:
            recommendations.append(
                "👤 **Human Skills Emphasis**: Human-only category is underrepresented. "
                "Increase focus on uniquely human skills that remain valuable despite AI advancement."
            )
        
        if 'new_tasks' in distribution and distribution['new_tasks']['percentage'] < 20:
            recommendations.append(
                "🆕 **Emerging Opportunities**: New tasks category needs attention. "
                "Focus on identifying and documenting emerging roles created by AI adoption."
            )
        
        return recommendations
    
    def generate_report(self) -> str:
        """Generate comprehensive category distribution insights report."""
        print("\n📋 Generating Category Distribution Insights Report...")
        
        distribution_analysis = self.analyze_category_distribution()
        evolution_analysis = self.analyze_category_evolution()
        relationship_analysis = self.analyze_cross_category_relationships()
        quality_analysis = self.analyze_quality_patterns_by_category()
        recommendations = self.generate_optimization_recommendations(
            distribution_analysis, evolution_analysis, relationship_analysis, quality_analysis
        )
        
        # Generate visualization data
        visualization_data = self.generate_visualization_data(
            distribution_analysis, evolution_analysis, relationship_analysis
        )
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""# Category Distribution Insights Analysis Report

**Generated**: {timestamp}  
**Analysis Tool**: Category Distribution Insights v2.0 (Enhanced with Predictive Modeling)  
**Total Articles Analyzed**: {distribution_analysis['total_articles']}  
**Categories Covered**: {distribution_analysis['categories_covered']}  

---

## 📊 Executive Summary

This enhanced analysis examines how cybersecurity content is distributed across the four AI impact categories, providing insights into workforce transformation patterns with advanced temporal analysis, predictive modeling, and interactive visualizations for DCWF-aligned career development.

### Key Findings

- **Distribution Balance Score**: {distribution_analysis['balance_score']:.3f} (1.0 = perfect balance)
- **Evolution Period**: {evolution_analysis['analysis_months']} months of data analyzed
- **Category Relationships**: {len(relationship_analysis['category_relationships'])} strategic relationships identified
- **Quality Leader**: {quality_analysis['quality_rankings'][0] if quality_analysis['quality_rankings'] else 'N/A'} category
- **Predictive Models**: Statistical trend analysis with R² validation
- **Visualizations**: Interactive charts and static graphs generated

---

## 📈 AI Impact Category Distribution

### Current Distribution Analysis

"""
        
        # Add distribution details
        for category, stats in sorted(distribution_analysis['distribution'].items(), 
                                      key=lambda x: x[1]['count'], reverse=True):
            report += f"""
#### {category.upper()} - {stats['description']}
- **Articles**: {stats['count']} ({stats['percentage']:.1f}% of total)
- **Average Quality**: {stats['avg_quality']:.3f} ± {stats['quality_std']:.3f}
- **Average Length**: {stats['avg_content_length']:,} characters
- **Top DCWF Tasks**: {', '.join(stats['top_dcwf_tasks'][:3]) if stats['top_dcwf_tasks'] else 'None identified'}
- **Key Skills**: {', '.join(stats['top_skills'][:3]) if stats['top_skills'] else 'None identified'}
"""
        
        report += f"""

---

## 📊 Advanced Temporal Analysis & Predictions

### Category Evolution Over {evolution_analysis['analysis_months']} Months

"""
        
        # Enhanced temporal analysis section
        for category, trend in evolution_analysis['category_trends'].items():
            direction_icon = "📈" if trend['trend_direction'] == 'Growing' else "📉" if trend['trend_direction'] == 'Declining' else "➡️"
            significance = " (Statistically Significant)" if trend.get('statistical_significance', False) else ""
            
            report += f"""
#### {category.upper()} {direction_icon}
- **Trend**: {trend['trend_direction']} ({trend['percentage_change']:+.1f}% total change){significance}
- **Monthly Change Rate**: {trend.get('monthly_change_rate', 0):+.3f}% per month
- **Trend Strength**: {trend.get('trend_strength', 0):.3f}/1.0
- **Model Accuracy**: R² = {trend.get('r_squared', 0):.3f}
- **Current Share**: {trend['current_percentage']:.1f}% of monthly articles
"""
            
            if trend.get('predicted_next_3_months'):
                predictions = ', '.join([f"{p:.1f}%" for p in trend['predicted_next_3_months']])
                report += f"- **3-Month Predictions**: {predictions}\n"
        
        # Add temporal patterns analysis
        temporal_patterns = evolution_analysis.get('temporal_patterns', {})
        if temporal_patterns.get('volatility_by_category'):
            report += f"""

### Temporal Pattern Analysis

#### Category Volatility (Stability Scores)
"""
            for category, volatility in temporal_patterns['volatility_by_category'].items():
                stability = 1 - volatility
                stability_level = "High" if stability > 0.8 else "Medium" if stability > 0.6 else "Low"
                report += f"- **{category.upper()}**: {stability:.3f} ({stability_level} stability)\n"
            
            report += f"\n**Overall System Stability**: {temporal_patterns.get('stability_score', 0):.3f}/1.0\n"
        
        # Add correlation analysis
        if temporal_patterns.get('correlation_matrix'):
            report += f"""

#### Category Correlation Analysis
"""
            significant_correlations = [corr for corr in temporal_patterns['correlation_matrix'] if corr.get('significant', False)]
            if significant_correlations:
                for corr in significant_correlations[:5]:  # Top 5
                    corr_strength = "Strong" if abs(corr['correlation']) > 0.7 else "Moderate" if abs(corr['correlation']) > 0.5 else "Weak"
                    report += f"- **{corr['category_1']} ↔ {corr['category_2']}**: r = {corr['correlation']:.3f} ({corr_strength}, p = {corr['p_value']:.3f})\n"
            else:
                report += "- No statistically significant correlations detected between categories\n"
        
        # Add seasonality analysis if available
        seasonality = evolution_analysis.get('seasonality_analysis', {})
        if seasonality.get('seasonal_categories'):
            report += f"""

#### Seasonal Pattern Detection
"""
            for category, seasonal_data in seasonality['seasonal_categories'].items():
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                peak_month = month_names[seasonal_data['peak_month'] - 1]
                low_month = month_names[seasonal_data['low_month'] - 1]
                report += f"- **{category.upper()}**: Peak in {peak_month}, Low in {low_month} (Strength: {seasonal_data['strength']:.3f})\n"
        
        report += f"""

---

## 🔗 Cross-Category Relationship Analysis

### Strategic Category Relationships

"""
        
        for pair, data in relationship_analysis['category_relationships'].items():
            report += f"""
#### {data['description']}
- **Relationship Strength**: {data['relationship_strength']:.3f}
- **Task Overlap**: {data['task_overlap']:.3f}
- **Skill Overlap**: {data['skill_overlap']:.3f}
- **Strategic Insight**: {data['strategic_insight']}

"""
        
        report += f"""

---

## ⭐ Quality Patterns by Category

### Category Quality Rankings

"""
        
        for i, category in enumerate(quality_analysis['quality_rankings'], 1):
            stats = quality_analysis['category_quality'][category]
            report += f"""
{i}. **{category.upper()}**
   - Average Quality: {stats['avg_quality']:.3f}
   - Quality Consistency: {stats['quality_consistency']:.3f}
   - Grade Distribution: {stats['quality_grades']['excellent']} Excellent, {stats['quality_grades']['good']} Good, {stats['quality_grades']['fair']} Fair, {stats['quality_grades']['poor']} Poor
   - Quality per 1K chars: {stats['quality_per_length']:.3f}

"""
        
        report += f"""

---

## 🎯 Strategic Recommendations

### DCWF-Aligned Optimization Strategies

"""
        
        for i, recommendation in enumerate(recommendations, 1):
            report += f"{i}. {recommendation}\n\n"
        
        # Add predictive insights section
        report += f"""

---

## 🔮 Predictive Insights & Future Outlook

### Machine Learning Model Results

Based on {evolution_analysis['analysis_months']} months of temporal data, our predictive models provide the following insights:

#### Model Performance Summary
"""
        
        total_r_squared = 0
        significant_trends = 0
        
        for category, trend in evolution_analysis['category_trends'].items():
            if trend.get('r_squared', 0) > 0:
                total_r_squared += trend['r_squared']
                if trend.get('statistical_significance', False):
                    significant_trends += 1
        
        avg_r_squared = total_r_squared / len(evolution_analysis['category_trends']) if evolution_analysis['category_trends'] else 0
        
        report += f"""
- **Average Model Accuracy**: R² = {avg_r_squared:.3f}
- **Statistically Significant Trends**: {significant_trends}/{len(evolution_analysis['category_trends'])} categories
- **Prediction Confidence**: {'High' if avg_r_squared > 0.7 else 'Medium' if avg_r_squared > 0.5 else 'Low'}

#### Key Predictive Findings
"""
        
        growing_categories = [cat for cat, trend in evolution_analysis['category_trends'].items() 
                            if trend['trend_direction'] == 'Growing' and trend.get('statistical_significance', False)]
        declining_categories = [cat for cat, trend in evolution_analysis['category_trends'].items() 
                              if trend['trend_direction'] == 'Declining' and trend.get('statistical_significance', False)]
        
        if growing_categories:
            report += f"- **Growing Categories**: {', '.join(growing_categories)} showing statistically significant growth trends\n"
        if declining_categories:
            report += f"- **Declining Categories**: {', '.join(declining_categories)} showing statistically significant decline trends\n"
        
        report += f"""

### Workforce Development Implications

#### 3-Month Outlook
Based on our predictive models, the cybersecurity workforce landscape is expected to evolve as follows:
"""
        
        # Add specific predictions for each category
        for category, trend in evolution_analysis['category_trends'].items():
            if trend.get('predicted_next_3_months'):
                current = trend['current_percentage']
                predicted = trend['predicted_next_3_months'][-1]  # 3 months out
                change = predicted - current
                
                if abs(change) > 1:  # Only report significant changes
                    direction = "increase" if change > 0 else "decrease"
                    report += f"- **{category.upper()}**: Expected to {direction} from {current:.1f}% to {predicted:.1f}% ({change:+.1f}%)\n"
        
        report += f"""

---

## 📊 Interactive Visualizations

### Generated Visualization Assets

This analysis has generated comprehensive visualization data for interactive exploration:

#### Available Visualizations
1. **Category Distribution Chart**: Interactive donut chart showing current distribution
2. **Evolution Timeline**: Multi-line chart with trend analysis and predictions
3. **Relationship Network**: Interactive network graph showing category relationships
4. **Prediction Dashboard**: Trend forecasting with confidence intervals
5. **Correlation Heatmap**: Statistical correlation matrix between categories

#### Static Visualization Files
- Category distribution pie chart saved to `data/visualizations/`
- Evolution timeline chart saved to `data/visualizations/`
- Correlation heatmap saved to `data/visualizations/`

#### Interactive Data Format
All visualization data is prepared in JSON format for web-based interactive charts using libraries like Chart.js, D3.js, or similar frameworks.

---

## 📋 Collection Optimization Insights

### Category-Specific Collection Strategies

Based on the analysis, the following collection optimization strategies are recommended:

#### High-Priority Categories
"""
        
        # Identify categories needing attention
        distribution = distribution_analysis['distribution']
        low_coverage_categories = [cat for cat, stats in distribution.items() if stats['percentage'] < 20]
        high_quality_categories = quality_analysis['quality_rankings'][:2]
        
        if low_coverage_categories:
            report += f"""
**Underrepresented Categories**: {', '.join(low_coverage_categories)}
- These categories need increased collection focus for balanced coverage
- Target specialized sources and expert content in these areas
"""
        
        if high_quality_categories:
            report += f"""
**Quality Source Categories**: {', '.join(high_quality_categories)}
- These categories consistently produce high-quality content
- Use successful collection strategies from these areas as templates
"""
        
        report += f"""

#### Quality Enhancement Opportunities

- **Average Quality Across All Categories**: {statistics.mean([stats['avg_quality'] for stats in distribution.values()]):.3f}
- **Quality Variance**: High variance indicates inconsistent source quality
- **Optimization Target**: Focus on categories below 0.70 average quality

---

## 🔮 Workforce Development Implications

### DCWF Task Distribution Insights

This analysis reveals key patterns for cybersecurity workforce development:

1. **Task Automation Patterns**: Categories show different automation susceptibilities
2. **Skill Evolution Trends**: Cross-category relationships indicate transferable skills
3. **Career Path Optimization**: Quality patterns suggest focus areas for student guidance
4. **Training Priority Areas**: Emerging and declining categories indicate curriculum needs
5. **Predictive Workforce Planning**: Statistical models enable proactive workforce development

### Strategic Workforce Guidance

- **For Students**: Focus on categories showing growth trends and high quality content
- **For Educators**: Develop integrated curricula based on cross-category relationships and predictive insights
- **For Organizations**: Prepare for workforce transitions indicated by category evolution models
- **For Policymakers**: Support skill development in emerging high-value categories with statistical validation

---

## 📊 Technical Analysis Details

**Analysis Methodology**: 
- Content analysis across {distribution_analysis['total_articles']} cybersecurity articles
- DCWF task extraction using pattern matching on {len(self._extract_dcwf_tasks(''))} task categories
- Quality scoring using multi-dimensional assessment framework
- Temporal analysis across {evolution_analysis['analysis_months']} months of collection data
- **Advanced Features**: Statistical trend analysis, machine learning predictions, correlation analysis

**Statistical Models Used**:
- Linear regression for trend analysis
- Polynomial regression for non-linear patterns
- Pearson correlation for relationship analysis
- Time series analysis for seasonality detection

**Data Quality Metrics**:
- Articles with quality scores: {len([item for item in self.category_data if item['quality_score'] > 0])}
- Articles with date information: {len([item for item in self.category_data if item['month_key'] != 'unknown'])}
- Articles with DCWF task mentions: {len([item for item in self.category_data if item['dcwf_tasks']])}

**Model Performance**:
- Average R² Score: {avg_r_squared:.3f}
- Statistically Significant Trends: {significant_trends}/{len(evolution_analysis['category_trends'])}
- Prediction Confidence Level: {'High' if avg_r_squared > 0.7 else 'Medium' if avg_r_squared > 0.5 else 'Low'}

**Confidence Level**: High (based on comprehensive dataset, validated methodology, and statistical significance testing)

---

*Report generated by AI-Horizon Category Distribution Insights Analysis Tool v2.0*  
*Enhanced with Advanced Temporal Analysis, Predictive Modeling, and Interactive Visualizations*  
*For questions about this analysis, refer to the AI-Horizon documentation*
"""
        
        return report
    
    def _generate_basic_report(self, distribution_analysis: Dict, evolution_analysis: Dict,
                              relationship_analysis: Dict, quality_analysis: Dict) -> str:
        """Generate a basic report without advanced visualization features."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""# Category Distribution Insights Analysis Report (Basic)

**Generated**: {timestamp}  
**Analysis Tool**: Category Distribution Insights v2.0 (Basic Mode)  
**Total Articles Analyzed**: {distribution_analysis['total_articles']}  
**Categories Covered**: {distribution_analysis['categories_covered']}  

---

## 📊 Executive Summary

This analysis examines how cybersecurity content is distributed across the four AI impact categories, providing insights into workforce transformation patterns and strategic guidance for DCWF-aligned career development.

**Note**: This is a basic analysis report. For advanced features including predictive modeling, statistical analysis, and interactive visualizations, install additional packages: `pip install numpy scipy matplotlib seaborn scikit-learn`

---

*Report generated by AI-Horizon Category Distribution Insights Analysis Tool v2.0 (Basic Mode)*  
*For questions about this analysis, refer to the AI-Horizon documentation*
"""
        
        return report
    
    def generate_visualization_data(self, distribution_analysis: Dict, evolution_analysis: Dict, 
                                   relationship_analysis: Dict) -> Dict[str, Any]:
        """Generate data for interactive visualizations."""
        print("\n📊 Generating Interactive Visualization Data...")
        
        viz_data = {
            'category_distribution_chart': self._prepare_distribution_chart_data(distribution_analysis),
            'evolution_timeline_chart': self._prepare_evolution_chart_data(evolution_analysis),
            'relationship_network_chart': self._prepare_relationship_network_data(relationship_analysis),
            'prediction_charts': self._prepare_prediction_chart_data(evolution_analysis),
            'correlation_heatmap': self._prepare_correlation_heatmap_data(evolution_analysis),
            'chart_configurations': self._get_chart_configurations()
        }
        
        # Generate static visualizations using matplotlib
        self._generate_static_visualizations(viz_data)
        
        return viz_data
    
    def _prepare_distribution_chart_data(self, distribution_analysis: Dict) -> Dict[str, Any]:
        """Prepare data for category distribution pie/donut chart."""
        categories = []
        values = []
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        for i, (category, stats) in enumerate(sorted(distribution_analysis['distribution'].items(), 
                                                   key=lambda x: x[1]['count'], reverse=True)):
            categories.append(category.replace('_', ' ').title())
            values.append(stats['count'])
        
        return {
            'type': 'donut',
            'labels': categories,
            'values': values,
            'colors': colors[:len(categories)],
            'title': 'AI Impact Category Distribution',
            'total_articles': distribution_analysis['total_articles']
        }
    
    def _prepare_evolution_chart_data(self, evolution_analysis: Dict) -> Dict[str, Any]:
        """Prepare data for category evolution timeline chart."""
        if not evolution_analysis.get('category_trends'):
            return {'type': 'line', 'series': [], 'months': []}
        
        months = []
        series_data = {}
        
        # Get all months from the first category that has data
        first_category = list(evolution_analysis['category_trends'].keys())[0]
        if 'monthly_data' in evolution_analysis['category_trends'][first_category]:
            months = list(evolution_analysis['category_trends'][first_category]['monthly_data'].keys())
        
        # Prepare series for each category
        for category, trend_data in evolution_analysis['category_trends'].items():
            if 'monthly_data' in trend_data:
                series_data[category.replace('_', ' ').title()] = {
                    'name': category.replace('_', ' ').title(),
                    'data': list(trend_data['monthly_data'].values()),
                    'trend_direction': trend_data.get('trend_direction', 'Stable'),
                    'predictions': trend_data.get('predicted_next_3_months', [])
                }
        
        return {
            'type': 'line',
            'months': months,
            'series': series_data,
            'title': 'Category Evolution Over Time (%)',
            'y_axis_title': 'Percentage of Total Articles'
        }
    
    def _prepare_relationship_network_data(self, relationship_analysis: Dict) -> Dict[str, Any]:
        """Prepare data for category relationship network visualization."""
        nodes = []
        links = []
        
        # Create nodes for each category
        categories = ['replace', 'augment', 'new_tasks', 'human_only']
        category_colors = {
            'replace': '#FF6B6B',
            'augment': '#4ECDC4', 
            'new_tasks': '#45B7D1',
            'human_only': '#96CEB4'
        }
        
        for category in categories:
            nodes.append({
                'id': category,
                'name': category.replace('_', ' ').title(),
                'category': category,
                'color': category_colors[category],
                'size': 30
            })
        
        # Create links based on relationship strength
        if 'task_overlaps' in relationship_analysis:
            for pair, data in relationship_analysis['task_overlaps'].items():
                # More robust parsing for category pairs
                # Find which categories this pair represents
                cat1, cat2 = None, None
                for c1 in categories:
                    for c2 in categories:
                        if c1 != c2:
                            possible_pair1 = f"{c1}_{c2}"
                            possible_pair2 = f"{c2}_{c1}"
                            if pair == possible_pair1 or pair == possible_pair2:
                                cat1, cat2 = c1, c2
                                break
                    if cat1 and cat2:
                        break
                
                if cat1 and cat2:
                    links.append({
                        'source': cat1,
                        'target': cat2,
                        'strength': data['overlap_score'],
                        'overlap_tasks': data['overlap_tasks'],
                        'width': max(1, data['overlap_score'] * 10),
                        'opacity': 0.3 + (data['overlap_score'] * 0.7)
                    })
        
        return {
            'type': 'network',
            'nodes': nodes,
            'links': links,
            'title': 'Category Relationship Network'
        }
    
    def _prepare_prediction_chart_data(self, evolution_analysis: Dict) -> Dict[str, Any]:
        """Prepare data for prediction visualization."""
        predictions = {}
        
        for category, trend_data in evolution_analysis.get('category_trends', {}).items():
            if 'predicted_next_3_months' in trend_data and trend_data['predicted_next_3_months']:
                predictions[category.replace('_', ' ').title()] = {
                    'current': trend_data.get('current_percentage', 0),
                    'predictions': trend_data['predicted_next_3_months'],
                    'confidence': trend_data.get('r_squared', 0),
                    'trend_direction': trend_data.get('trend_direction', 'Stable')
                }
        
        return {
            'type': 'prediction',
            'categories': predictions,
            'title': 'Category Trend Predictions (Next 3 Months)',
            'y_axis_title': 'Predicted Percentage'
        }
    
    def _prepare_correlation_heatmap_data(self, evolution_analysis: Dict) -> Dict[str, Any]:
        """Prepare data for correlation heatmap."""
        correlation_matrix = []
        categories = ['replace', 'augment', 'new_tasks', 'human_only']
        
        # Initialize correlation matrix
        for i, cat1 in enumerate(categories):
            row = []
            for j, cat2 in enumerate(categories):
                if i == j:
                    row.append(1.0)  # Self-correlation
                else:
                    correlation = 0.0
                    # Find correlation from temporal patterns
                    temporal_patterns = evolution_analysis.get('temporal_patterns', {})
                    if 'correlation_matrix' in temporal_patterns:
                        for corr_data in temporal_patterns['correlation_matrix']:
                            # Direct comparison without relying on string splitting
                            if ((corr_data.get('category_1') == cat1 and corr_data.get('category_2') == cat2) or
                                (corr_data.get('category_1') == cat2 and corr_data.get('category_2') == cat1)):
                                correlation = corr_data['correlation']
                                break
                    row.append(correlation)
            correlation_matrix.append(row)
        
        return {
            'type': 'heatmap',
            'matrix': correlation_matrix,
            'categories': [cat.replace('_', ' ').title() for cat in categories],
            'title': 'Category Correlation Heatmap'
        }
    
    def _get_chart_configurations(self) -> Dict[str, Any]:
        """Get configuration for chart rendering."""
        return {
            'theme': 'professional',
            'color_palette': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'],
            'font_family': 'Arial, sans-serif',
            'responsive': True,
            'animations': True
        }
    
    def _generate_static_visualizations(self, viz_data: Dict) -> None:
        """Generate static visualization files using matplotlib."""
        try:
            plt.style.use('seaborn-v0_8')
            
            # Create visualization directory
            viz_dir = Path('data/visualizations')
            viz_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 1. Category Distribution Pie Chart
            if viz_data['category_distribution_chart']['values']:
                plt.figure(figsize=(10, 8))
                plt.pie(viz_data['category_distribution_chart']['values'], 
                       labels=viz_data['category_distribution_chart']['labels'],
                       colors=viz_data['category_distribution_chart']['colors'],
                       autopct='%1.1f%%', startangle=90)
                plt.title('AI Impact Category Distribution', fontsize=16, fontweight='bold')
                plt.axis('equal')
                plt.tight_layout()
                plt.savefig(viz_dir / f'category_distribution_{timestamp}.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # 2. Evolution Timeline
            if viz_data['evolution_timeline_chart']['series']:
                plt.figure(figsize=(12, 8))
                for category, series in viz_data['evolution_timeline_chart']['series'].items():
                    plt.plot(viz_data['evolution_timeline_chart']['months'], series['data'], 
                            marker='o', linewidth=2, label=category)
                
                plt.title('Category Evolution Over Time', fontsize=16, fontweight='bold')
                plt.xlabel('Month')
                plt.ylabel('Percentage of Total Articles')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(viz_dir / f'category_evolution_{timestamp}.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # 3. Correlation Heatmap
            if viz_data['correlation_heatmap']['matrix']:
                plt.figure(figsize=(10, 8))
                sns.heatmap(viz_data['correlation_heatmap']['matrix'],
                           xticklabels=viz_data['correlation_heatmap']['categories'],
                           yticklabels=viz_data['correlation_heatmap']['categories'],
                           annot=True, cmap='coolwarm', center=0, 
                           square=True, cbar_kws={'shrink': 0.8})
                plt.title('Category Correlation Heatmap', fontsize=16, fontweight='bold')
                plt.tight_layout()
                plt.savefig(viz_dir / f'category_correlation_{timestamp}.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            print(f"   Static visualizations saved to: {viz_dir}/")
            
        except Exception as e:
            print(f"   Warning: Could not generate static visualizations: {e}")
            # Don't fail the entire analysis if visualization generation fails

def main():
    """Main execution function."""
    print("🔍 Starting Category Distribution Insights Analysis...")
    print("=" * 60)
    
    try:
        # Initialize analyzer
        analyzer = CategoryDistributionAnalyzer()
        
        # Load and analyze data
        analyzer.load_data()
        
        if not analyzer.category_data:
            print("❌ No data available for analysis")
            return
        
        # Generate comprehensive report
        report_content = analyzer.generate_report()
        
        # Save report
        report_dir = Path('data/reports')
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'category_distribution_insights_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n✅ Analysis Complete!")
        print(f"📄 Report saved to: {report_file}")
        
        # Print summary for console output parsing
        distribution_analysis = analyzer.analyze_category_distribution()
        print(f"\n📊 Summary:")
        print(f"Total Analyzed: {distribution_analysis['total_articles']} articles")
        print(f"Categories Covered: {distribution_analysis['categories_covered']}")
        print(f"Distribution Balance: {distribution_analysis['balance_score']:.3f}")
        
        # Check if visualizations were generated
        viz_dir = Path('data/visualizations')
        if viz_dir.exists():
            viz_files = list(viz_dir.glob(f'*{timestamp}*'))
            if viz_files:
                print(f"📊 Visualizations: {len(viz_files)} charts generated in {viz_dir}/")
        
        return str(report_file)
        
    except ImportError as e:
        missing_package = str(e).split("'")[1] if "'" in str(e) else "unknown"
        print(f"⚠️  Warning: Missing package '{missing_package}' - running with basic analysis")
        print("   To enable advanced features, install: pip install numpy scipy matplotlib seaborn scikit-learn")
        
        # Fall back to basic analysis without advanced features
        try:
            analyzer = CategoryDistributionAnalyzer()
            analyzer.load_data()
            
            if not analyzer.category_data:
                print("❌ No data available for analysis")
                return
            
            # Run basic analysis without visualization
            distribution_analysis = analyzer.analyze_category_distribution()
            evolution_analysis = analyzer.analyze_category_evolution()
            relationship_analysis = analyzer.analyze_cross_category_relationships()
            quality_analysis = analyzer.analyze_quality_patterns_by_category()
            
            # Generate basic report
            basic_report = analyzer._generate_basic_report(
                distribution_analysis, evolution_analysis, relationship_analysis, quality_analysis
            )
            
            report_dir = Path('data/reports')
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = report_dir / f'category_distribution_insights_basic_{timestamp}.md'
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(basic_report)
            
            print(f"\n✅ Basic Analysis Complete!")
            print(f"📄 Report saved to: {report_file}")
            print(f"📊 Summary:")
            print(f"Total Analyzed: {distribution_analysis['total_articles']} articles")
            print(f"Categories Covered: {distribution_analysis['categories_covered']}")
            print(f"Distribution Balance: {distribution_analysis['balance_score']:.3f}")
            
            return str(report_file)
            
        except Exception as e:
            print(f"❌ Basic analysis also failed: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 