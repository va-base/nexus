"""Bootstrap initial data from manual inputs

This script provides a comprehensive way to load initial data into Nexus from various sources:
- Companies and themes
- Investment hypotheses
- Raw thoughts, notes, and emails
- Research memos
- Priorities and focus areas

The script supports multiple input formats:
- JSON files with structured data
- Plain text files for unstructured thoughts
- Markdown files for formatted notes
- CSV files for tabular data
"""
import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus.storage.postgres import PostgresStore
from nexus.utils.embeddings import EmbeddingGenerator
from nexus.utils.provenance import ProvenanceLogger


class InitialDataBootstrap:
    """Bootstrap initial data into Nexus"""
    
    def __init__(self, data_dir: str = "data/initial"):
        self.data_dir = Path(data_dir)
        self.store = PostgresStore()
        self.embedding_gen = EmbeddingGenerator()
        self.provenance = ProvenanceLogger(self.store)
        
        self.company_map = {}
        self.theme_map = {}
        self.hypothesis_map = {}
    
    def bootstrap_all(self):
        """Bootstrap all initial data"""
        print("=" * 60)
        print("Nexus Initial Data Bootstrap")
        print("=" * 60)
        print()
        
        if not self.data_dir.exists():
            print(f"Error: Data directory not found: {self.data_dir}")
            print(f"Please create the directory and add your initial data files.")
            return
        
        self._load_companies()
        self._load_themes()
        self._load_hypotheses()
        self._load_raw_evidence()
        self._load_memos()
        self._load_priorities()
        
        print()
        print("=" * 60)
        print("Bootstrap Complete!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  Companies: {len(self.company_map)}")
        print(f"  Themes: {len(self.theme_map)}")
        print(f"  Hypotheses: {len(self.hypothesis_map)}")
    
    def _load_companies(self):
        """Load companies from companies.json or companies.csv"""
        print("Loading companies...")
        
        json_file = self.data_dir / "companies.json"
        csv_file = self.data_dir / "companies.csv"
        
        companies = []
        
        if json_file.exists():
            with open(json_file, 'r') as f:
                companies = json.load(f)
        elif csv_file.exists():
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                companies = list(reader)
        else:
            print("  No companies file found (companies.json or companies.csv)")
            return
        
        for company_data in companies:
            ticker = company_data.get('ticker')
            name = company_data.get('name')
            
            if not name:
                print(f"  Skipping company without name: {company_data}")
                continue
            
            company_id = self.store.insert_company({
                'ticker': ticker,
                'name': name,
                'sector': company_data.get('sector'),
                'market_cap': int(company_data['market_cap']) if company_data.get('market_cap') else None,
                'is_public': company_data.get('is_public', 'true').lower() == 'true',
                'metadata': {
                    'source': 'manual_bootstrap',
                    'notes': company_data.get('notes', '')
                }
            })
            
            self.company_map[ticker or name] = company_id
            print(f"  ✓ Added company: {name} ({ticker or 'private'})")
        
        print(f"  Loaded {len(self.company_map)} companies")
        print()
    
    def _load_themes(self):
        """Load investment themes from themes.json"""
        print("Loading themes...")
        
        themes_file = self.data_dir / "themes.json"
        
        if not themes_file.exists():
            print("  No themes file found (themes.json)")
            return
        
        with open(themes_file, 'r') as f:
            themes = json.load(f)
        
        for theme_data in themes:
            name = theme_data.get('name')
            
            if not name:
                print(f"  Skipping theme without name: {theme_data}")
                continue
            
            query = """
                INSERT INTO themes (name, description, metadata)
                VALUES (:name, :description, :metadata)
                RETURNING id
            """
            result = self.store.execute(query, {
                'name': name,
                'description': theme_data.get('description', ''),
                'metadata': json.dumps({
                    'source': 'manual_bootstrap',
                    'tags': theme_data.get('tags', [])
                })
            })
            theme_id = result.fetchone()[0]
            
            self.theme_map[name] = theme_id
            print(f"  ✓ Added theme: {name}")
        
        print(f"  Loaded {len(self.theme_map)} themes")
        print()
    
    def _load_hypotheses(self):
        """Load hypotheses from hypotheses.json"""
        print("Loading hypotheses...")
        
        hypotheses_file = self.data_dir / "hypotheses.json"
        
        if not hypotheses_file.exists():
            print("  No hypotheses file found (hypotheses.json)")
            return
        
        with open(hypotheses_file, 'r') as f:
            hypotheses = json.load(f)
        
        for hyp_data in hypotheses:
            statement = hyp_data.get('statement')
            
            if not statement:
                print(f"  Skipping hypothesis without statement: {hyp_data}")
                continue
            
            company_key = hyp_data.get('company')
            theme_key = hyp_data.get('theme')
            
            company_id = self.company_map.get(company_key) if company_key else None
            theme_id = self.theme_map.get(theme_key) if theme_key else None
            
            embedding = self.embedding_gen.encode(statement)
            
            target_date = None
            if hyp_data.get('target_date'):
                try:
                    target_date = datetime.strptime(hyp_data['target_date'], '%Y-%m-%d').date()
                except ValueError:
                    print(f"  Warning: Invalid target_date format: {hyp_data['target_date']}")
            
            hypothesis_id = self.store.insert_hypothesis({
                'company_id': str(company_id) if company_id else None,
                'theme_id': str(theme_id) if theme_id else None,
                'statement': statement,
                'hypothesis_type': hyp_data.get('type', 'custom'),
                'time_horizon': hyp_data.get('time_horizon', 'medium_term'),
                'target_date': target_date,
                'initial_belief': float(hyp_data.get('initial_belief', 0.5)),
                'embedding': embedding,
                'metadata': {
                    'source': 'manual_bootstrap',
                    'priority': hyp_data.get('priority', 'medium'),
                    'tags': hyp_data.get('tags', [])
                },
                'created_by': 'manual_bootstrap'
            })
            
            self.hypothesis_map[statement] = hypothesis_id
            print(f"  ✓ Added hypothesis: {statement[:80]}...")
        
        print(f"  Loaded {len(self.hypothesis_map)} hypotheses")
        print()
    
    def _load_raw_evidence(self):
        """Load raw evidence from text files, emails, notes"""
        print("Loading raw evidence...")
        
        evidence_dir = self.data_dir / "evidence"
        
        if not evidence_dir.exists():
            print("  No evidence directory found (data/initial/evidence/)")
            return
        
        count = 0
        
        for file_path in evidence_dir.glob("**/*"):
            if not file_path.is_file():
                continue
            
            if file_path.suffix not in ['.txt', '.md', '.email', '.note']:
                continue
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                continue
            
            metadata = self._extract_metadata_from_content(content, file_path)
            
            company_id = None
            if metadata.get('company'):
                company_id = self.company_map.get(metadata['company'])
            
            evidence_id = self.store.insert_evidence({
                'company_id': str(company_id) if company_id else None,
                'source_type': 'manual',
                'source_url': None,
                'source_date': metadata.get('date', date.today()),
                'title': metadata.get('title', file_path.stem),
                'content': content,
                'raw_metadata': {
                    'file_path': str(file_path.relative_to(self.data_dir)),
                    'file_type': file_path.suffix,
                    'source': 'manual_bootstrap',
                    **metadata
                },
                'validation_status': 'validated',
                'ingested_by': 'manual_bootstrap'
            })
            
            count += 1
            print(f"  ✓ Added evidence: {file_path.name}")
        
        print(f"  Loaded {count} evidence files")
        print()
    
    def _load_memos(self):
        """Load research memos from memos directory"""
        print("Loading memos...")
        
        memos_dir = self.data_dir / "memos"
        
        if not memos_dir.exists():
            print("  No memos directory found (data/initial/memos/)")
            return
        
        count = 0
        
        for file_path in memos_dir.glob("**/*.md"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                continue
            
            metadata = self._extract_metadata_from_content(content, file_path)
            
            company_id = None
            if metadata.get('company'):
                company_id = self.company_map.get(metadata['company'])
            
            theme_id = None
            if metadata.get('theme'):
                theme_id = self.theme_map.get(metadata['theme'])
            
            title = metadata.get('title', file_path.stem)
            
            embedding = self.embedding_gen.encode(f"{title}\n\n{content[:1000]}")
            
            query = """
                INSERT INTO memos (company_id, theme_id, title, content, memo_type, 
                                  author, embedding, created_at)
                VALUES (:company_id, :theme_id, :title, :content, :memo_type, 
                        :author, :embedding::vector, :created_at)
                RETURNING id
            """
            result = self.store.execute(query, {
                'company_id': str(company_id) if company_id else None,
                'theme_id': str(theme_id) if theme_id else None,
                'title': title,
                'content': content,
                'memo_type': metadata.get('type', 'deep_dive'),
                'author': metadata.get('author', 'manual_bootstrap'),
                'embedding': str(embedding),
                'created_at': metadata.get('date', datetime.now())
            })
            
            count += 1
            print(f"  ✓ Added memo: {title}")
        
        print(f"  Loaded {count} memos")
        print()
    
    def _load_priorities(self):
        """Load priorities from priorities.json"""
        print("Loading priorities...")
        
        priorities_file = self.data_dir / "priorities.json"
        
        if not priorities_file.exists():
            print("  No priorities file found (priorities.json)")
            return
        
        with open(priorities_file, 'r') as f:
            priorities = json.load(f)
        
        for priority in priorities:
            description = priority.get('description')
            
            if not description:
                continue
            
            query = """
                INSERT INTO themes (name, description, metadata)
                VALUES (:name, :description, :metadata)
                RETURNING id
            """
            result = self.store.execute(query, {
                'name': priority.get('name', f"Priority: {description[:50]}"),
                'description': description,
                'metadata': json.dumps({
                    'source': 'manual_bootstrap',
                    'type': 'priority',
                    'priority_level': priority.get('level', 'high'),
                    'timeframe': priority.get('timeframe', 'near_term')
                })
            })
            
            print(f"  ✓ Added priority: {priority.get('name', description[:50])}")
        
        print(f"  Loaded {len(priorities)} priorities")
        print()
    
    def _extract_metadata_from_content(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from content (YAML frontmatter or inline markers)"""
        metadata = {}
        
        lines = content.split('\n')
        
        if lines[0].strip() == '---':
            in_frontmatter = True
            frontmatter_lines = []
            
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    break
                frontmatter_lines.append(line)
            
            for line in frontmatter_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip().lower()] = value.strip()
        
        for line in lines[:20]:
            line_lower = line.lower()
            if 'company:' in line_lower:
                metadata['company'] = line.split(':', 1)[1].strip()
            elif 'theme:' in line_lower:
                metadata['theme'] = line.split(':', 1)[1].strip()
            elif 'date:' in line_lower:
                date_str = line.split(':', 1)[1].strip()
                try:
                    metadata['date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            elif 'title:' in line_lower:
                metadata['title'] = line.split(':', 1)[1].strip()
        
        return metadata


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bootstrap initial data into Nexus')
    parser.add_argument('--data-dir', default='data/initial',
                       help='Directory containing initial data files (default: data/initial)')
    
    args = parser.parse_args()
    
    bootstrap = InitialDataBootstrap(data_dir=args.data_dir)
    bootstrap.bootstrap_all()


if __name__ == '__main__':
    main()
