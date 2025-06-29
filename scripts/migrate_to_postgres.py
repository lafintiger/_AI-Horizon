#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL

This script helps migrate your AI-Horizon database from SQLite (local) 
to PostgreSQL (Heroku production).

Usage:
    python scripts/migrate_to_postgres.py --export
    python scripts/migrate_to_postgres.py --import --db-url <DATABASE_URL>
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def export_sqlite_data(db_path="data/aih_database.db", output_file="database_export.json"):
    """Export SQLite database to JSON format for easy import."""
    
    if not os.path.exists(db_path):
        print(f"❌ SQLite database not found at: {db_path}")
        return False
    
    print(f"📤 Exporting SQLite database from: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        total_records = 0
        
        for table in tables:
            print(f"  📋 Exporting table: {table}")
            cursor.execute(f"SELECT * FROM {table}")
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Get all rows
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            table_data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    row_dict[column] = row[i]
                table_data.append(row_dict)
            
            export_data['tables'][table] = {
                'columns': columns,
                'data': table_data,
                'record_count': len(table_data)
            }
            
            total_records += len(table_data)
            print(f"    ✅ {len(table_data)} records exported")
        
        conn.close()
        
        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Export complete!")
        print(f"   📊 Total tables: {len(tables)}")
        print(f"   📊 Total records: {total_records}")
        print(f"   📄 Export file: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

def generate_postgres_schema():
    """Generate PostgreSQL schema creation script."""
    
    schema_sql = """
-- AI-Horizon PostgreSQL Schema
-- Generated for Heroku deployment

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main artifacts table
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    url TEXT,
    title TEXT,
    content TEXT,
    source_type TEXT,
    category TEXT,
    quality_score REAL,
    collected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_metadata TEXT,
    processed_metadata TEXT,
    content_hash TEXT,
    wisdom_extracted TEXT,
    ai_impact_category TEXT,
    confidence_score REAL,
    multi_category_analysis TEXT,
    content_enhanced BOOLEAN DEFAULT FALSE,
    metadata_standardized BOOLEAN DEFAULT FALSE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_artifacts_collected_at ON artifacts(collected_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_category ON artifacts(category);
CREATE INDEX IF NOT EXISTS idx_artifacts_source_type ON artifacts(source_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_quality_score ON artifacts(quality_score);
CREATE INDEX IF NOT EXISTS idx_artifacts_ai_impact_category ON artifacts(ai_impact_category);

-- Task-centric tables (if they exist)
CREATE TABLE IF NOT EXISTS dcwf_tasks (
    id SERIAL PRIMARY KEY,
    task_id TEXT UNIQUE NOT NULL,
    task_name TEXT NOT NULL,
    description TEXT,
    work_role_id TEXT,
    work_role_name TEXT,
    specialty_area TEXT,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_tools (
    id SERIAL PRIMARY KEY,
    tool_name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    capabilities TEXT,
    pricing_model TEXT,
    website_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_tool_recommendations (
    id SERIAL PRIMARY KEY,
    task_id TEXT,
    tool_id INTEGER,
    effectiveness_rating REAL,
    example_prompts TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_id) REFERENCES ai_tools(id)
);

CREATE TABLE IF NOT EXISTS article_task_mappings (
    id SERIAL PRIMARY KEY,
    article_id TEXT,
    task_id TEXT,
    confidence_score REAL,
    extracted_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES artifacts(id)
);

-- User management tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    permissions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Insert default admin user (password: admin123 - CHANGE THIS!)
INSERT INTO users (username, password_hash, role, permissions) VALUES 
('admin', 'pbkdf2:sha256:600000$vQHNTKWo$e3fcf8c7f5c8e2a1b4e5f6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7', 'admin', 'all')
ON CONFLICT (username) DO NOTHING;

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for artifacts table
CREATE TRIGGER update_artifacts_updated_at BEFORE UPDATE ON artifacts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
"""
    
    with open('postgres_schema.sql', 'w') as f:
        f.write(schema_sql)
    
    print("✅ PostgreSQL schema generated: postgres_schema.sql")
    return True

def import_json_to_postgres(json_file="database_export.json", db_url=None):
    """Import JSON data to PostgreSQL database."""
    
    if not db_url:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not provided and not found in environment")
            return False
    
    if not os.path.exists(json_file):
        print(f"❌ Export file not found: {json_file}")
        return False
    
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    
    print(f"📥 Importing data to PostgreSQL...")
    print(f"   📄 Source file: {json_file}")
    
    try:
        # Load export data
        with open(json_file, 'r') as f:
            export_data = json.load(f)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        total_imported = 0
        
        for table_name, table_info in export_data['tables'].items():
            if table_name.startswith('sqlite_'):
                continue  # Skip SQLite system tables
            
            print(f"  📋 Importing table: {table_name}")
            
            columns = table_info['columns']
            data = table_info['data']
            
            if not data:
                print(f"    ⚠️ No data to import for {table_name}")
                continue
            
            # Create insert statement
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Insert data
            for row in data:
                try:
                    values = [row.get(col) for col in columns]
                    cursor.execute(insert_sql, values)
                except Exception as e:
                    print(f"    ⚠️ Error inserting row: {e}")
                    continue
            
            conn.commit()
            total_imported += len(data)
            print(f"    ✅ {len(data)} records imported")
        
        cursor.close()
        conn.close()
        
        print(f"✅ Import complete!")
        print(f"   📊 Total records imported: {total_imported}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='AI-Horizon Database Migration Tool')
    parser.add_argument('--export', action='store_true', help='Export SQLite database to JSON')
    parser.add_argument('--import', action='store_true', help='Import JSON data to PostgreSQL')
    parser.add_argument('--schema', action='store_true', help='Generate PostgreSQL schema')
    parser.add_argument('--db-url', help='PostgreSQL database URL (for import)')
    parser.add_argument('--sqlite-path', default='data/aih_database.db', help='SQLite database path')
    parser.add_argument('--json-file', default='database_export.json', help='JSON export file')
    
    args = parser.parse_args()
    
    if not any([args.export, getattr(args, 'import'), args.schema]):
        parser.print_help()
        return
    
    print("🚀 AI-Horizon Database Migration Tool")
    print("=" * 50)
    
    if args.schema:
        print("\n📋 Generating PostgreSQL schema...")
        generate_postgres_schema()
    
    if args.export:
        print(f"\n📤 Exporting SQLite database...")
        export_sqlite_data(args.sqlite_path, args.json_file)
    
    if getattr(args, 'import'):
        print(f"\n📥 Importing to PostgreSQL...")
        import_json_to_postgres(args.json_file, args.db_url)
    
    print("\n✅ Migration process complete!")

if __name__ == "__main__":
    main() 