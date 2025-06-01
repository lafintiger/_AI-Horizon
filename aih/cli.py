"""
Command-line interface for AI-Horizon pipeline.

Provides commands for data collection, classification, and management.
"""

import asyncio
import click
from datetime import datetime
from typing import List
from tqdm import tqdm

from aih.config import settings
from aih.utils.logging import get_logger
from aih.utils.database import DatabaseManager
from aih.gather.perplexity import PerplexityConnector
from aih.classify.classifier import ArtifactClassifier
from aih.classify.scorer import SourceScorer

logger = get_logger(__name__)

@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI-Horizon: Cybersecurity Workforce Evolution Forecasting Pipeline"""
    pass

@main.command()
@click.option('--query', '-q', help='Search query for data collection')
@click.option('--category', '-c', 
              type=click.Choice(['replace', 'augment', 'new_tasks', 'human_only', 'general']),
              default='general',
              help='AI impact category to focus on')
@click.option('--max-results', '-m', default=20, help='Maximum number of artifacts to collect')
@click.option('--timeframe', '-t', default='2024', help='Timeframe for search (e.g., "2024", "last 6 months")')
@click.option('--weekly', is_flag=True, help='Run weekly collection with predefined queries')
@click.option('--multi-query', is_flag=True, help='Use multiple task-focused queries for better coverage')
@click.option('--skip-duplicates', is_flag=True, default=True, help='Skip articles already in database')
def collect(query, category, max_results, timeframe, weekly, multi_query, skip_duplicates):
    """Collect artifacts from data sources with enhanced duplicate detection."""
    async def _collect():
        logger.info("Starting enhanced artifact collection...")
        
        db = DatabaseManager()
        connector = PerplexityConnector()
        
        # Validate connector configuration
        if not connector.validate_config():
            click.echo("❌ Connector configuration validation failed. Check your API keys.")
            return
        
        # Get existing URLs to avoid duplicates
        existing_urls = set()
        if skip_duplicates:
            existing_urls = db.get_existing_urls()
            click.echo(f"📚 Found {len(existing_urls)} existing articles in database")
        
        if weekly:
            # Run enhanced weekly collection with multi-query
            categories = ['replace', 'augment', 'new_tasks', 'human_only']
            
            run_id = db.start_collection_run(
                run_type="weekly_enhanced",
                query="Multi-category task-focused collection"
            )
            
            total_artifacts = 0
            
            try:
                for cat in categories:
                    click.echo(f"\n🔍 Collecting for category: {cat.upper()}")
                    
                    if multi_query:
                        artifacts = await connector.collect_multi_query(
                            category=cat,
                            max_results=max_results // len(categories),  # Distribute across categories
                            timeframe=timeframe,
                            existing_urls=existing_urls
                        )
                    else:
                        # Single query with enhanced template
                        artifacts = await connector.collect(
                            query=f"cybersecurity {cat} tasks AI automation",
                            max_results=max_results // len(categories),
                            category=cat,
                            timeframe=timeframe
                        )
                        
                        # Filter duplicates
                        unique_artifacts = []
                        for artifact in artifacts:
                            if artifact.url not in existing_urls:
                                unique_artifacts.append(artifact)
                                existing_urls.add(artifact.url)
                        artifacts = unique_artifacts
                    
                    # Save artifacts to database
                    with tqdm(artifacts, desc=f"Saving {cat} artifacts") as pbar:
                        for artifact in pbar:
                            if not db.artifact_exists(artifact.url):
                                artifact_dict = {
                                    'id': artifact.id,
                                    'url': artifact.url,
                                    'title': artifact.title,
                                    'content': artifact.content,
                                    'source_type': artifact.source_type,
                                    'collected_at': artifact.collected_at,
                                    'metadata': artifact.metadata
                                }
                                db.save_artifact(artifact_dict)
                                total_artifacts += 1
                            else:
                                pbar.set_description(f"Skipped duplicate: {artifact.title[:30]}...")
                    
                    click.echo(f"✅ Collected {len(artifacts)} new artifacts for category '{cat}'")
                
                db.complete_collection_run(run_id, total_artifacts)
                click.echo(f"\n🎉 Enhanced weekly collection complete!")
                click.echo(f"📊 Total new articles: {total_artifacts}")
                click.echo(f"📚 Total in database: {len(existing_urls) + total_artifacts}")
                
            except Exception as e:
                logger.error(f"Collection failed: {e}")
                db.complete_collection_run(run_id, total_artifacts, str(e))
                click.echo(f"❌ Collection failed: {e}")
        
        else:
            # Single category collection
            if not query and not multi_query:
                click.echo("❌ Please provide a query with -q, use --weekly, or use --multi-query flag")
                return
            
            run_id = db.start_collection_run(
                run_type="manual_enhanced",
                query=query or f"multi-query {category}"
            )
            
            total_artifacts = 0
            
            try:
                click.echo(f"\n🔍 Collecting for category: {category.upper()}")
                
                if multi_query:
                    artifacts = await connector.collect_multi_query(
                        category=category,
                        max_results=max_results,
                        timeframe=timeframe,
                        existing_urls=existing_urls
                    )
                else:
                    artifacts = await connector.collect(
                        query=query,
                        max_results=max_results,
                        category=category,
                        timeframe=timeframe
                    )
                    
                    # Filter duplicates
                    unique_artifacts = []
                    for artifact in artifacts:
                        if artifact.url not in existing_urls:
                            unique_artifacts.append(artifact)
                            existing_urls.add(artifact.url)
                    artifacts = unique_artifacts
                
                # Save artifacts to database
                with tqdm(artifacts, desc="Saving artifacts") as pbar:
                    for artifact in pbar:
                        if not db.artifact_exists(artifact.url):
                            artifact_dict = {
                                'id': artifact.id,
                                'url': artifact.url,
                                'title': artifact.title,
                                'content': artifact.content,
                                'source_type': artifact.source_type,
                                'collected_at': artifact.collected_at,
                                'metadata': artifact.metadata
                            }
                            db.save_artifact(artifact_dict)
                            total_artifacts += 1
                        else:
                            pbar.set_description(f"Skipped duplicate: {artifact.title[:30]}...")
                
                db.complete_collection_run(run_id, total_artifacts)
                click.echo(f"\n🎉 Collection complete!")
                click.echo(f"📊 New articles collected: {total_artifacts}")
                click.echo(f"📚 Total in database: {len(existing_urls) + total_artifacts}")
                
            except Exception as e:
                logger.error(f"Collection failed: {e}")
                db.complete_collection_run(run_id, total_artifacts, str(e))
                click.echo(f"❌ Collection failed: {e}")
    
    asyncio.run(_collect())

@main.command()
@click.option('--limit', '-l', default=None, type=int, help='Limit number of artifacts to classify')
@click.option('--unclassified-only', is_flag=True, help='Only classify artifacts without existing classifications')
@click.option('--model', '-m', help='LLM model to use for classification')
def classify(limit, unclassified_only, model):
    """Classify collected artifacts into AI impact categories."""
    async def _classify():
        logger.info("Starting artifact classification...")
        
        db = DatabaseManager()
        classifier = ArtifactClassifier(model_name=model)
        scorer = SourceScorer(model_name=model)
        
        # Get artifacts to classify
        artifacts = db.get_artifacts(limit=limit, unclassified_only=unclassified_only)
        
        if not artifacts:
            click.echo("📭 No artifacts found to classify.")
            return
        
        click.echo(f"🔍 Found {len(artifacts)} artifacts to classify")
        
        classified_count = 0
        scored_count = 0
        
        with tqdm(artifacts, desc="Processing artifacts") as pbar:
            for artifact in pbar:
                try:
                    pbar.set_description(f"Classifying: {artifact['title'][:30]}...")
                    
                    # Classify artifact
                    classifications = await classifier.classify_artifact(artifact)
                    
                    # Save classifications
                    for classification in classifications:
                        classification_data = {
                            'artifact_id': artifact['id'],
                            'category': classification.category,
                            'confidence': classification.confidence,
                            'rationale': classification.rationale,
                            'model_used': classification.model_used,
                            'classified_at': classification.classified_at
                        }
                        db.save_classification(classification_data)
                        classified_count += 1
                    
                    # Score source reliability
                    pbar.set_description(f"Scoring: {artifact['title'][:30]}...")
                    score = await scorer.score_artifact(artifact)
                    
                    score_data = {
                        'artifact_id': artifact['id'],
                        'source_reliability': score.source_reliability,
                        'info_credibility': score.info_credibility,
                        'specificity_score': score.specificity_score,
                        'recency_score': score.recency_score,
                        'evidence_score': score.evidence_score,
                        'expert_score': score.expert_score,
                        'overall_score': score.overall_score,
                        'scoring_rationale': score.rationale
                    }
                    db.save_source_score(score_data)
                    scored_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing artifact {artifact['id']}: {e}")
                    continue
        
        click.echo(f"\n🎉 Classification complete!")
        click.echo(f"📊 Classifications created: {classified_count}")
        click.echo(f"🏆 Sources scored: {scored_count}")
    
    asyncio.run(_classify())

@main.command()
@click.option('--category', '-c', 
              type=click.Choice(['replace', 'augment', 'new_tasks', 'human_only', 'all']),
              default='all',
              help='Category to report on')
@click.option('--min-confidence', default=0.5, help='Minimum confidence threshold')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json', 'csv']),
              default='table',
              help='Output format')
def report(category, min_confidence, output_format):
    """Generate reports from classified artifacts."""
    logger.info("Generating reports...")
    
    db = DatabaseManager()
    
    if category == 'all':
        categories = ['replace', 'augment', 'new_tasks', 'human_only']
    else:
        categories = [category]
    
    for cat in categories:
        click.echo(f"\n📈 Report for category: {cat.upper()}")
        
        classifications = db.get_classifications_by_category(cat)
        
        # Filter by confidence
        high_confidence = [c for c in classifications if c['confidence'] >= min_confidence]
        
        if output_format == 'table':
            click.echo(f"Total artifacts: {len(classifications)}")
            click.echo(f"High confidence (>={min_confidence}): {len(high_confidence)}")
            click.echo(f"Average confidence: {sum(c['confidence'] for c in classifications) / len(classifications):.2f}" if classifications else "N/A")
            
            if high_confidence:
                click.echo("\nTop 5 high-confidence artifacts:")
                for i, item in enumerate(high_confidence[:5], 1):
                    click.echo(f"{i}. {item['title'][:60]}... (confidence: {item['confidence']:.2f})")
        
        # TODO: Add JSON and CSV output formats

@main.command()
@click.option('--port', '-p', default=8080, help='Port to run dashboard on')
def dashboard(port):
    """Launch the web dashboard."""
    click.echo(f"🚀 Starting dashboard on port {port}...")
    click.echo("📊 Dashboard functionality will be implemented in Phase 3")
    # TODO: Implement Flask/Django dashboard

@main.command()
def status():
    """Show pipeline status and statistics."""
    logger.info("Checking pipeline status...")
    
    db = DatabaseManager()
    
    # Get statistics
    artifacts = db.get_artifacts()
    total_artifacts = len(artifacts)
    
    click.echo("📊 AI-Horizon Pipeline Status")
    click.echo("=" * 40)
    click.echo(f"Total artifacts collected: {total_artifacts}")
    
    if total_artifacts > 0:
        # Count classifications by category
        for cat_id, cat_info in AI_IMPACT_CATEGORIES.items():
            classifications = db.get_classifications_by_category(cat_id)
            click.echo(f"{cat_info['name']}: {len(classifications)} artifacts")
        
        # Show recent activity
        recent_artifacts = artifacts[:5]
        click.echo(f"\nRecent artifacts:")
        for artifact in recent_artifacts:
            click.echo(f"  • {artifact['title'][:50]}... ({artifact['source_type']})")
    
    # Check API configurations
    click.echo(f"\nAPI Configuration:")
    click.echo(f"  Perplexity API: {'✅' if settings.perplexity_api_key else '❌'}")
    click.echo(f"  OpenAI API: {'✅' if settings.openai_api_key else '❌'}")
    click.echo(f"  Anthropic API: {'✅' if settings.anthropic_api_key else '❌'}")

@main.command()
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
def reset():
    """Reset the database (WARNING: Deletes all data)."""
    logger.warning("Resetting database...")
    
    # TODO: Implement database reset functionality
    click.echo("🗑️  Database reset functionality will be implemented")

if __name__ == "__main__":
    main() 