"""Financial data parsers for stock prices, financials, and earnings"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class StockPriceParser:
    """Parse stock price data into evidence format"""
    
    def parse(self, price_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse stock price data
        
        Args:
            price_data: Raw price data from connector
            metadata: Additional metadata
        
        Returns:
            Parsed data in evidence format
        """
        if "error" in price_data:
            return {"error": price_data["error"]}
        
        ticker = price_data.get("ticker")
        date = price_data.get("date")
        
        content_parts = [
            f"Stock Price Data for {ticker}",
            f"Date: {date}",
            f"Open: ${price_data.get('open', 0):.2f}",
            f"High: ${price_data.get('high', 0):.2f}",
            f"Low: ${price_data.get('low', 0):.2f}",
            f"Close: ${price_data.get('close', 0):.2f}",
            f"Volume: {price_data.get('volume', 0):,}",
        ]
        
        if "change_percent" in price_data:
            content_parts.append(f"Change: {price_data['change_percent']}")
        
        content = "\n".join(content_parts)
        
        metrics = {
            "ticker": ticker,
            "date": date,
            "close_price": price_data.get("close"),
            "volume": price_data.get("volume"),
            "price_range": {
                "high": price_data.get("high"),
                "low": price_data.get("low")
            }
        }
        
        return {
            "content": content,
            "metrics": metrics,
            "source": price_data.get("source", "unknown"),
            "data_type": "stock_price",
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def parse_historical(self, prices: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse historical price data
        
        Args:
            prices: List of price data points
            metadata: Additional metadata
        
        Returns:
            Parsed historical data
        """
        if not prices or "error" in prices[0]:
            return {"error": prices[0].get("error", "No data") if prices else "No data"}
        
        ticker = prices[0].get("ticker")
        
        closes = [p["close"] for p in prices if "close" in p]
        volumes = [p["volume"] for p in prices if "volume" in p]
        
        if closes:
            avg_close = sum(closes) / len(closes)
            min_close = min(closes)
            max_close = max(closes)
            price_change = ((closes[-1] - closes[0]) / closes[0] * 100) if len(closes) > 1 else 0
        else:
            avg_close = min_close = max_close = price_change = 0
        
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        content_parts = [
            f"Historical Stock Price Data for {ticker}",
            f"Period: {prices[0]['date']} to {prices[-1]['date']}",
            f"Data Points: {len(prices)}",
            f"",
            f"Price Statistics:",
            f"  Average Close: ${avg_close:.2f}",
            f"  Min Close: ${min_close:.2f}",
            f"  Max Close: ${max_close:.2f}",
            f"  Price Change: {price_change:.2f}%",
            f"",
            f"Volume Statistics:",
            f"  Average Volume: {avg_volume:,.0f}",
        ]
        
        content = "\n".join(content_parts)
        
        metrics = {
            "ticker": ticker,
            "period_start": prices[0]["date"],
            "period_end": prices[-1]["date"],
            "data_points": len(prices),
            "avg_close": avg_close,
            "price_change_percent": price_change,
            "avg_volume": avg_volume,
            "prices": prices
        }
        
        return {
            "content": content,
            "metrics": metrics,
            "source": prices[0].get("source", "unknown"),
            "data_type": "historical_prices",
            "parsed_at": datetime.utcnow().isoformat()
        }


class FinancialStatementsParser:
    """Parse financial statements data"""
    
    def parse(self, financial_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse financial statements
        
        Args:
            financial_data: Raw financial data from connector
            metadata: Additional metadata
        
        Returns:
            Parsed financial data
        """
        if "error" in financial_data:
            return {"error": financial_data["error"]}
        
        ticker = financial_data.get("ticker")
        content_parts = [f"Financial Statements for {ticker}"]
        
        metrics = {
            "ticker": ticker,
            "fetched_at": financial_data.get("fetched_at")
        }
        
        if "income_statement" in financial_data:
            income = financial_data["income_statement"]
            content_parts.extend([
                "",
                f"Income Statement (Period: {income.get('period_end', 'N/A')})",
                f"  Total Revenue: ${self._format_number(income.get('total_revenue'))}",
                f"  Gross Profit: ${self._format_number(income.get('gross_profit'))}",
                f"  Operating Income: ${self._format_number(income.get('operating_income'))}",
                f"  Net Income: ${self._format_number(income.get('net_income'))}",
                f"  EBITDA: ${self._format_number(income.get('ebitda'))}",
            ])
            
            metrics["income_statement"] = income
            
            if income.get("total_revenue") and income.get("net_income"):
                net_margin = (income["net_income"] / income["total_revenue"]) * 100
                content_parts.append(f"  Net Margin: {net_margin:.2f}%")
                metrics["net_margin"] = net_margin
        
        if "balance_sheet" in financial_data:
            balance = financial_data["balance_sheet"]
            content_parts.extend([
                "",
                f"Balance Sheet (Period: {balance.get('period_end', 'N/A')})",
                f"  Total Assets: ${self._format_number(balance.get('total_assets'))}",
                f"  Total Liabilities: ${self._format_number(balance.get('total_liabilities'))}",
                f"  Stockholders Equity: ${self._format_number(balance.get('stockholders_equity'))}",
                f"  Cash and Equivalents: ${self._format_number(balance.get('cash_and_equivalents'))}",
            ])
            
            metrics["balance_sheet"] = balance
            
            if balance.get("total_liabilities") and balance.get("stockholders_equity"):
                debt_to_equity = balance["total_liabilities"] / balance["stockholders_equity"]
                content_parts.append(f"  Debt-to-Equity Ratio: {debt_to_equity:.2f}")
                metrics["debt_to_equity"] = debt_to_equity
        
        if "cash_flow" in financial_data:
            cf = financial_data["cash_flow"]
            content_parts.extend([
                "",
                f"Cash Flow Statement (Period: {cf.get('period_end', 'N/A')})",
                f"  Operating Cash Flow: ${self._format_number(cf.get('operating_cash_flow'))}",
                f"  Investing Cash Flow: ${self._format_number(cf.get('investing_cash_flow'))}",
                f"  Financing Cash Flow: ${self._format_number(cf.get('financing_cash_flow'))}",
                f"  Free Cash Flow: ${self._format_number(cf.get('free_cash_flow'))}",
            ])
            
            metrics["cash_flow"] = cf
        
        content = "\n".join(content_parts)
        
        return {
            "content": content,
            "metrics": metrics,
            "source": financial_data.get("source", "unknown"),
            "data_type": "financial_statements",
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _format_number(self, value: Optional[float]) -> str:
        """Format large numbers for display"""
        if value is None:
            return "N/A"
        
        if abs(value) >= 1e9:
            return f"{value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"{value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.2f}K"
        else:
            return f"{value:.2f}"


class EarningsParser:
    """Parse earnings data"""
    
    def parse(self, earnings_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse earnings data
        
        Args:
            earnings_data: Raw earnings data from connector
            metadata: Additional metadata
        
        Returns:
            Parsed earnings data
        """
        if "error" in earnings_data:
            return {"error": earnings_data["error"]}
        
        ticker = earnings_data.get("ticker")
        content_parts = [f"Earnings Data for {ticker}"]
        
        metrics = {
            "ticker": ticker,
            "fetched_at": earnings_data.get("fetched_at")
        }
        
        if "quarterly_earnings" in earnings_data:
            quarterly = earnings_data["quarterly_earnings"]
            if quarterly:
                content_parts.extend(["", "Quarterly Earnings:"])
                
                for q in quarterly[:4]:
                    date = q.get("date", "N/A")
                    revenue = q.get("revenue")
                    earnings = q.get("earnings")
                    
                    content_parts.append(f"  {date}:")
                    if revenue is not None:
                        content_parts.append(f"    Revenue: ${self._format_number(revenue)}")
                    if earnings is not None:
                        content_parts.append(f"    Earnings: ${self._format_number(earnings)}")
                
                metrics["quarterly_earnings"] = quarterly
                
                if len(quarterly) >= 2:
                    latest = quarterly[0]
                    previous = quarterly[1]
                    
                    if latest.get("revenue") and previous.get("revenue"):
                        revenue_growth = ((latest["revenue"] - previous["revenue"]) / previous["revenue"]) * 100
                        content_parts.append(f"  QoQ Revenue Growth: {revenue_growth:.2f}%")
                        metrics["qoq_revenue_growth"] = revenue_growth
                    
                    if latest.get("earnings") and previous.get("earnings"):
                        earnings_growth = ((latest["earnings"] - previous["earnings"]) / previous["earnings"]) * 100
                        content_parts.append(f"  QoQ Earnings Growth: {earnings_growth:.2f}%")
                        metrics["qoq_earnings_growth"] = earnings_growth
        
        if "annual_earnings" in earnings_data:
            annual = earnings_data["annual_earnings"]
            if annual:
                content_parts.extend(["", "Annual Earnings:"])
                
                for a in annual[-3:]:
                    year = a.get("year", "N/A")
                    revenue = a.get("revenue")
                    earnings = a.get("earnings")
                    
                    content_parts.append(f"  {year}:")
                    if revenue is not None:
                        content_parts.append(f"    Revenue: ${self._format_number(revenue)}")
                    if earnings is not None:
                        content_parts.append(f"    Earnings: ${self._format_number(earnings)}")
                
                metrics["annual_earnings"] = annual
        
        if "metrics" in earnings_data:
            metrics_data = earnings_data["metrics"]
            content_parts.extend(["", "Key Metrics:"])
            
            if metrics_data.get("trailing_eps"):
                content_parts.append(f"  Trailing EPS: ${metrics_data['trailing_eps']:.2f}")
            if metrics_data.get("forward_eps"):
                content_parts.append(f"  Forward EPS: ${metrics_data['forward_eps']:.2f}")
            if metrics_data.get("trailing_pe"):
                content_parts.append(f"  Trailing P/E: {metrics_data['trailing_pe']:.2f}")
            if metrics_data.get("profit_margins"):
                content_parts.append(f"  Profit Margin: {metrics_data['profit_margins']*100:.2f}%")
            if metrics_data.get("revenue_growth"):
                content_parts.append(f"  Revenue Growth: {metrics_data['revenue_growth']*100:.2f}%")
            if metrics_data.get("earnings_growth"):
                content_parts.append(f"  Earnings Growth: {metrics_data['earnings_growth']*100:.2f}%")
            
            metrics["key_metrics"] = metrics_data
        
        content = "\n".join(content_parts)
        
        return {
            "content": content,
            "metrics": metrics,
            "source": earnings_data.get("source", "unknown"),
            "data_type": "earnings",
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _format_number(self, value: Optional[float]) -> str:
        """Format large numbers for display"""
        if value is None:
            return "N/A"
        
        if abs(value) >= 1e9:
            return f"{value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"{value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.2f}K"
        else:
            return f"{value:.2f}"


class CompanyInfoParser:
    """Parse company information"""
    
    def parse(self, company_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse company information
        
        Args:
            company_data: Raw company data from connector
            metadata: Additional metadata
        
        Returns:
            Parsed company data
        """
        if "error" in company_data:
            return {"error": company_data["error"]}
        
        ticker = company_data.get("ticker")
        name = company_data.get("name", ticker)
        
        content_parts = [
            f"Company Information: {name} ({ticker})",
            ""
        ]
        
        if company_data.get("sector"):
            content_parts.append(f"Sector: {company_data['sector']}")
        
        if company_data.get("industry"):
            content_parts.append(f"Industry: {company_data['industry']}")
        
        if company_data.get("market_cap"):
            market_cap = company_data["market_cap"]
            if market_cap >= 1e9:
                content_parts.append(f"Market Cap: ${market_cap/1e9:.2f}B")
            else:
                content_parts.append(f"Market Cap: ${market_cap/1e6:.2f}M")
        
        if company_data.get("employees"):
            content_parts.append(f"Employees: {company_data['employees']:,}")
        
        if company_data.get("website"):
            content_parts.append(f"Website: {company_data['website']}")
        
        if company_data.get("description"):
            content_parts.extend(["", "Description:", company_data["description"][:500]])
        
        if company_data.get("pe_ratio"):
            content_parts.append(f"P/E Ratio: {company_data['pe_ratio']:.2f}")
        
        if company_data.get("eps"):
            content_parts.append(f"EPS: ${company_data['eps']:.2f}")
        
        if company_data.get("profit_margin"):
            content_parts.append(f"Profit Margin: {company_data['profit_margin']*100:.2f}%")
        
        content = "\n".join(content_parts)
        
        metrics = {
            "ticker": ticker,
            "name": name,
            "sector": company_data.get("sector"),
            "industry": company_data.get("industry"),
            "market_cap": company_data.get("market_cap"),
            "employees": company_data.get("employees")
        }
        
        return {
            "content": content,
            "metrics": metrics,
            "source": company_data.get("source", "unknown"),
            "data_type": "company_info",
            "parsed_at": datetime.utcnow().isoformat()
        }
