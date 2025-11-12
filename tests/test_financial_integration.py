"""Tests for financial data integration"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from nexus.ingestion.financial_connectors import (
    YahooFinanceConnector,
    AlphaVantageConnector,
    FinancialDataConnector,
    DataSource
)
from nexus.ingestion.financial_parsers import (
    StockPriceParser,
    FinancialStatementsParser,
    EarningsParser,
    CompanyInfoParser
)


class TestYahooFinanceConnector:
    """Test Yahoo Finance connector"""
    
    @patch('nexus.ingestion.financial_connectors.yfinance')
    def test_get_stock_price(self, mock_yf):
        """Test getting stock price"""
        mock_ticker = Mock()
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.iloc = [Mock()]
        mock_hist.iloc[-1] = {
            'Open': 150.0,
            'High': 155.0,
            'Low': 149.0,
            'Close': 154.0,
            'Volume': 1000000
        }
        mock_hist.index = [datetime(2025, 11, 12)]
        mock_ticker.history.return_value = mock_hist
        mock_yf.Ticker.return_value = mock_ticker
        
        connector = YahooFinanceConnector()
        connector.yf = mock_yf
        
        result = connector.get_stock_price("AAPL")
        
        assert result["ticker"] == "AAPL"
        assert result["close"] == 154.0
        assert result["volume"] == 1000000
        assert "error" not in result
    
    @patch('nexus.ingestion.financial_connectors.yfinance')
    def test_get_stock_price_error(self, mock_yf):
        """Test error handling for stock price"""
        mock_ticker = Mock()
        mock_hist = MagicMock()
        mock_hist.empty = True
        mock_ticker.history.return_value = mock_hist
        mock_yf.Ticker.return_value = mock_ticker
        
        connector = YahooFinanceConnector()
        connector.yf = mock_yf
        
        result = connector.get_stock_price("INVALID")
        
        assert "error" in result


class TestStockPriceParser:
    """Test stock price parser"""
    
    def test_parse_stock_price(self):
        """Test parsing stock price data"""
        parser = StockPriceParser()
        
        price_data = {
            "ticker": "AAPL",
            "date": "2025-11-12",
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 154.0,
            "volume": 1000000,
            "source": "yahoo_finance"
        }
        
        result = parser.parse(price_data, {})
        
        assert "content" in result
        assert "AAPL" in result["content"]
        assert "metrics" in result
        assert result["metrics"]["ticker"] == "AAPL"
        assert result["metrics"]["close_price"] == 154.0
        assert result["data_type"] == "stock_price"
    
    def test_parse_historical_prices(self):
        """Test parsing historical price data"""
        parser = StockPriceParser()
        
        prices = [
            {
                "ticker": "AAPL",
                "date": "2025-11-10",
                "close": 150.0,
                "volume": 1000000
            },
            {
                "ticker": "AAPL",
                "date": "2025-11-11",
                "close": 152.0,
                "volume": 1100000
            },
            {
                "ticker": "AAPL",
                "date": "2025-11-12",
                "close": 154.0,
                "volume": 1200000
            }
        ]
        
        result = parser.parse_historical(prices, {})
        
        assert "content" in result
        assert "metrics" in result
        assert result["metrics"]["ticker"] == "AAPL"
        assert result["metrics"]["data_points"] == 3
        assert result["data_type"] == "historical_prices"


class TestFinancialStatementsParser:
    """Test financial statements parser"""
    
    def test_parse_financials(self):
        """Test parsing financial statements"""
        parser = FinancialStatementsParser()
        
        financial_data = {
            "ticker": "AAPL",
            "source": "yahoo_finance",
            "income_statement": {
                "period_end": "2025-09-30",
                "total_revenue": 100000000000,
                "net_income": 25000000000
            },
            "balance_sheet": {
                "period_end": "2025-09-30",
                "total_assets": 500000000000,
                "total_liabilities": 300000000000,
                "stockholders_equity": 200000000000
            }
        }
        
        result = parser.parse(financial_data, {})
        
        assert "content" in result
        assert "AAPL" in result["content"]
        assert "metrics" in result
        assert "income_statement" in result["metrics"]
        assert "balance_sheet" in result["metrics"]
        assert result["data_type"] == "financial_statements"


class TestEarningsParser:
    """Test earnings parser"""
    
    def test_parse_earnings(self):
        """Test parsing earnings data"""
        parser = EarningsParser()
        
        earnings_data = {
            "ticker": "AAPL",
            "source": "yahoo_finance",
            "quarterly_earnings": [
                {
                    "date": "2025-09-30",
                    "revenue": 100000000000,
                    "earnings": 25000000000
                },
                {
                    "date": "2025-06-30",
                    "revenue": 95000000000,
                    "earnings": 23000000000
                }
            ],
            "metrics": {
                "trailing_eps": 6.50,
                "forward_eps": 7.00,
                "profit_margins": 0.25
            }
        }
        
        result = parser.parse(earnings_data, {})
        
        assert "content" in result
        assert "AAPL" in result["content"]
        assert "metrics" in result
        assert "quarterly_earnings" in result["metrics"]
        assert result["data_type"] == "earnings"


class TestCompanyInfoParser:
    """Test company info parser"""
    
    def test_parse_company_info(self):
        """Test parsing company information"""
        parser = CompanyInfoParser()
        
        company_data = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 3000000000000,
            "source": "yahoo_finance"
        }
        
        result = parser.parse(company_data, {})
        
        assert "content" in result
        assert "Apple Inc." in result["content"]
        assert "metrics" in result
        assert result["metrics"]["ticker"] == "AAPL"
        assert result["metrics"]["name"] == "Apple Inc."
        assert result["data_type"] == "company_info"


class TestFinancialDataConnector:
    """Test unified financial data connector"""
    
    @patch('nexus.ingestion.financial_connectors.YahooFinanceConnector')
    def test_get_stock_price_with_fallback(self, mock_yahoo_class):
        """Test stock price with fallback"""
        mock_yahoo = Mock()
        mock_yahoo.get_stock_price.return_value = {
            "ticker": "AAPL",
            "close": 154.0,
            "source": "yahoo_finance"
        }
        mock_yahoo_class.return_value = mock_yahoo
        
        connector = FinancialDataConnector()
        connector.yahoo = mock_yahoo
        
        result = connector.get_stock_price("AAPL")
        
        assert result["ticker"] == "AAPL"
        assert result["close"] == 154.0
        assert "error" not in result


@pytest.mark.integration
class TestFinancialIntegrationFlow:
    """Integration tests for financial data flow"""
    
    @patch('nexus.ingestion.financial_connectors.YahooFinanceConnector')
    @patch('nexus.storage.postgres.PostgresStore')
    @patch('nexus.storage.redis_bus.RedisEventBus')
    def test_stock_price_monitoring_flow(self, mock_bus, mock_store, mock_yahoo_class):
        """Test stock price monitoring flow"""
        mock_store_instance = Mock()
        mock_store_instance.fetch_all.return_value = [
            ("company-id-1", "AAPL", "Apple Inc.")
        ]
        mock_store_instance.insert_evidence.return_value = "evidence-id-1"
        mock_store.return_value = mock_store_instance
        
        mock_bus_instance = Mock()
        mock_bus.return_value = mock_bus_instance
        
        mock_yahoo = Mock()
        mock_yahoo.get_stock_price.return_value = {
            "ticker": "AAPL",
            "date": "2025-11-12",
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 154.0,
            "volume": 1000000,
            "source": "yahoo_finance"
        }
        mock_yahoo_class.return_value = mock_yahoo
        
        from nexus.monitoring.stock_prices_flow import monitor_stock_prices
        
        monitor_stock_prices()
        
        assert mock_store_instance.insert_evidence.called
        
        assert mock_bus_instance.publish.called
