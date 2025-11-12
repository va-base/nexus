"""Financial data source connectors"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from enum import Enum


class DataSource(Enum):
    """Available financial data sources"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    FINANCIAL_MODELING_PREP = "fmp"


class YahooFinanceConnector:
    """
    Yahoo Finance connector using yfinance library
    Free, no API key required, good for stock prices and basic financials
    """
    
    def __init__(self):
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            raise ImportError("yfinance library not installed. Install with: pip install yfinance")
    
    def get_stock_price(self, ticker: str, period: str = "1d") -> Dict[str, Any]:
        """
        Get stock price data
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            Dict with price data
        """
        try:
            stock = self.yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return {"error": f"No data found for ticker {ticker}"}
            
            latest = hist.iloc[-1]
            
            return {
                "ticker": ticker,
                "date": hist.index[-1].strftime("%Y-%m-%d"),
                "open": float(latest['Open']),
                "high": float(latest['High']),
                "low": float(latest['Low']),
                "close": float(latest['Close']),
                "volume": int(latest['Volume']),
                "source": "yahoo_finance",
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_historical_prices(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get historical stock prices
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of price data dicts
        """
        try:
            stock = self.yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return []
            
            prices = []
            for date, row in hist.iterrows():
                prices.append({
                    "ticker": ticker,
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']),
                    "source": "yahoo_finance"
                })
            
            return prices
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_financials(self, ticker: str) -> Dict[str, Any]:
        """
        Get financial statements (income statement, balance sheet, cash flow)
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dict with financial data
        """
        try:
            stock = self.yf.Ticker(ticker)
            
            income_stmt = stock.quarterly_income_stmt
            balance_sheet = stock.quarterly_balance_sheet
            cash_flow = stock.quarterly_cashflow
            
            result = {
                "ticker": ticker,
                "source": "yahoo_finance",
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            if not income_stmt.empty:
                latest_income = income_stmt.iloc[:, 0]
                result["income_statement"] = {
                    "period_end": income_stmt.columns[0].strftime("%Y-%m-%d"),
                    "total_revenue": float(latest_income.get('Total Revenue', 0)) if 'Total Revenue' in latest_income.index else None,
                    "gross_profit": float(latest_income.get('Gross Profit', 0)) if 'Gross Profit' in latest_income.index else None,
                    "operating_income": float(latest_income.get('Operating Income', 0)) if 'Operating Income' in latest_income.index else None,
                    "net_income": float(latest_income.get('Net Income', 0)) if 'Net Income' in latest_income.index else None,
                    "ebitda": float(latest_income.get('EBITDA', 0)) if 'EBITDA' in latest_income.index else None,
                }
            
            if not balance_sheet.empty:
                latest_balance = balance_sheet.iloc[:, 0]
                result["balance_sheet"] = {
                    "period_end": balance_sheet.columns[0].strftime("%Y-%m-%d"),
                    "total_assets": float(latest_balance.get('Total Assets', 0)) if 'Total Assets' in latest_balance.index else None,
                    "total_liabilities": float(latest_balance.get('Total Liabilities Net Minority Interest', 0)) if 'Total Liabilities Net Minority Interest' in latest_balance.index else None,
                    "stockholders_equity": float(latest_balance.get('Stockholders Equity', 0)) if 'Stockholders Equity' in latest_balance.index else None,
                    "cash_and_equivalents": float(latest_balance.get('Cash And Cash Equivalents', 0)) if 'Cash And Cash Equivalents' in latest_balance.index else None,
                }
            
            if not cash_flow.empty:
                latest_cf = cash_flow.iloc[:, 0]
                result["cash_flow"] = {
                    "period_end": cash_flow.columns[0].strftime("%Y-%m-%d"),
                    "operating_cash_flow": float(latest_cf.get('Operating Cash Flow', 0)) if 'Operating Cash Flow' in latest_cf.index else None,
                    "investing_cash_flow": float(latest_cf.get('Investing Cash Flow', 0)) if 'Investing Cash Flow' in latest_cf.index else None,
                    "financing_cash_flow": float(latest_cf.get('Financing Cash Flow', 0)) if 'Financing Cash Flow' in latest_cf.index else None,
                    "free_cash_flow": float(latest_cf.get('Free Cash Flow', 0)) if 'Free Cash Flow' in latest_cf.index else None,
                }
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def get_earnings(self, ticker: str) -> Dict[str, Any]:
        """
        Get earnings data
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dict with earnings data
        """
        try:
            stock = self.yf.Ticker(ticker)
            
            earnings = stock.earnings
            quarterly_earnings = stock.quarterly_earnings
            
            result = {
                "ticker": ticker,
                "source": "yahoo_finance",
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            if earnings is not None and not earnings.empty:
                result["annual_earnings"] = []
                for year, row in earnings.iterrows():
                    result["annual_earnings"].append({
                        "year": int(year),
                        "revenue": float(row['Revenue']) if 'Revenue' in row.index else None,
                        "earnings": float(row['Earnings']) if 'Earnings' in row.index else None,
                    })
            
            if quarterly_earnings is not None and not quarterly_earnings.empty:
                result["quarterly_earnings"] = []
                for date, row in quarterly_earnings.iterrows():
                    result["quarterly_earnings"].append({
                        "date": date.strftime("%Y-%m-%d"),
                        "revenue": float(row['Revenue']) if 'Revenue' in row.index else None,
                        "earnings": float(row['Earnings']) if 'Earnings' in row.index else None,
                    })
            
            info = stock.info
            if info:
                result["metrics"] = {
                    "trailing_eps": info.get("trailingEps"),
                    "forward_eps": info.get("forwardEps"),
                    "trailing_pe": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "profit_margins": info.get("profitMargins"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                }
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get company information
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dict with company info
        """
        try:
            stock = self.yf.Ticker(ticker)
            info = stock.info
            
            return {
                "ticker": ticker,
                "name": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "employees": info.get("fullTimeEmployees"),
                "description": info.get("longBusinessSummary"),
                "website": info.get("website"),
                "source": "yahoo_finance",
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}


class AlphaVantageConnector:
    """
    Alpha Vantage connector
    Free tier: 25 requests per day, 5 requests per minute
    Requires API key from https://www.alphavantage.co/support/#api-key
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key required. Set ALPHA_VANTAGE_API_KEY env var.")
        self.client = httpx.Client(timeout=30.0)
    
    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make API request"""
        params["apikey"] = self.api_key
        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """Get latest stock price"""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker
        }
        
        data = self._make_request(params)
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "ticker": ticker,
                "date": quote.get("07. latest trading day"),
                "open": float(quote.get("02. open", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "close": float(quote.get("05. price", 0)),
                "volume": int(quote.get("06. volume", 0)),
                "change_percent": quote.get("10. change percent"),
                "source": "alpha_vantage",
                "fetched_at": datetime.utcnow().isoformat()
            }
        
        return data
    
    def get_historical_prices(self, ticker: str, outputsize: str = "compact") -> List[Dict[str, Any]]:
        """
        Get historical daily prices
        
        Args:
            ticker: Stock ticker
            outputsize: 'compact' (100 days) or 'full' (20+ years)
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": outputsize
        }
        
        data = self._make_request(params)
        
        if "Time Series (Daily)" in data:
            prices = []
            for date, values in data["Time Series (Daily)"].items():
                prices.append({
                    "ticker": ticker,
                    "date": date,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"]),
                    "source": "alpha_vantage"
                })
            return prices
        
        return [data]
    
    def get_company_overview(self, ticker: str) -> Dict[str, Any]:
        """Get company overview and fundamentals"""
        params = {
            "function": "OVERVIEW",
            "symbol": ticker
        }
        
        data = self._make_request(params)
        
        if "Symbol" in data:
            return {
                "ticker": data.get("Symbol"),
                "name": data.get("Name"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "market_cap": int(data.get("MarketCapitalization", 0)),
                "description": data.get("Description"),
                "pe_ratio": float(data.get("PERatio", 0)) if data.get("PERatio") != "None" else None,
                "eps": float(data.get("EPS", 0)) if data.get("EPS") != "None" else None,
                "revenue_ttm": int(data.get("RevenueTTM", 0)),
                "profit_margin": float(data.get("ProfitMargin", 0)) if data.get("ProfitMargin") != "None" else None,
                "source": "alpha_vantage",
                "fetched_at": datetime.utcnow().isoformat()
            }
        
        return data
    
    def close(self):
        """Close HTTP client"""
        self.client.close()


class FinancialDataConnector:
    """
    Unified financial data connector that tries multiple sources
    Falls back to alternatives if primary source fails
    """
    
    def __init__(self, primary_source: DataSource = DataSource.YAHOO_FINANCE):
        self.primary_source = primary_source
        self.yahoo = None
        self.alpha_vantage = None
        
        try:
            self.yahoo = YahooFinanceConnector()
        except ImportError:
            pass
        
        alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if alpha_key:
            try:
                self.alpha_vantage = AlphaVantageConnector(alpha_key)
            except Exception:
                pass
    
    def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """Get stock price with fallback"""
        if self.primary_source == DataSource.YAHOO_FINANCE and self.yahoo:
            result = self.yahoo.get_stock_price(ticker)
            if "error" not in result:
                return result
        
        if self.alpha_vantage:
            return self.alpha_vantage.get_stock_price(ticker)
        
        return {"error": "No available data sources"}
    
    def get_historical_prices(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get historical prices with fallback"""
        if self.yahoo:
            result = self.yahoo.get_historical_prices(ticker, start_date, end_date)
            if result and "error" not in result[0]:
                return result
        
        if self.alpha_vantage:
            return self.alpha_vantage.get_historical_prices(ticker)
        
        return [{"error": "No available data sources"}]
    
    def get_financials(self, ticker: str) -> Dict[str, Any]:
        """Get financial statements"""
        if self.yahoo:
            return self.yahoo.get_financials(ticker)
        
        return {"error": "No available data sources"}
    
    def get_earnings(self, ticker: str) -> Dict[str, Any]:
        """Get earnings data"""
        if self.yahoo:
            return self.yahoo.get_earnings(ticker)
        
        return {"error": "No available data sources"}
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """Get company information with fallback"""
        if self.yahoo:
            result = self.yahoo.get_company_info(ticker)
            if "error" not in result:
                return result
        
        if self.alpha_vantage:
            return self.alpha_vantage.get_company_overview(ticker)
        
        return {"error": "No available data sources"}
    
    def close(self):
        """Close all connections"""
        if self.alpha_vantage:
            self.alpha_vantage.close()
