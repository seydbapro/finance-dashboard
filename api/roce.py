# Fichier : /api/roce.py
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import json
import numpy as np

API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 
ROCE_THRESHOLD = 0.15 # Seuil de 15% pour le scoring

def calculate_roce(ticker: str, api_key: str):
    """
    Récupère les données FMP et calcule le ROCE moyen sur les 5 dernières années.
    """
    balance_sheet_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?limit=5&apikey={api_key}"
    income_statement_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=5&apikey={api_key}"

    try:
        balance_data = requests.get(balance_sheet_url).json()
        income_data = requests.get(income_statement_url).json()
    except Exception as e:
        return {"error": f"Erreur de communication avec FMP: {e}"}

    roce_list = []
    
    if not balance_data or not income_data or len(balance_data) != len(income_data):
         return {"error": "Données incomplètes ou non synchronisées pour le calcul du ROCE."}

    for bs, inc in zip(balance_data, income_data):
        try:
            ebit = inc.get('ebit', 0)
            tax_expense = inc.get('incomeTaxExpense', 0)
            total_assets = bs.get('totalAssets', 0)
            current_liabilities = bs.get('currentLiabilities', 0)

            capital_employed = total_assets - current_liabilities
            effective_tax_rate = tax_expense / ebit if ebit > 0 and tax_expense >= 0 else 0.25
            nopat = ebit * (1 - effective_tax_rate)
            roce = nopat / capital_employed if capital_employed > 0 else 0
            roce_list.append(roce)
        except Exception:
            continue 

    if not roce_list:
        return {"error": "Aucune donnée de ROCE valide trouvée."}
        
    roce_moyen_5_ans = np.mean(roce_list)
    statut = "Vert" if roce_moyen_5_ans >= ROCE_THRESHOLD else "Rouge"

    return {
        "roce_moyen_pct": round(roce_moyen_5_ans * 100, 2),
        "roce_statut": statut,
        "roce_regle": f"Moyenne sur 5 ans >= {ROCE_THRESHOLD * 100}%"
    }

def handler(request: BaseHTTPRequestHandler):
    query = urlparse(request.url).query
    params = parse_qs(query)
    ticker = params.get('ticker', ['MSFT'])[0].upper()
    
    roce_result = calculate_roce(ticker, API_KEY)
    
    if "error" in roce_result:
        return json.dumps(roce_result), 400
        
    return json.dumps({"success": True, "data": roce_result}), 200