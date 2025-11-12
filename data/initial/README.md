# Initial Data Setup for Nexus

This directory contains templates and examples for bootstrapping your initial data into Nexus. The system supports various input formats to accommodate different types of information you want to add.

## Quick Start

1. **Copy the example files** and remove the `.example` extension:
   ```bash
   cp companies.json.example companies.json
   cp themes.json.example themes.json
   cp hypotheses.json.example hypotheses.json
   cp priorities.json.example priorities.json
   ```

2. **Edit the files** with your actual data (see format details below)

3. **Add your raw thoughts, emails, and notes** to the `evidence/` directory

4. **Add your research memos** to the `memos/` directory

5. **Run the bootstrap script**:
   ```bash
   # From the repository root
   python scripts/bootstrap_initial_data.py
   
   # Or with Docker
   docker-compose run --rm worker python scripts/bootstrap_initial_data.py
   ```

## File Formats

### Companies (`companies.json` or `companies.csv`)

Define the companies you want to track. Supports both JSON and CSV formats.

**JSON Format:**
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

**CSV Format:**
```csv
ticker,name,sector,market_cap,is_public,notes
ACME,Acme Corp,Technology,50000000000,true,Leading AI infrastructure company
```

**Fields:**
- `ticker` (optional): Stock ticker symbol
- `name` (required): Company name
- `sector` (optional): Industry sector
- `market_cap` (optional): Market capitalization in dollars
- `is_public` (optional): true/false, defaults to true
- `notes` (optional): Additional notes about the company

### Themes (`themes.json`)

Define investment themes or focus areas.

```json
[
  {
    "name": "AI Infrastructure",
    "description": "Companies building foundational AI infrastructure",
    "tags": ["ai", "infrastructure", "enterprise"]
  }
]
```

**Fields:**
- `name` (required): Theme name
- `description` (optional): Detailed description
- `tags` (optional): Array of tags for categorization

### Hypotheses (`hypotheses.json`)

Define your investment hypotheses to track.

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
    "tags": ["revenue", "growth", "q4"]
  }
]
```

**Fields:**
- `statement` (required): The hypothesis statement
- `company` (optional): Company ticker or name (must match companies.json)
- `theme` (optional): Theme name (must match themes.json)
- `type` (optional): growth, margin, market_share, product, risk, custom
- `time_horizon` (optional): short_term, medium_term, long_term
- `target_date` (optional): YYYY-MM-DD format
- `initial_belief` (optional): 0.0 to 1.0, defaults to 0.5
- `priority` (optional): low, medium, high, critical
- `tags` (optional): Array of tags

### Priorities (`priorities.json`)

Define your current priorities and focus areas.

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

**Fields:**
- `name` (required): Priority name
- `description` (required): Detailed description
- `level` (optional): low, medium, high, critical
- `timeframe` (optional): near_term, medium_term, long_term, ongoing

### Raw Evidence (`evidence/` directory)

Add your raw thoughts, emails, notes, and other unstructured content as text files.

**Supported file types:**
- `.txt` - Plain text files
- `.md` - Markdown files
- `.email` - Email content
- `.note` - Notes

**Optional metadata** (add at the top of the file):

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

**Examples:**
- `evidence/thought-about-acme.txt` - Random thoughts
- `evidence/email-from-contact.email` - Email content
- `evidence/notes-from-meeting.note` - Meeting notes
- `evidence/research-snippet.md` - Research snippets

### Research Memos (`memos/` directory)

Add structured research memos as Markdown files.

**Format:**
```markdown
---
company: ACME
theme: AI Infrastructure
type: deep_dive
author: Your Name
date: 2025-11-05
---

# Memo Title

## Executive Summary

[Your analysis here...]
```

**Metadata fields:**
- `company` (optional): Company ticker or name
- `theme` (optional): Theme name
- `type` (optional): deep_dive, update, alert, investigation
- `author` (optional): Author name
- `date` (optional): YYYY-MM-DD format

## Directory Structure

```
data/initial/
├── README.md                          # This file
├── companies.json                     # Your companies (copy from .example)
├── companies.csv                      # Alternative CSV format
├── themes.json                        # Your investment themes
├── hypotheses.json                    # Your hypotheses to track
├── priorities.json                    # Your current priorities
├── evidence/                          # Raw thoughts, emails, notes
│   ├── thought-1.txt
│   ├── email-from-contact.email
│   └── meeting-notes.md
└── memos/                             # Structured research memos
    ├── acme-deep-dive.md
    └── market-analysis.md
```

## Tips

1. **Start simple**: Begin with just companies and a few hypotheses
2. **Iterate**: You can run the bootstrap script multiple times (it will add new data)
3. **Use metadata**: Add company/theme/date metadata to evidence files for better organization
4. **Mix formats**: Use JSON for structured data, text files for unstructured thoughts
5. **Organize by topic**: Create subdirectories in `evidence/` and `memos/` to organize by company or theme

## Advanced Usage

### Custom data directory

```bash
python scripts/bootstrap_initial_data.py --data-dir /path/to/your/data
```

### Incremental updates

The bootstrap script is idempotent for companies and themes (won't create duplicates). For hypotheses and evidence, it will create new entries each time you run it.

## What Gets Created

When you run the bootstrap script, it will:

1. **Companies**: Insert into the `companies` table
2. **Themes**: Insert into the `themes` table
3. **Hypotheses**: Insert into the `hypotheses` table with embeddings
4. **Evidence**: Insert into the `evidence` table (marked as validated)
5. **Memos**: Insert into the `memos` table with embeddings
6. **Priorities**: Insert as special themes with priority metadata

All data is tagged with `source: manual_bootstrap` for provenance tracking.

## Next Steps

After bootstrapping your initial data:

1. **View in the UI**: Access http://localhost:8501 to see your data
2. **Use the API**: Query via http://localhost:8000/docs
3. **Run monitoring**: The system will start monitoring for new evidence
4. **Add more data**: Continue adding files to `evidence/` and `memos/` and re-run the script

## Troubleshooting

**Error: "Data directory not found"**
- Make sure you're running from the repository root
- Or specify the full path with `--data-dir`

**Error: "Company not found"**
- Make sure company tickers/names in hypotheses.json match companies.json exactly
- Check for typos and case sensitivity

**Files not being ingested**
- Check file extensions (.txt, .md, .email, .note)
- Make sure files are not empty
- Check file encoding (should be UTF-8)

## Support

For questions or issues, refer to the main Nexus documentation or contact the development team.
