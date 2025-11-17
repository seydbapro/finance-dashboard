from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import json

# Votre clé API FMP
API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 

def get_base_metrics(ticker: str, api_key: str):
    """
    Récupère les métriques de base, ratios de valorisation et prix en temps réel
    directement de FMP sans aucun calcul.
    """
    
    # Endpoint 1: Ratios de Valorisation (P/E, P/S, etc.)
    ratios_url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?limit=1&apikey={api_key}"
    
    # Endpoint 2: Prix en temps réel et Beta (pour l'affichage immédiat)
    quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={api_key}"

    try:
        ratios_data = requests.get(ratios_url).json()[0]
        quote_data = requests.get(quote_url).json()[0]
        
    except Exception:
        return {"error": f"Échec de la récupération des données de base pour {ticker}. Ticker invalide ou limites API atteintes."}
    
    # Extraction et structuration des données brutes
    metrics = {
        "price": quote_data.get('price', 0),
        "market_cap": quote_data.get('marketCap', 0),
        "volume": quote_data.get('volume', 0),
        "beta": quote_data.get('beta', 0),
        "pe_ratio": ratios_data['valuationRatios'].get('priceEarningsRatio', 'N/A'),
        "ps_ratio": ratios_data['valuationRatios'].get('priceToSalesRatio', 'N/A'),
        "debt_to_equity": ratios_data['financialStructureRatios'].get('debtEquityRatio', 'N/A'),
        "net_margin": ratios_data['profitabilityIndicator'].get('netProfitMargin', 'N/A')
    }
    
    return metrics

# --- Fonction Serverless de Vercel (Point d'entrée) ---

def handler(request: BaseHTTPRequestHandler):
    query = urlparse(request.url).query
    params = parse_qs(query)
    ticker = params.get('ticker', ['MSFT'])[0].upper()
    
    try:
        metrics_result = get_base_metrics(ticker, API_KEY)
        
        if "error" in metrics_result:
            return json.dumps({"success": False, "error": metrics_result["error"]}), 400
        
        return json.dumps({"success": True, "data": metrics_result}), 200
    
    except Exception as e:
        return json.dumps({"success": False, "error": f"Erreur fatale dans les métriques de base: {e}"}), 500
