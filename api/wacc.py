from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import json
import numpy as np

# Votre clé API FMP
API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 
RISK_FREE_RATE = 0.040        # Taux sans risque (4.0%)
MARKET_RISK_PREMIUM = 0.060   # Prime de risque du marché (6.0%)

# Structure de la réponse pour Vercel
class VercelResponse:
    def __init__(self, data, status=200):
        self.headers = {'Content-Type': 'application/json'}
        self.status = status
        self.data = json.dumps(data)

def calculate_wacc(ticker: str, api_key: str):
    """
    Récupère les données FMP et calcule le Coût Moyen Pondéré du Capital (WACC).
    """
    metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={api_key}"
    income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=1&apikey={api_key}"
    balance_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?limit=1&apikey={api_key}"

    try:
        metrics = requests.get(metrics_url).json()[0]
        income = requests.get(income_url).json()[0]
        balance = requests.get(balance_url).json()[0]
    except Exception:
        return {"error": "Échec de la récupération des données financières FMP."}

    market_cap_E = metrics.get('marketCap', 0)
    total_debt_D = balance.get('totalDebt', 0)
    V = market_cap_E + total_debt_D 

    beta = metrics.get('beta', 1.0)
    cost_of_equity_Re = RISK_FREE_RATE + beta * MARKET_RISK_PREMIUM

    interest_expense = income.get('interestExpense', 0)
    income_tax_expense = income.get('incomeTaxExpense', 0)
    ebit = income.get('ebit', 1)
    
    cost_of_debt_Rd = interest_expense / total_debt_D if total_debt_D > 0 else 0.05
    effective_tax_rate_T = income_tax_expense / ebit if ebit > 0 else 0.25
    
    equity_term = (market_cap_E / V) * cost_of_equity_Re if V > 0 else 0
    debt_term = (total_debt_D / V) * cost_of_debt_Rd * (1 - effective_tax_rate_T) if V > 0 else 0
    
    wacc = equity_term + debt_term

    return {
        "wacc": wacc, # Important : retourne la valeur décimale pour le DCF
        "wacc_pct": round(wacc * 100, 2),
        "beta": round(beta, 2),
        "cost_of_equity_pct": round(cost_of_equity_Re * 100, 2),
    }

# --- Fonction Serverless de Vercel (Point d'entrée corrigé) ---
def handler(request: BaseHTTPRequestHandler):
    ticker = request.query.get('ticker', 'MSFT').upper()
    
    try:
        result = calculate_wacc(ticker, API_KEY)
        
        if "error" in result:
            return VercelResponse({"success": False, "error": result["error"]}, status=400)
            
        return VercelResponse({"success": True, "data": result})
    
    except Exception as e:
        return VercelResponse({"success": False, "error": f"Erreur fatale interne: {e}"}, status=500)