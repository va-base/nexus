CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

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

CREATE TABLE instruments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    instrument_type VARCHAR(20) NOT NULL,
    exchange VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_instruments_company ON instruments(company_id);
CREATE INDEX idx_instruments_symbol ON instruments(symbol);

CREATE TABLE themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    parent_theme_id UUID REFERENCES themes(id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE hypotheses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    theme_id UUID REFERENCES themes(id),
    statement TEXT NOT NULL,
    hypothesis_type VARCHAR(50),
    time_horizon VARCHAR(20),
    target_date DATE,
    initial_belief FLOAT DEFAULT 0.5,
    status VARCHAR(20) DEFAULT 'active',
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_hypotheses_company ON hypotheses(company_id);
CREATE INDEX idx_hypotheses_theme ON hypotheses(theme_id);
CREATE INDEX idx_hypotheses_status ON hypotheses(status);
CREATE INDEX idx_hypotheses_embedding ON hypotheses USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    source_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    source_date DATE,
    title TEXT,
    content TEXT,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    raw_metadata JSONB,
    validation_status VARCHAR(20) DEFAULT 'pending',
    validation_errors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ingested_by VARCHAR(100)
);

CREATE INDEX idx_evidence_company ON evidence(company_id);
CREATE INDEX idx_evidence_source_type ON evidence(source_type);
CREATE INDEX idx_evidence_source_date ON evidence(source_date);
CREATE INDEX idx_evidence_content_hash ON evidence(content_hash);

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evidence_id UUID REFERENCES evidence(id),
    company_id UUID REFERENCES companies(id),
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(50),
    polarity VARCHAR(10),
    magnitude FLOAT,
    confidence FLOAT,
    extracted_entities JSONB,
    embedding vector(384),
    model_version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claims_evidence ON claims(evidence_id);
CREATE INDEX idx_claims_company ON claims(company_id);
CREATE INDEX idx_claims_type ON claims(claim_type);
CREATE INDEX idx_claims_embedding ON claims USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE hypothesis_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    claim_id UUID REFERENCES claims(id),
    relevance_score FLOAT NOT NULL,
    impact_direction VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hypothesis_id, claim_id)
);

CREATE INDEX idx_hypothesis_claims_hypothesis ON hypothesis_claims(hypothesis_id);
CREATE INDEX idx_hypothesis_claims_claim ON hypothesis_claims(claim_id);

CREATE TABLE belief_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    prior_belief FLOAT NOT NULL,
    posterior_belief FLOAT NOT NULL,
    log_odds_delta FLOAT NOT NULL,
    contributing_claims JSONB,
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

CREATE TABLE memos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    theme_id UUID REFERENCES themes(id),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    memo_type VARCHAR(50),
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

CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument_id UUID REFERENCES instruments(id),
    position_type VARCHAR(10) NOT NULL,
    quantity FLOAT NOT NULL,
    entry_price FLOAT,
    entry_date DATE,
    exit_price FLOAT,
    exit_date DATE,
    status VARCHAR(20) DEFAULT 'open',
    related_hypotheses UUID[],
    rationale TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_positions_instrument ON positions(instrument_id);
CREATE INDEX idx_positions_status ON positions(status);

CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    company_id UUID REFERENCES companies(id),
    investigation_type VARCHAR(50) NOT NULL,
    trigger_reason TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
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

CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
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
