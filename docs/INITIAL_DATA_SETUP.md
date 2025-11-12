# Initial Data Setup Guide

This guide explains how to bootstrap Nexus with your initial knowledge, thoughts, and investment data.

## Overview

Nexus provides a flexible system for loading your initial data, including:

- **Companies**: Companies you want to track (public or private)
- **Themes**: Investment themes and focus areas
- **Hypotheses**: Testable propositions about companies or markets
- **Raw Evidence**: Unstructured thoughts, emails, notes, and documents
- **Research Memos**: Structured analysis and deep dives
- **Priorities**: Current focus areas and priorities

The system is designed to handle both structured data (JSON, CSV) and unstructured content (text files, emails, notes), making it easy to add whatever information you have in whatever format works best for you.

## Quick Start

### 1. Prepare Your Data Directory

The bootstrap system looks for data in `data/initial/`. Example files are provided to help you get started:

```bash
cd data/initial/

# Copy example files and customize them
cp companies.json.example companies.json
cp themes.json.example themes.json
cp hypotheses.json.example hypotheses.json
cp priorities.json.example priorities.json

# Edit these files with your actual data
```

### 2. Add Your Content

**Structured Data** (edit the JSON files):
- `companies.json` - Companies you track
- `themes.json` - Investment themes
- `hypotheses.json` - Hypotheses to monitor
- `priorities.json` - Current priorities

**Unstructured Content** (add files to directories):
- `evidence/` - Raw thoughts, emails, notes (`.txt`, `.md`, `.email`, `.note`)
- `memos/` - Research memos (`.md`)

### 3. Run the Bootstrap

```bash
# Make sure services are running
make setup

# Bootstrap your data
make bootstrap

# Or run directly
python scripts/bootstrap_initial_data.py
```

## Data Formats

### Companies

**JSON Format** (`companies.json`):
```json
[
  {
    "ticker": "ACME",
    "name": "Acme Corp",
    "sector": "Technology",
    "market_cap": 50000000000,
    "is_public": true,
    "notes": "Leading AI infrastructure company"
  }
]
```

**CSV Format** (`companies.csv`):
```csv
ticker,name,sector,market_cap,is_public,notes
ACME,Acme Corp,Technology,50000000000,true,Leading AI infrastructure company
```

### Themes

```json
[
  {
    "name": "AI Infrastructure",
    "description": "Companies building foundational AI infrastructure",
    "tags": ["ai", "infrastructure", "enterprise"]
  }
]
```

### Hypotheses

```json
[
  {
    "statement": "ACME revenue growth will exceed 30% YoY in Q4 2025",
    "company": "ACME",
    "theme": "AI Infrastructure",
    "type": "growth",
    "time_horizon": "short_term",
    "target_date": "2025-12-31",
    "initial_belief": 0.65,
    "priority": "high",
    "tags": ["revenue", "growth"]
  }
]
```

**Hypothesis Types**: `growth`, `margin`, `market_share`, `product`, `risk`, `custom`

**Time Horizons**: `short_term`, `medium_term`, `long_term`

**Initial Belief**: 0.0 (no confidence) to 1.0 (full confidence), defaults to 0.5

### Raw Evidence

Add any text files to `evidence/` directory. The system supports:
- `.txt` - Plain text
- `.md` - Markdown
- `.email` - Email content
- `.note` - Notes

**Optional Metadata** (add at the top of files):

```
Company: ACME
Date: 2025-11-10
Title: My thoughts on ACME

[Your content here...]
```

Or use YAML frontmatter:

```
---
company: ACME
date: 2025-11-10
title: My thoughts on ACME
---

[Your content here...]
```

### Research Memos

Add Markdown files to `memos/` directory:

```markdown
---
company: ACME
theme: AI Infrastructure
type: deep_dive
author: Your Name
date: 2025-11-05
---

# ACME Deep Dive

## Executive Summary
[Your analysis...]

## Key Findings
[Your findings...]
```

**Memo Types**: `deep_dive`, `update`, `alert`, `investigation`

### Priorities

```json
[
  {
    "name": "Q4 Earnings Season",
    "description": "Focus on Q4 earnings for AI infrastructure companies",
    "level": "high",
    "timeframe": "near_term"
  }
]
```

**Priority Levels**: `low`, `medium`, `high`, `critical`

**Timeframes**: `near_term`, `medium_term`, `long_term`, `ongoing`

## Workflow Examples

### Example 1: Starting from Scratch

You have a list of companies, some investment theses, and scattered notes.

1. **Create companies.json** with your watchlist
2. **Create themes.json** with your investment themes
3. **Create hypotheses.json** with your key theses
4. **Dump your notes** into `evidence/` as text files
5. **Run bootstrap**: `make bootstrap`

### Example 2: Adding Email Insights

You received an email with market insights.

1. **Save email content** to `evidence/insight-from-contact.email`
2. **Add metadata** at the top:
   ```
   Company: ACME
   Date: 2025-11-10
   Title: Email from industry contact
   ```
3. **Run bootstrap**: `make bootstrap`

### Example 3: Adding Research Memos

You wrote a deep dive on a company.

1. **Create markdown file** in `memos/acme-analysis.md`
2. **Add frontmatter** with metadata
3. **Write your analysis** in markdown
4. **Run bootstrap**: `make bootstrap`

## Best Practices

### Organization

- **Use subdirectories**: Organize evidence and memos by company or theme
  ```
  evidence/
    acme/
      thought-1.txt
      email-2.email
    beta/
      notes.md
  ```

- **Consistent naming**: Use descriptive filenames with dates
  ```
  evidence/acme-q3-thoughts-2025-11-10.txt
  memos/acme-deep-dive-2025-11-05.md
  ```

### Metadata

- **Always add dates**: Helps with recency scoring in belief updates
- **Link to companies**: Enables automatic hypothesis matching
- **Use tags**: Makes it easier to find related content later

### Incremental Updates

- **Run bootstrap multiple times**: It's safe to re-run as you add more data
- **Companies and themes**: Won't create duplicates (checks by name/ticker)
- **Evidence and memos**: Creates new entries each time
- **Hypotheses**: Creates new entries (be careful not to duplicate)

### Data Quality

- **Be specific in hypotheses**: "Revenue growth >30%" is better than "Strong growth"
- **Include timeframes**: Helps the system know when to evaluate
- **Set realistic initial beliefs**: Don't start at 0.0 or 1.0 unless you're certain
- **Add context in notes**: More context = better claim extraction later

## Advanced Usage

### Custom Data Directory

```bash
python scripts/bootstrap_initial_data.py --data-dir /path/to/your/data
```

### Programmatic Access

You can also use the bootstrap class directly in Python:

```python
from scripts.bootstrap_initial_data import InitialDataBootstrap

bootstrap = InitialDataBootstrap(data_dir="data/initial")
bootstrap.bootstrap_all()
```

### Batch Processing

For large amounts of data, organize by batches:

```
data/initial/
  batch-1/
    companies.json
    hypotheses.json
  batch-2/
    companies.json
    hypotheses.json
```

Then run:
```bash
python scripts/bootstrap_initial_data.py --data-dir data/initial/batch-1
python scripts/bootstrap_initial_data.py --data-dir data/initial/batch-2
```

## Integration with Nexus

After bootstrapping, your data is immediately available:

### Via UI (Streamlit)

```bash
make run
# Visit http://localhost:8501
```

- View companies and hypotheses
- See belief states
- Browse evidence and memos

### Via API (FastAPI)

```bash
# Visit http://localhost:8000/docs
```

- Query hypotheses: `GET /hypotheses/`
- View beliefs: `GET /beliefs/`
- Search evidence: `GET /evidence/`

### Automatic Processing

Once data is loaded:

1. **Embeddings are generated** for hypotheses and memos
2. **Evidence is validated** and ready for claim extraction
3. **Monitoring flows** will start tracking your companies
4. **Belief updates** will occur as new evidence arrives

## Troubleshooting

### "Data directory not found"

Make sure you're running from the repository root, or specify the full path:
```bash
python scripts/bootstrap_initial_data.py --data-dir /full/path/to/data/initial
```

### "Company not found" in hypotheses

Company references in `hypotheses.json` must exactly match the ticker or name in `companies.json`. Check for:
- Typos
- Case sensitivity
- Extra spaces

### Files not being ingested

Check:
- File extensions (must be `.txt`, `.md`, `.email`, or `.note`)
- Files are not empty
- File encoding is UTF-8
- Files are in the correct directory (`evidence/` or `memos/`)

### Database connection errors

Make sure services are running:
```bash
make setup  # Starts postgres and redis
```

## Next Steps

After bootstrapping your initial data:

1. **Review in UI**: Check that everything loaded correctly
2. **Run monitoring**: Start ingestion pipelines with `make ingest`
3. **Add more data**: Continue adding evidence and memos as you work
4. **Monitor beliefs**: Watch how beliefs update as new evidence arrives
5. **Trigger investigations**: High-priority belief changes will trigger investigations

## Support

For detailed format specifications, see `data/initial/README.md`.

For questions about the system architecture, see `ARCHITECTURE.md`.
