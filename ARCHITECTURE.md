# Nexus v0 Architecture

## 1. Minimal Architecture

### Components

**Event Bus (Redis Streams)**: Central message broker for all system events (ingestion, evidence extraction, belief updates, alerts). Provides persistent event log with consumer groups for reliable processing.

**Lakehouse (DuckDB + Parquet)**: Offline analytics and feature computation. Raw data stored as Parquet files in `/data/parquet`; DuckDB queries for aggregations, time-series analysis, and feature engineering.

**Feature Store (PostgreSQL)**: Materialized features for real-time serving. Stores computed metrics (revenue growth, hiring velocity, sentiment scores) with timestamps for hypothesis evaluation.

**Vector Index (pgvector in PostgreSQL)**: Semantic search over claims, memos, and evidence. Enables relevance scoring between hypotheses and incoming evidence via cosine similarity.

**Orchestration (Prefect 2)**: Schedules and manages monitoring flows (filings, earnings, hiring), investigation playbooks, and batch belief updates. Provides retry logic, flow visualization, and alerting.

**Model Router (LiteLLM + Mock)**: Abstraction layer for LLM calls. Defaults to deterministic mock extractor for local development; supports OpenAI/Anthropic via env config. Handles rate limiting, retries, and prompt logging.

**Belief Store (PostgreSQL)**: Append-only `belief_updates` table with full provenance; materialized `current_beliefs` view for fast queries. Stores log-odds, confidence intervals, and contributing evidence IDs.

**API (FastAPI)**: REST endpoints for UI, external integrations, and manual evidence submission. Publishes events to Redis; queries beliefs and investigations.

**UI (Streamlit)**: Dashboard for hypothesis monitoring, investigation triage, belief history visualization, and manual evidence annotation.

### Data Flow

```mermaid
graph TB
    subgraph "Ingestion Layer"
        SEC[SEC Filings]
        EARN[Earnings Transcripts]
        HIRE[Hiring Data]
        MANUAL[Manual Evidence]
    end
    
    subgraph "Event Bus"
        REDIS[Redis Streams]
    end
    
    subgraph "Processing Layer"
        PARSER[Parsers & Validators]
        LLM[Model Router]
        EXTRACT[Claim Extractor]
    end
    
    subgraph "Storage Layer"
        PG[(PostgreSQL)]
        PARQUET[Parquet Files]
        DUCK[DuckDB]
    end
    
    subgraph "Intelligence Layer"
        BELIEF[Belief Engine]
        INVEST[Investigation Orchestrator]
        ALERT[Alert Manager]
    end
    
    subgraph "Orchestration"
        PREFECT[Prefect Flows]
    end
    
    subgraph "Serving Layer"
        API[FastAPI]
        UI[Streamlit UI]
    end
    
    SEC --> REDIS
    EARN --> REDIS
    HIRE --> REDIS
    MANUAL --> API
    API --> REDIS
    
    REDIS --> PARSER
    PARSER --> EXTRACT
    EXTRACT --> LLM
    LLM --> REDIS
    
    REDIS --> PG
    REDIS --> PARQUET
    PARQUET --> DUCK
    
    PG --> BELIEF
    DUCK --> BELIEF
    BELIEF --> PG
    BELIEF --> ALERT
    
    ALERT --> INVEST
    INVEST --> PREFECT
    PREFECT --> REDIS
    
    PG --> API
    API --> UI
    
    PREFECT -.schedules.-> SEC
    PREFECT -.schedules.-> EARN
    PREFECT -.schedules.-> HIRE
```

### Interfaces

**Event Contracts**: JSON schemas for `ingestion.raw`, `evidence.extracted`, `belief.updated`, `investigation.triggered`, `alert.fired` (see Section 2).

**Storage Adapters**: Abstract interfaces for EventBus, VectorStore, BeliefStore, FeatureStore to enable component swapping.

**LLM Client**: Unified interface with `extract_claims(text, context)` method; implementations for Mock, OpenAI, Anthropic.

**Parser Registry**: Pluggable parsers for different document types (10-Q, 10-K, 8-K, earnings transcripts, job postings).

---

## 2. Ontology + Schemas

### Core Entities

**Company**: Legal entity being researched (public or private).
**Instrument**: Tradable security (stock, option, bond) linked to Company.
**Theme**: Investment thesis category (e.g., "AI Infrastructure", "Consumer Resilience").
**Hypothesis**: Testable proposition about a Company/Theme with belief state (e.g., "ACME revenue growth will exceed 30% YoY in Q4").
**Evidence**: Raw data artifact (filing, transcript, article, data point).
**Claim**: Structured assertion extracted from Evidence via LLM.
**Memo**: Human-authored research note with claims and reasoning.
**Prediction**: Quantitative forecast with confidence interval and time horizon.
**Position**: Investment allocation (long/short, size, entry/exit) linked to Hypotheses.

### SQL DDL

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Companies
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(10) UNIQUE,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    market_cap BIGINT,
    is_public BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_companies_sector ON companies(sector);

-- Instruments
CREATE TABLE instruments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    instrument_type VARCHAR(20) NOT NULL, -- 'stock', 'option', 'bond'
    exchange VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_instruments_company ON instruments(company_id);
CREATE INDEX idx_instruments_symbol ON instruments(symbol);

-- Themes
CREATE TABLE themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    parent_theme_id UUID REFERENCES themes(id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hypotheses
CREATE TABLE hypotheses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    theme_id UUID REFERENCES themes(id),
    statement TEXT NOT NULL,
    hypothesis_type VARCHAR(50), -- 'growth', 'margin', 'market_share', 'product', 'risk'
    time_horizon VARCHAR(20), -- 'short_term', 'medium_term', 'long_term'
    target_date DATE,
    initial_belief FLOAT DEFAULT 0.5,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved', 'archived'
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_hypotheses_company ON hypotheses(company_id);
CREATE INDEX idx_hypotheses_theme ON hypotheses(theme_id);
CREATE INDEX idx_hypotheses_status ON hypotheses(status);
CREATE INDEX idx_hypotheses_embedding ON hypotheses USING ivfflat (embedding vector_cosine_ops);

-- Evidence
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    source_type VARCHAR(50) NOT NULL, -- 'filing', 'transcript', 'news', 'hiring', 'manual'
    source_url TEXT,
    source_date DATE,
    title TEXT,
    content TEXT,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    raw_metadata JSONB,
    validation_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'validated', 'rejected'
    validation_errors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ingested_by VARCHAR(100)
);

CREATE INDEX idx_evidence_company ON evidence(company_id);
CREATE INDEX idx_evidence_source_type ON evidence(source_type);
CREATE INDEX idx_evidence_source_date ON evidence(source_date);
CREATE INDEX idx_evidence_content_hash ON evidence(content_hash);

-- Claims
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evidence_id UUID REFERENCES evidence(id),
    company_id UUID REFERENCES companies(id),
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(50), -- 'financial', 'operational', 'strategic', 'risk', 'sentiment'
    polarity VARCHAR(10), -- 'positive', 'negative', 'neutral'
    magnitude FLOAT, -- 0.0 to 1.0
    confidence FLOAT, -- 0.0 to 1.0
    extracted_entities JSONB,
    embedding vector(384),
    model_version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claims_evidence ON claims(evidence_id);
CREATE INDEX idx_claims_company ON claims(company_id);
CREATE INDEX idx_claims_type ON claims(claim_type);
CREATE INDEX idx_claims_embedding ON claims USING ivfflat (embedding vector_cosine_ops);

-- Hypothesis-Claim Links
CREATE TABLE hypothesis_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    claim_id UUID REFERENCES claims(id),
    relevance_score FLOAT NOT NULL, -- cosine similarity
    impact_direction VARCHAR(10), -- 'supports', 'contradicts', 'neutral'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hypothesis_id, claim_id)
);

CREATE INDEX idx_hypothesis_claims_hypothesis ON hypothesis_claims(hypothesis_id);
CREATE INDEX idx_hypothesis_claims_claim ON hypothesis_claims(claim_id);

-- Belief Updates (append-only)
CREATE TABLE belief_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    prior_belief FLOAT NOT NULL,
    posterior_belief FLOAT NOT NULL,
    log_odds_delta FLOAT NOT NULL,
    contributing_claims JSONB, -- array of {claim_id, weight, sign}
    reliability_score FLOAT,
    recency_score FLOAT,
    relevance_score FLOAT,
    uncertainty FLOAT,
    trigger_reason VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_belief_updates_hypothesis ON belief_updates(hypothesis_id);
CREATE INDEX idx_belief_updates_created_at ON belief_updates(created_at);

-- Current Beliefs (materialized view)
CREATE MATERIALIZED VIEW current_beliefs AS
SELECT DISTINCT ON (hypothesis_id)
    hypothesis_id,
    posterior_belief as current_belief,
    log_odds_delta,
    uncertainty,
    created_at as last_updated
FROM belief_updates
ORDER BY hypothesis_id, created_at DESC;

CREATE UNIQUE INDEX idx_current_beliefs_hypothesis ON current_beliefs(hypothesis_id);

-- Memos
CREATE TABLE memos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    theme_id UUID REFERENCES themes(id),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    memo_type VARCHAR(50), -- 'deep_dive', 'update', 'alert', 'investigation'
    author VARCHAR(100),
    related_hypotheses UUID[],
    related_evidence UUID[],
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memos_company ON memos(company_id);
CREATE INDEX idx_memos_theme ON memos(theme_id);
CREATE INDEX idx_memos_type ON memos(memo_type);

-- Predictions
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    company_id UUID REFERENCES companies(id),
    metric_name VARCHAR(100) NOT NULL,
    predicted_value FLOAT NOT NULL,
    confidence_lower FLOAT,
    confidence_upper FLOAT,
    prediction_date DATE NOT NULL,
    target_date DATE NOT NULL,
    model_version VARCHAR(50),
    actual_value FLOAT,
    actual_date DATE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_hypothesis ON predictions(hypothesis_id);
CREATE INDEX idx_predictions_company ON predictions(company_id);
CREATE INDEX idx_predictions_target_date ON predictions(target_date);

-- Positions
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument_id UUID REFERENCES instruments(id),
    position_type VARCHAR(10) NOT NULL, -- 'long', 'short'
    quantity FLOAT NOT NULL,
    entry_price FLOAT,
    entry_date DATE,
    exit_price FLOAT,
    exit_date DATE,
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'closed'
    related_hypotheses UUID[],
    rationale TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_positions_instrument ON positions(instrument_id);
CREATE INDEX idx_positions_status ON positions(status);

-- Investigations
CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    company_id UUID REFERENCES companies(id),
    investigation_type VARCHAR(50) NOT NULL, -- 'earnings_deep_dive', 'hiring_momentum', 'custom'
    trigger_reason TEXT,
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
    assigned_to VARCHAR(100),
    inputs JSONB,
    outputs JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_investigations_hypothesis ON investigations(hypothesis_id);
CREATE INDEX idx_investigations_company ON investigations(company_id);
CREATE INDEX idx_investigations_status ON investigations(status);
CREATE INDEX idx_investigations_priority ON investigations(priority);

-- Provenance Log (immutable audit trail)
CREATE TABLE provenance_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    actor VARCHAR(100),
    payload JSONB,
    content_hash VARCHAR(64),
    parent_event_id UUID REFERENCES provenance_log(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_provenance_entity ON provenance_log(entity_type, entity_id);
CREATE INDEX idx_provenance_event_type ON provenance_log(event_type);
CREATE INDEX idx_provenance_created_at ON provenance_log(created_at);

-- LLM Interactions (for compliance and reproducibility)
CREATE TABLE llm_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(100) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prompt_template VARCHAR(100),
    prompt_text TEXT NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    response_text TEXT,
    response_metadata JSONB,
    tokens_used INTEGER,
    latency_ms INTEGER,
    error TEXT,
    redacted_fields JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_interactions_request_id ON llm_interactions(request_id);
CREATE INDEX idx_llm_interactions_model ON llm_interactions(model_name);
CREATE INDEX idx_llm_interactions_created_at ON llm_interactions(created_at);

-- Feature Store
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- 'company', 'instrument', 'hypothesis'
    entity_id UUID NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value FLOAT,
    feature_metadata JSONB,
    computed_at TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_type, entity_id, feature_name, computed_at)
);

CREATE INDEX idx_features_entity ON features(entity_type, entity_id);
CREATE INDEX idx_features_name ON features(feature_name);
CREATE INDEX idx_features_computed_at ON features(computed_at);
```

### JSON Event Contracts

**Ingestion Event** (`ingestion.raw`)
```json
{
  "event_id": "uuid",
  "event_type": "ingestion.raw",
  "timestamp": "2025-11-11T19:00:00Z",
  "source": {
    "type": "filing|transcript|hiring|manual",
    "provider": "sec|earnings_call|greenhouse|user",
    "url": "https://...",
    "date": "2025-11-10"
  },
  "company": {
    "ticker": "ACME",
    "name": "Acme Corp"
  },
  "content": {
    "title": "Q3 2025 10-Q Filing",
    "text": "...",
    "metadata": {}
  },
  "content_hash": "sha256:...",
  "ingested_by": "monitor_filings_flow"
}
```

**Evidence Event** (`evidence.extracted`)
```json
{
  "event_id": "uuid",
  "event_type": "evidence.extracted",
  "timestamp": "2025-11-11T19:05:00Z",
  "evidence_id": "uuid",
  "company_id": "uuid",
  "claims": [
    {
      "claim_id": "uuid",
      "text": "Revenue grew 35% YoY to $150M",
      "type": "financial",
      "polarity": "positive",
      "magnitude": 0.8,
      "confidence": 0.92,
      "entities": {
        "metric": "revenue",
        "value": 150000000,
        "growth": 0.35,
        "period": "Q3 2025"
      },
      "embedding": [0.1, 0.2, ...]
    }
  ],
  "model_version": "gpt-4-2024-11-01",
  "extraction_metadata": {
    "latency_ms": 1200,
    "tokens_used": 450
  }
}
```

**Belief Update Event** (`belief.updated`)
```json
{
  "event_id": "uuid",
  "event_type": "belief.updated",
  "timestamp": "2025-11-11T19:10:00Z",
  "hypothesis_id": "uuid",
  "prior_belief": 0.65,
  "posterior_belief": 0.78,
  "log_odds_delta": 0.62,
  "contributing_claims": [
    {
      "claim_id": "uuid",
      "weight": 0.85,
      "sign": 1,
      "reliability": 0.92,
      "recency": 1.0,
      "relevance": 0.88
    }
  ],
  "uncertainty": 0.12,
  "trigger_reason": "new_evidence",
  "escalation_required": false
}
```

---

## 3. Monitoring v0

### Filing Pipeline

**Trigger**: Cron schedule (daily at 6 AM ET) + webhook from SEC EDGAR (future).

**Parser**: `FilingParser` extracts sections (Risk Factors, MD&A, Financial Statements) from 10-Q, 10-K, 8-K HTML/XBRL.

**Validation Rules**:
- Content hash uniqueness (no duplicate ingestion)
- Filing date within expected range (not future-dated)
- Company ticker matches SEC CIK mapping
- Required sections present (MD&A for 10-Q/10-K)
- File size < 50MB

**Alert Thresholds**:
- **High**: 8-K filed (material event)
- **Medium**: 10-Q/10-K filed with >20% revenue/earnings miss vs consensus
- **Low**: Routine 10-Q/10-K filed

**Triage Logic**:
1. Parse filing and extract claims
2. Match claims to active hypotheses (relevance > 0.7)
3. If matched hypotheses have high conviction (belief > 0.8 or < 0.2), escalate to High priority
4. If claim magnitude > 0.7 and contradicts hypothesis, trigger investigation
5. Otherwise, update beliefs and log

**Priority**:
- Critical: MNPI detected (insider trading keywords, non-public guidance)
- High: Material event (8-K), large belief delta (>0.2)
- Medium: Quarterly filing with moderate impact
- Low: Routine disclosure

### Earnings Pipeline

**Trigger**: Earnings calendar (scheduled 1 hour after market close on earnings date).

**Parser**: `TranscriptParser` segments transcript into Prepared Remarks and Q&A; extracts speaker, sentiment, and key metrics.

**Validation Rules**:
- Transcript date matches earnings date ±1 day
- Company name/ticker in transcript header
- Minimum length 5000 characters
- Speaker labels present

**Alert Thresholds**:
- **High**: Guidance revision >10%, unexpected loss, CEO/CFO departure mentioned
- **Medium**: Revenue/EPS beat/miss >5%, margin expansion/contraction >200bps
- **Low**: In-line results, routine commentary

**Triage Logic**:
1. Extract guidance, metrics, and sentiment from prepared remarks
2. Extract Q&A themes (product, competition, macro concerns)
3. Compare metrics to predictions table; flag misses
4. If guidance revised or sentiment shift detected, trigger Earnings Deep Dive investigation
5. Update beliefs for revenue/margin/product hypotheses

**Priority**:
- Critical: Guidance cut >20%, going concern warning
- High: Guidance revision >10%, unexpected loss
- Medium: Beat/miss >5%
- Low: In-line results

### Hiring Pipeline

**Trigger**: Polling job boards API (daily at 8 AM) or webhook from ATS integration.

**Parser**: `JobPostingParser` extracts role title, department, seniority, location, posting date, and keywords (AI, ML, sales, engineering).

**Validation Rules**:
- Posting date within last 30 days
- Company name matches database
- Role title non-empty
- Location valid (city/state or "Remote")

**Alert Thresholds**:
- **High**: >50 new postings in 7 days (hiring surge)
- **Medium**: >20 new postings in 7 days, or >5 senior/exec roles
- **Low**: <20 new postings in 7 days

**Triage Logic**:
1. Aggregate postings by department and seniority
2. Compute hiring velocity (7-day, 30-day rolling counts)
3. If velocity > 2x historical average, trigger Hiring Momentum investigation
4. If senior roles (VP+, Director) > 5, escalate to High priority
5. Update hiring_velocity feature in feature store

**Priority**:
- High: Hiring surge (>50 postings/week), multiple exec roles
- Medium: Moderate hiring (20-50 postings/week)
- Low: Steady-state hiring (<20 postings/week)

---

## 4. Investigation v0

### Playbook 1: Earnings Deep Dive

**Inputs**:
- `company_id`: UUID
- `earnings_date`: Date
- `transcript_id`: UUID (evidence ID)
- `trigger_reason`: String (e.g., "guidance_revision", "margin_compression")
- `related_hypotheses`: List[UUID]

**Steps**:
1. **Retrieve Context**: Fetch company financials (last 4 quarters), active hypotheses, prior predictions, and current beliefs.
2. **Extract Key Metrics**: Parse transcript for revenue, EPS, gross margin, operating margin, guidance, and segment breakdowns.
3. **Compare to Predictions**: Calculate deltas between actual and predicted values; flag misses >5%.
4. **Sentiment Analysis**: Run sentiment model on prepared remarks and Q&A; detect tone shift vs prior quarters.
5. **Competitive Context**: Query vector index for recent claims about competitors; assess relative performance.
6. **Generate Memo**: Synthesize findings into structured memo with sections: Summary, Key Metrics, Guidance Changes, Risks, Hypothesis Impacts.
7. **Update Beliefs**: For each related hypothesis, compute belief update based on evidence and write to belief_updates table.
8. **Escalate if Needed**: If belief delta >0.3 or uncertainty >0.4, assign to human analyst for review.

**Outputs**:
- `memo_id`: UUID (created memo)
- `belief_updates`: List[UUID] (updated hypotheses)
- `escalation_required`: Boolean
- `key_findings`: JSON with metrics, deltas, and sentiment scores

**Acceptance Criteria**:
- Memo generated within 30 minutes of transcript ingestion
- All related hypotheses updated with provenance links
- Escalation triggered if belief delta >0.3
- Key metrics extracted with >90% accuracy vs manual review

### Playbook 2: Hiring Momentum

**Inputs**:
- `company_id`: UUID
- `date_range`: (start_date, end_date)
- `trigger_reason`: String (e.g., "hiring_surge", "exec_hiring")
- `related_hypotheses`: List[UUID] (e.g., "ACME scaling AI team")

**Steps**:
1. **Aggregate Postings**: Query job postings for company in date range; group by department, seniority, and location.
2. **Compute Velocity**: Calculate 7-day, 30-day, and 90-day hiring velocity; compare to historical baseline.
3. **Department Analysis**: Identify departments with highest growth (e.g., Engineering +40%, Sales +25%).
4. **Seniority Mix**: Flag if senior roles (Director+, VP+) exceed 20% of postings (indicates expansion vs backfill).
5. **Keyword Extraction**: Extract role keywords (AI, ML, cloud, blockchain) and map to themes.
6. **Competitive Benchmark**: Compare hiring velocity to peer companies in same sector.
7. **Generate Memo**: Synthesize findings with sections: Hiring Velocity, Department Breakdown, Seniority Mix, Theme Mapping, Hypothesis Impacts.
8. **Update Beliefs**: For hypotheses related to growth, product development, or market expansion, update beliefs based on hiring signals.

**Outputs**:
- `memo_id`: UUID
- `hiring_metrics`: JSON with velocity, department breakdown, seniority mix
- `belief_updates`: List[UUID]
- `theme_signals`: JSON mapping themes to hiring evidence

**Acceptance Criteria**:
- Hiring metrics computed within 10 minutes of trigger
- Department breakdown accurate to ±5%
- Hypotheses updated if hiring velocity >2x baseline
- Memo includes competitive benchmark for top 3 peers

---

## 5. Belief Update Logic

### Log-Odds Specification

**Model**: Belief state represented as probability `p ∈ [0,1]`. Internally stored as log-odds `L = log(p / (1-p))`.

**Update Rule**: For new evidence `e` with claims `{c_1, ..., c_n}`, compute:

```
L' = L + Σ_i sgn(c_i) * w_i

where:
  sgn(c_i) = +1 if claim supports hypothesis, -1 if contradicts, 0 if neutral
  w_i = reliability(c_i) * recency(c_i) * relevance(c_i) * magnitude(c_i)
```

**Scoring Weights**:

1. **Reliability** `r ∈ [0,1]`: Source credibility and extraction confidence.
   - SEC filing: 0.95
   - Earnings transcript: 0.90
   - News article (tier 1): 0.75
   - Social media: 0.40
   - Manual entry: 0.85
   - Multiply by LLM extraction confidence

2. **Recency** `t ∈ [0,1]`: Exponential time decay.
   ```
   t = exp(-λ * Δt)
   where Δt = days since evidence date, λ = 0.01 (half-life ~70 days)
   ```

3. **Relevance** `rel ∈ [0,1]`: Cosine similarity between claim embedding and hypothesis embedding.
   ```
   rel = max(0, cosine_similarity(emb_claim, emb_hypothesis))
   Only link if rel ≥ 0.7
   ```

4. **Magnitude** `m ∈ [0,1]`: Claim strength from parser.
   - Large numeric delta (>20%): 0.9
   - Moderate delta (10-20%): 0.7
   - Qualitative strong: 0.6
   - Qualitative weak: 0.3

**Pseudocode**:

```python
def update_belief(hypothesis_id, new_claims):
    # Fetch current belief
    current = get_current_belief(hypothesis_id)
    L = log_odds(current.belief)
    
    # Compute weighted evidence
    delta_L = 0
    contributions = []
    
    for claim in new_claims:
        # Check relevance threshold
        relevance = cosine_similarity(claim.embedding, hypothesis.embedding)
        if relevance < 0.7:
            continue
        
        # Compute weights
        reliability = get_source_reliability(claim.source_type) * claim.confidence
        recency = exp(-0.01 * (today - claim.source_date).days)
        magnitude = claim.magnitude
        
        weight = reliability * recency * relevance * magnitude
        sign = get_claim_polarity(claim, hypothesis)  # +1, -1, 0
        
        delta_L += sign * weight
        contributions.append({
            'claim_id': claim.id,
            'weight': weight,
            'sign': sign,
            'reliability': reliability,
            'recency': recency,
            'relevance': relevance
        })
    
    # Apply update
    L_new = L + delta_L
    p_new = sigmoid(L_new)
    
    # Compute uncertainty (variance of contributions)
    uncertainty = compute_uncertainty(contributions)
    
    # Write belief update
    write_belief_update(
        hypothesis_id=hypothesis_id,
        prior_belief=current.belief,
        posterior_belief=p_new,
        log_odds_delta=delta_L,
        contributing_claims=contributions,
        uncertainty=uncertainty
    )
    
    # Check escalation rules
    if abs(delta_L) >= 0.5 or uncertainty >= 0.4:
        trigger_escalation(hypothesis_id, delta_L, uncertainty)
    
    return p_new
```

### Uncertainty Handling

**Conflicting Evidence**: If claims with opposite signs have similar weights, uncertainty increases.
```
uncertainty = std_dev([w_i * sgn_i for all claims]) / mean(|w_i|)
```

**Low Confidence**: If all claims have confidence <0.6, flag for manual review.

**Sparse Evidence**: If <3 claims in last 90 days, mark hypothesis as "data_starved" and reduce belief update magnitude by 50%.

### Escalation Rules

**Trigger Investigation** if:
- `|delta_L| ≥ 0.5` (large belief shift)
- `uncertainty ≥ 0.4` (high conflict or low confidence)
- `sign_flip and max(reliability) ≥ 0.8` (high-confidence contradiction)
- `belief crosses 0.5` (conviction flip)

**Assign Priority**:
- Critical: `|delta_L| ≥ 1.0` or `belief → [0.9, 1.0] or [0.0, 0.1]` (extreme conviction)
- High: `|delta_L| ≥ 0.5`
- Medium: `uncertainty ≥ 0.4`
- Low: Routine update

---

## 6. Provenance, Compliance, and Audit

### MNPI Gates

**Detection**: Keyword filter on ingested content before LLM processing.
- Keywords: "insider", "non-public", "confidential", "material non-public", "private placement", "unannounced"
- Regex: earnings numbers before official release, M&A mentions before announcement

**Action**: If MNPI detected:
1. Flag evidence with `validation_status = 'mnpi_hold'`
2. Do NOT send to LLM or belief engine
3. Alert compliance officer via Slack/email
4. Log to provenance with `action = 'mnpi_gate_triggered'`
5. Require manual review and approval before processing

**Compliance Review**: UI shows flagged evidence; officer can approve (with justification) or reject.

### Redaction

**PII Redaction**: Before LLM calls, redact:
- Email addresses: `[EMAIL]`
- Phone numbers: `[PHONE]`
- SSN/Tax IDs: `[SSN]`
- Names (if not public figures): `[NAME]`

**Sensitive Data**: Redact proprietary metrics, internal code names, unreleased product names.

**Logging**: Store redacted fields in `llm_interactions.redacted_fields` JSONB for audit.

### Prompt/Response Logging

**LLM Interactions Table**: Every LLM call logged with:
- `request_id`: Unique ID for tracing
- `prompt_text`: Full prompt (post-redaction)
- `prompt_hash`: SHA-256 of prompt for deduplication
- `response_text`: Full response
- `model_name`, `tokens_used`, `latency_ms`
- `created_at`: Timestamp

**Retention**: Keep logs for 7 years (regulatory requirement).

**Reproducibility**: Given `request_id`, can retrieve exact prompt and response; re-run with same prompt to verify determinism (for mock mode).

### Provenance Log

**Immutable Audit Trail**: Every action logged to `provenance_log`:
- Evidence ingestion: `event_type = 'evidence.ingested'`, `entity_type = 'evidence'`, `entity_id = evidence.id`
- Claim extraction: `event_type = 'claim.extracted'`, `parent_event_id = ingestion_event.id`
- Belief update: `event_type = 'belief.updated'`, `parent_event_id = claim_event.id`
- Investigation triggered: `event_type = 'investigation.triggered'`
- Position update: `event_type = 'position.updated'`

**Lineage**: `parent_event_id` links events into DAG; can trace any position back to source evidence.

**Content Hashing**: All evidence and claims hashed (SHA-256); stored in provenance for tamper detection.

**Query API**: `/api/provenance/{entity_type}/{entity_id}` returns full lineage graph.

---

## 7. Repo Skeleton and Run Script

### Folder Layout

```
nexus/
├── README.md
├── ARCHITECTURE.md
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── data/
│   ├── fixtures/
│   │   ├── companies.json
│   │   ├── sample_10q.html
│   │   ├── sample_transcript.txt
│   │   └── sample_hiring.json
│   └── parquet/
│       └── .gitkeep
├── db/
│   └── init.sql
├── nexus/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   └── events.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   ├── redis_bus.py
│   │   ├── vector_store.py
│   │   └── feature_store.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parsers.py
│   │   ├── validators.py
│   │   └── mnpi_filter.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   ├── mock_extractor.py
│   │   └── claim_extractor.py
│   ├── belief/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── scoring.py
│   │   └── escalation.py
│   ├── investigation/
│   │   ├── __init__.py
│   │   ├── playbooks.py
│   │   ├── earnings_deep_dive.py
│   │   └── hiring_momentum.py
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── filings_flow.py
│   │   ├── earnings_flow.py
│   │   └── hiring_flow.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── hypotheses.py
│   │   │   ├── evidence.py
│   │   │   ├── beliefs.py
│   │   │   └── investigations.py
│   │   └── schemas.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── pages/
│   │       ├── dashboard.py
│   │       ├── hypotheses.py
│   │       └── investigations.py
│   └── utils/
│       ├── __init__.py
│       ├── embeddings.py
│       ├── provenance.py
│       └── metrics.py
├── tests/
│   ├── __init__.py
│   ├── test_parsers.py
│   ├── test_belief_engine.py
│   ├── test_claim_extractor.py
│   └── test_api.py
└── scripts/
    ├── seed_fixtures.py
    ├── run_smoke_test.py
    └── eval_extraction.py
```

### Docker Compose Services

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: nexus
      POSTGRES_PASSWORD: nexus_dev_password
      POSTGRES_DB: nexus
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nexus"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  prefect-server:
    image: prefecthq/prefect:2-python3.11
    command: prefect server start --host 0.0.0.0
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
      PREFECT_SERVER_API_HOST: 0.0.0.0
    ports:
      - "4200:4200"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4200/api/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  worker:
    build: .
    command: python -m nexus.monitoring.worker
    environment:
      DATABASE_URL: postgresql://nexus:nexus_dev_password@postgres:5432/nexus
      REDIS_URL: redis://redis:6379
      PREFECT_API_URL: http://prefect-server:4200/api
      LLM_BACKEND: mock
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      prefect-server:
        condition: service_healthy
    volumes:
      - ./data:/app/data

  api:
    build: .
    command: uvicorn nexus.api.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql://nexus:nexus_dev_password@postgres:5432/nexus
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./data:/app/data

  ui:
    build: .
    command: streamlit run nexus/ui/app.py --server.port 8501 --server.address 0.0.0.0
    environment:
      API_URL: http://api:8000
    ports:
      - "8501:8501"
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### Makefile Targets

```makefile
.PHONY: help setup ingest test run eval clean

help:
	@echo "Nexus v0 - Investment Research System"
	@echo ""
	@echo "Targets:"
	@echo "  setup    - Initialize database and seed fixtures"
	@echo "  ingest   - Run ingestion pipelines on fixtures"
	@echo "  test     - Run unit and integration tests"
	@echo "  run      - Start all services (docker-compose up)"
	@echo "  eval     - Run evaluation suite"
	@echo "  clean    - Stop services and remove volumes"

setup:
	@echo "Setting up Nexus..."
	docker-compose up -d postgres redis
	@echo "Waiting for services..."
	sleep 10
	docker-compose run --rm worker python scripts/seed_fixtures.py
	@echo "Setup complete!"

ingest:
	@echo "Running ingestion pipelines..."
	docker-compose run --rm worker python -m nexus.monitoring.filings_flow
	docker-compose run --rm worker python -m nexus.monitoring.earnings_flow
	docker-compose run --rm worker python -m nexus.monitoring.hiring_flow
	@echo "Ingestion complete!"

test:
	@echo "Running tests..."
	docker-compose run --rm worker pytest tests/ -v
	@echo "Tests complete!"

run:
	@echo "Starting Nexus services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "  API: http://localhost:8000"
	@echo "  UI: http://localhost:8501"
	@echo "  Prefect: http://localhost:4200"

eval:
	@echo "Running evaluation suite..."
	docker-compose run --rm worker python scripts/eval_extraction.py
	@echo "Evaluation complete!"

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Cleanup complete!"
```

---

## 8. Evaluations and KPIs

### Extraction Metrics

**Precision**: `TP / (TP + FP)` where TP = correctly extracted claims, FP = hallucinated/incorrect claims.
- **Target**: ≥0.90
- **Measurement**: Manual annotation of 100 random claims per week; compare to ground truth.

**Recall**: `TP / (TP + FN)` where FN = missed claims in source document.
- **Target**: ≥0.85
- **Measurement**: Annotate 50 documents with all claims; measure extraction coverage.

**F1 Score**: Harmonic mean of precision and recall.
- **Target**: ≥0.87

**Entity Extraction Accuracy**: Correct extraction of metrics, dates, percentages.
- **Target**: ≥0.95
- **Measurement**: Compare extracted entities to ground truth on 100 claims.

### Latency Metrics

**Ingestion to Claim Extraction**: Time from evidence ingestion to claims written to DB.
- **Target**: p50 <30s, p95 <60s

**Belief Update Latency**: Time from claim extraction to belief update.
- **Target**: p50 <10s, p95 <30s

**Investigation Trigger to Memo**: Time from investigation trigger to completed memo.
- **Target**: Earnings Deep Dive <30min, Hiring Momentum <10min

**End-to-End**: Evidence ingestion to belief update.
- **Target**: p50 <60s, p95 <120s

### Coverage Metrics

**Hypothesis Coverage**: % of active hypotheses with ≥1 belief update in last 30 days.
- **Target**: ≥80%

**Evidence Utilization**: % of ingested evidence that generates ≥1 claim.
- **Target**: ≥70%

**Claim Linking**: % of claims linked to ≥1 hypothesis (relevance ≥0.7).
- **Target**: ≥60%

### Calibration Metrics

**Brier Score**: `(1/N) Σ (p_i - o_i)^2` where `p_i` = predicted belief, `o_i` = actual outcome (0 or 1).
- **Target**: <0.15 (well-calibrated)
- **Measurement**: For resolved hypotheses, compare final belief to actual outcome.

**Calibration Curve**: Plot predicted belief vs observed frequency in bins [0-0.1, 0.1-0.2, ..., 0.9-1.0].
- **Target**: Curve close to diagonal (perfect calibration).

**Sharpness**: Variance of predicted beliefs (higher = more decisive).
- **Target**: >0.1 (avoid clustering around 0.5)

### Belief Delta Alerts

**Large Shift**: Count of hypotheses with `|delta_L| ≥ 0.5` per week.
- **Target**: 5-10 (enough signal, not too noisy)

**Escalation Rate**: % of belief updates triggering escalation.
- **Target**: 5-10% (balance automation and human review)

**False Positive Rate**: % of escalations deemed unnecessary by analysts.
- **Target**: <20%

### 4-Week Build Plan

**Week 1: Core Infrastructure**
- Milestone: Database schema, event bus, and storage adapters functional
- Deliverables:
  - PostgreSQL with pgvector initialized
  - Redis Streams event bus with producer/consumer
  - Basic API with health check endpoint
  - Docker Compose stack running
- Acceptance: `make setup && make run` succeeds; API returns 200 on `/health`

**Week 2: Ingestion and Extraction**
- Milestone: Parsers and mock extractor operational
- Deliverables:
  - Filing, transcript, and hiring parsers
  - Mock claim extractor with deterministic outputs
  - Validation rules and MNPI filter
  - Fixtures seeded and ingested
- Acceptance: `make ingest` processes all fixtures; claims written to DB with embeddings

**Week 3: Belief Engine and Investigations**
- Milestone: Belief updates and playbooks functional
- Deliverables:
  - Belief engine with log-odds scoring
  - Escalation rules and uncertainty handling
  - Earnings Deep Dive and Hiring Momentum playbooks
  - Prefect flows for monitoring pipelines
- Acceptance: Belief updates triggered by fixture ingestion; investigations created for high-priority events

**Week 4: UI, Provenance, and Evaluation**
- Milestone: End-to-end system with UI and audit trail
- Deliverables:
  - Streamlit dashboard with hypothesis and investigation views
  - Provenance logging for all events
  - LLM interaction logging
  - Evaluation scripts for precision/recall and calibration
- Acceptance: `make eval` runs successfully; UI displays hypotheses with belief history; provenance API returns lineage

**Post-v0 Roadmap**:
- Week 5-6: LiteLLM integration with OpenAI/Anthropic; real data sources (SEC EDGAR API)
- Week 7-8: Advanced features (multi-hypothesis reasoning, portfolio optimization, backtesting)
- Week 9-12: Production hardening (auth, monitoring, alerting, CI/CD)
