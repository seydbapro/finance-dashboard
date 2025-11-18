from urllib.parse import urlparse, parse_qs
import requests
import json
import numpy as np

API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 

# --- HYPOTHÈSES DU MODÈLE ---
TERMINAL_GROWTH_RATE = 0.025 # 2.5% de croissance perpétuelle
PROJECTION_YEARS = 5

def calculate_dcf(ticker: str, wacc: float, growth_rate: float, api_key: str):
    """
    Récupère les données FCF et calcule la Juste Valeur (Fair Value) par action.
    """
    cf_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit=1&apikey={api_key}"
    metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={api_key}"

    try:
        cf_data = requests.get(cf_url).json()[0]
        metrics = requests.get(metrics_url).json()[0]
    except Exception:
        return {"error": "Échec de la récupération des données FCF pour le DCF."}

    fcf_base = cf_data.get('freeCashFlow', 0)
    shares_outstanding = metrics.get('sharesOutstanding', 1)
    net_debt = metrics.get('netDebt', 0)

    if fcf_base == 0 or shares_outstanding == 0:
        return {"error": "FCF ou nombre d'actions non disponible pour le DCF."}
    
    # Projection et Actualisation des Flux (Années 1 à 5)
    present_value_fcf = 0
    fcf_an_precedent = fcf_base

    for year in range(1, PROJECTION_YEARS + 1):
        fcf_projet = fcf_an_precedent * (1 + growth_rate)
        pv = fcf_projet / ((1 + wacc) ** year)
        present_value_fcf += pv
        fcf_an_precedent = fcf_projet

    # Calcul de la Valeur Terminale (TV)
    fcf_an_6 = fcf_an_precedent * (1 + TERMINAL_GROWTH_RATE)
    
    if wacc <= TERMINAL_GROWTH_RATE: 
         return {"error": "WACC <= taux de croissance perpétuelle. DCF non valide."}
         
    terminal_value = fcf_an_6 / (wacc - TERMINAL_GROWTH_RATE)
    present_value_tv = terminal_value / ((1 + wacc) ** PROJECTION_YEARS)

    # Calcul du Prix Cible
    enterprise_value = present_value_fcf + present_value_tv
    equity_value = enterprise_value - net_debt
    fair_value_per_share = equity_value / shares_outstanding

    return {
        "prix_cible_dcf": round(fair_value_per_share, 2),
        "wacc": round(wacc, 4),
        "croissance_fcf_pct": round(growth_rate * 100, 2),
        "fcf_base": fcf_base
    }

# --- Fonction Serverless de Vercel (Point d'entrée corrigé) ---
def handler(request):
    """
    Retourne un dictionnaire qui est automatiquement converti en JSON par Vercel.
    """
    # Lecture des paramètres
    try:
        ticker = request.query.get('ticker', 'MSFT').upper()
        wacc = float(request.query.get('wacc', 0.0915))
        growth_rate = float(request.query.get('growth', 0.10))
    except:
        query = urlparse(request.url).query
        params = parse_qs(query)
        ticker = params.get('ticker', ['MSFT'])[0].upper()
        wacc = float(params.get('wacc', [0.0915])[0])
        growth_rate = float(params.get('growth', [0.10])[0])
    
    try:
        result = calculate_dcf(ticker, wacc, growth_rate, API_KEY)
        
        if "error" in result:
            return {"success": False, "error": result["error"]}, 400
            
        return {"success": True, "data": result}
    
    except Exception as e:
        return {"success": False, "error": f"Erreur fatale interne: {e}"}, 500