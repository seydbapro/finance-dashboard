from urllib.parse import urlparse, parse_qs
import requests
import json
import numpy as np

# Votre clé API FMP
API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 
ROCE_THRESHOLD = 0.15 

def calculate_roce(ticker: str, api_key: str):
    """
    MIGRÉ : Utilise les nouveaux endpoints FMP *-full* pour les états financiers.
    """
    # NOUVEAUX ENDPOINTS FMP
    balance_sheet_url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement-full/{ticker}?limit=5&apikey={api_key}"
    income_statement_url = f"https://financialmodelingprep.com/api/v3/income-statement-full/{ticker}?limit=5&apikey={api_key}"

    try:
        balance_data = requests.get(balance_sheet_url).json()
        income_data = requests.get(income_statement_url).json()
    except Exception as e:
        return {"error": f"Erreur de communication avec FMP: {e}"}

    roce_list = []
    
    # Vérification des données FMP
    if not balance_data or not income_data or isinstance(balance_data, dict) or len(balance_data) != len(income_data):
         return {"error": "Données fondamentales incomplètes pour le ROCE. Vérifiez l'accès API."}

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

# --- Fonction Serverless de Vercel ---
def handler(request):
    """
    Retourne un dictionnaire qui est automatiquement converti en JSON par Vercel.
    """
    # Lecture des paramètres
    try:
        ticker = request.query.get('ticker', 'MSFT').upper()
    except:
        query = urlparse(request.url).query
        params = parse_qs(query)
        ticker = params.get('ticker', ['MSFT'])[0].upper()
    
    try:
        result = calculate_roce(ticker, API_KEY)
        
        if "error" in result:
            return {"success": False, "error": result["error"]}, 400
            
        return {"success": True, "data": result}
    
    except Exception as e:
        return {"success": False, "error": f"Erreur fatale interne: {e}"}, 500