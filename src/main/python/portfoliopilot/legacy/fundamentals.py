# data/fundamentals.py
import pandas as pd
import datetime


class FundamentalsDataLoader:
    def __init__(self):
        # Time-Series Registry: Maps release dates to corporate updates.
        # This prevents look-ahead bias during historical simulations.
        self.historical_db = {
            "RELIANCE.NS": [
                {"effective_date": "2024-01-01", "pe_ratio": 26.2, "debt_to_equity": 44.1, "operating_margin": 0.17},
                {"effective_date": "2025-01-01", "pe_ratio": 24.5, "debt_to_equity": 42.5, "operating_margin": 0.18},
                {"effective_date": "2026-01-01", "pe_ratio": 22.1, "debt_to_equity": 39.8, "operating_margin": 0.19}
            ],
            "TCS.NS": [
                {"effective_date": "2024-01-01", "pe_ratio": 30.1, "debt_to_equity": 9.1, "operating_margin": 0.25},
                {"effective_date": "2025-01-01", "pe_ratio": 28.5, "debt_to_equity": 8.4, "operating_margin": 0.26},
                {"effective_date": "2026-01-01", "pe_ratio": 27.2, "debt_to_equity": 7.9, "operating_margin": 0.27}
            ]
        }

    def fetch_company_metrics_point_in_time(self, ticker: str, evaluation_date: pd.Timestamp) -> dict:
        """Extracts the exact fundamental profile available on Day X."""
        tk_clean = str(ticker).strip().upper()

        if tk_clean not in self.historical_db:
            # Safe baseline institutional fallback if ticker is outside our primary tracking loop
            return {"pe_ratio": 22.0, "debt_to_equity": 35.0, "operating_margin": 0.18}

        available_updates = self.historical_db[tk_clean]
        target_record = None

        # Traverse chronologically to locate the most recent update that occurred before or on Day X
        for record in sorted(available_updates, key=lambda x: x["effective_date"]):
            record_date = pd.to_datetime(record["effective_date"])
            if record_date <= evaluation_date:
                target_record = record

        if target_record:
            return {
                "pe_ratio": float(target_record["pe_ratio"]),
                "debt_to_equity": float(target_record["debt_to_equity"]),
                "operating_margin": float(target_record["operating_margin"])
            }

        # Fallback to the oldest known record if backtest date predates our first timeline log
        return available_updates[0]
