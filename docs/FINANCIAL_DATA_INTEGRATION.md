# Financial Data Integration

## Overview

The financial data integration system enables Nexus to ingest quantitative financial data from reputable and free/cheap sources. The system monitors stock prices, financial statements, and earnings data for tracked companies, integrating seamlessly with the existing Nexus architecture.

## Data Sources

### Primary: Yahoo Finance (via yfinance)
- **Cost**: Free, no API key required
- **Rate Limits**: None (reasonable use expected)
- **Data Available**:
  - Daily and historical stock prices
  - Financial statements (income statement, balance sheet, cash flow)
  - Earnings data (quarterly and annual)
  - Company information
- **Reliability**: High, widely used in production systems

### Secondary: Alpha Vantage (optional)
- **Cost**: Free tier with 25 requests/day, 5 requests/minute
- **API Key**: Required (get at https://www.alphavantage.co/support/#api-key)
- **Data Available**:
  - Stock prices
  - Company overview and fundamentals
- **Use Case**: Fallback when Yahoo Finance is unavailable

## Architecture

The financial data integration follows the existing Nexus architecture:

```
Financial Data Sources → Connectors → Parsers → Monitoring Flows
    ↓
Evidence Storage → Event Bus → Claim Extraction → Belief Updates
    ↓
API Endpoints → UI/External Systems
```

### Components

1. **Connectors** (`nexus/ingestion/financial_connectors.py`)
   - `YahooFinanceConnector`: Primary connector using yfinance library
   - `AlphaVantageConnector`: Secondary connector with API key
   - `FinancialDataConnector`: Unified connector with automatic fallback

2. **Parsers** (`nexus/ingestion/financial_parsers.py`)
   - `StockPriceParser`: Parse stock price data into evidence format
   - `FinancialStatementsParser`: Parse financial statements
   - `EarningsParser`: Parse earnings data
   - `CompanyInfoParser`: Parse company information

3. **Monitoring Flows** (`nexus/monitoring/`)
   - `stock_prices_flow.py`: Monitor daily stock prices
   - `financials_flow.py`: Monitor financial statements
   - `earnings_data_flow.py`: Monitor earnings data

4. **API Endpoints** (`nexus/api/routes/financial_data.py`)
   - `/api/financial/stock-price/{ticker}`: Get current stock price
   - `/api/financial/historical-prices/{ticker}`: Get historical prices
   - `/api/financial/financials/{ticker}`: Get financial statements
   - `/api/financial/earnings/{ticker}`: Get earnings data
   - `/api/financial/company-info/{ticker}`: Get company information
   - `/api/financial/evidence/financial/{ticker}`: Get stored financial evidence

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The `yfinance` library is automatically installed as part of the requirements.

### 2. Configure Environment (Optional)

If you want to use Alpha Vantage as a fallback:

```bash
# Copy .env.example to .env
cp .env.example .env

# Add your Alpha Vantage API key
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

### 3. Ensure Companies are Tracked

The monitoring flows fetch data for all companies in the database with:
- A valid `ticker` symbol
- `is_public = true`

Add companies to track:

```python
from nexus.storage.postgres import PostgresStore

store = PostgresStore()
store.insert_company({
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "sector": "Technology",
    "is_public": True
})
```

## Usage

### Running Monitoring Flows

#### Monitor Stock Prices

```bash
# Monitor all tracked companies
python -m nexus.monitoring.stock_prices_flow

# Monitor historical prices for a specific ticker
python -c "from nexus.monitoring.stock_prices_flow import monitor_historical_prices; monitor_historical_prices('AAPL', days=30)"
```

#### Monitor Financial Statements

```bash
python -m nexus.monitoring.financials_flow
```

#### Monitor Earnings Data

```bash
python -m nexus.monitoring.earnings_data_flow
```

### Using the API

Start the API server:

```bash
python -m nexus.api.main
```

Then access the endpoints:

```bash
# Get current stock price
curl http://localhost:8000/api/financial/stock-price/AAPL

# Get historical prices (last 30 days)
curl http://localhost:8000/api/financial/historical-prices/AAPL?days=30

# Get financial statements
curl http://localhost:8000/api/financial/financials/AAPL

# Get earnings data
curl http://localhost:8000/api/financial/earnings/AAPL

# Get company information
curl http://localhost:8000/api/financial/company-info/AAPL

# Get stored financial evidence
curl http://localhost:8000/api/financial/evidence/financial/AAPL?limit=10
```

### Using Connectors Directly

```python
from nexus.ingestion.financial_connectors import FinancialDataConnector

connector = FinancialDataConnector()

# Get stock price
price = connector.get_stock_price("AAPL")
print(f"Current price: ${price['close']}")

# Get historical prices
prices = connector.get_historical_prices("AAPL", "2025-10-01", "2025-11-01")
print(f"Fetched {len(prices)} price points")

# Get financial statements
financials = connector.get_financials("AAPL")
print(f"Revenue: ${financials['income_statement']['total_revenue']}")

# Get earnings
earnings = connector.get_earnings("AAPL")
print(f"Quarterly earnings: {len(earnings['quarterly_earnings'])} quarters")

# Get company info
info = connector.get_company_info("AAPL")
print(f"Company: {info['name']} ({info['sector']})")
```

## Data Flow

### 1. Ingestion

Monitoring flows fetch data from financial data sources:

```
Financial API → Connector → Parser → Evidence Record
```

### 2. Storage

Evidence is stored in PostgreSQL with full provenance:

```sql
INSERT INTO evidence (
    company_id, source_type, source_url, source_date,
    title, content, content_hash, raw_metadata,
    validation_status, ingested_by
) VALUES (...)
```

### 3. Event Publishing

Events are published to Redis Streams for downstream processing:

```json
{
  "event_type": "ingestion.raw",
  "source": {
    "type": "stock_price",
    "provider": "yahoo_finance"
  },
  "company": {
    "id": "uuid",
    "ticker": "AAPL"
  },
  "content": {
    "title": "AAPL Stock Price - 2025-11-12",
    "text": "...",
    "metadata": {...}
  }
}
```

### 4. Claim Extraction

The existing claim extraction system processes financial evidence:

```
Evidence → LLM Extractor → Claims → Hypothesis Matching → Belief Updates
```

## Scheduling

Use Prefect to schedule regular monitoring:

```python
from prefect import flow, task
from prefect.schedules import IntervalSchedule
from datetime import timedelta

@flow(schedule=IntervalSchedule(interval=timedelta(hours=1)))
def scheduled_stock_monitoring():
    from nexus.monitoring.stock_prices_flow import monitor_stock_prices
    monitor_stock_prices()

@flow(schedule=IntervalSchedule(interval=timedelta(days=1)))
def scheduled_financials_monitoring():
    from nexus.monitoring.financials_flow import monitor_financials
    monitor_financials()
```

## Error Handling

The system handles errors gracefully:

1. **API Failures**: Automatic fallback to secondary data source
2. **Invalid Tickers**: Returns error without crashing
3. **Rate Limits**: Respects rate limits (especially for Alpha Vantage)
4. **Data Validation**: Validates evidence before storage

## Testing

Run the test suite:

```bash
# Run all financial integration tests
pytest tests/test_financial_integration.py -v

# Run with coverage
pytest tests/test_financial_integration.py --cov=nexus.ingestion --cov=nexus.monitoring
```

## Monitoring and Observability

All financial data ingestion is logged with full provenance:

```sql
-- View recent financial data ingestion
SELECT 
    event_type,
    entity_type,
    action,
    payload,
    created_at
FROM provenance_log
WHERE action IN (
    'stock_price_fetched',
    'financial_statements_fetched',
    'earnings_data_fetched'
)
ORDER BY created_at DESC
LIMIT 10;
```

## Best Practices

1. **Rate Limiting**: Be mindful of API rate limits, especially with Alpha Vantage
2. **Caching**: Consider caching frequently accessed data
3. **Scheduling**: Run stock price monitoring during market hours for real-time data
4. **Error Monitoring**: Monitor provenance logs for ingestion failures
5. **Data Quality**: Validate financial data before using in belief updates

## Troubleshooting

### Issue: "yfinance library not installed"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "No data found for ticker"

**Possible Causes**:
- Invalid ticker symbol
- Company not publicly traded
- Data temporarily unavailable

**Solution**: Verify ticker symbol and try again later

### Issue: Alpha Vantage rate limit exceeded

**Solution**: 
- Wait for rate limit to reset (1 minute for per-minute limit, 24 hours for daily limit)
- Use Yahoo Finance as primary source (no rate limits)

### Issue: "Company not found for ticker"

**Solution**: Add the company to the database first
```python
store.insert_company({
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "is_public": True
})
```

## Future Enhancements

Potential improvements for future versions:

1. **Additional Data Sources**: 
   - Financial Modeling Prep API
   - IEX Cloud
   - Polygon.io

2. **Real-time Data**: 
   - WebSocket connections for live prices
   - Streaming data ingestion

3. **Advanced Analytics**:
   - Technical indicators (RSI, MACD, etc.)
   - Sentiment analysis from news
   - Insider trading data

4. **Performance Optimization**:
   - Batch processing for multiple tickers
   - Parallel data fetching
   - Intelligent caching strategies

5. **Data Quality**:
   - Anomaly detection
   - Data reconciliation across sources
   - Historical data backfilling

## References

- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [Alpha Vantage API Documentation](https://www.alphavantage.co/documentation/)
- [Nexus Architecture](../ARCHITECTURE.md)
