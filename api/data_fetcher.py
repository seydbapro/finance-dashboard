from urllib.parse import urlparse, parse_qs
import requests
import json
import numpy as np

# NOTE: Cette clé est l'ancienne clé bloquée.
API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 

def get_all_data(ticker: str, api_key: str):
    """
    Récupère toutes les métriques et ratios de FMP en un seul appel (Key Metrics Full).
    Ceci utilise l'ancien endpoint, susceptible de renvoyer une erreur HTML.
    """
    
    # ANCIEN ENDPOINT FMP
    # Remplacez par 'key-metrics' au lieu de 'key-metrics-full'
    metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit=1&apikey={api_key}"
    
    try:
        data = requests.get(metrics_url).json()
        
        if not data or isinstance(data, dict) and data.get("Error Message"):
             return {"error": f"API FMP bloquée ou Ticker {ticker} non trouvé. Vérifiez votre clé."}

        # Nous extrayons le premier élément de la liste
        metrics = data[0]

        # Retourne les métriques brutes
        return {
            "market_cap": metrics.get('marketCap', 0),
            "eps_ttm": metrics.get('epsTTM', 'N/A'),
            "shares_outstanding": metrics.get('sharesOutstanding', 0),
            "net_debt": metrics.get('netDebt', 0),
            "beta": metrics.get('beta', 0),
            "pe_ratio": metrics.get('peRatio', 'N/A'),
            "net_income_to_common": metrics.get('netIncomeToCommon', 0),
            "total_assets": metrics.get('totalAssets', 0),
        }
        
    except Exception as e:
        return {"error": f"Erreur lors de l'extraction des données: {e}"}

# --- Fonction Serverless de Vercel (Utilise le retour natif) ---
def handler(request):
    try:
        ticker = request.query.get('ticker', 'MSFT').upper()
    except:
        query = urlparse(request.url).query
        params = parse_qs(query)
        ticker = params.get('ticker', ['MSFT'])[0].upper()
    
    try:
        result = get_all_data(ticker, API_KEY)
        
        if "error" in result:
            return {"success": False, "error": result["error"]}, 400
            
        return {"success": True, "data": result}
    
    except Exception as e:
        return {"success": False, "error": f"Erreur fatale interne: {e}"}, 500
