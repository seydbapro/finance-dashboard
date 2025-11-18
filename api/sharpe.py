from urllib.parse import urlparse, parse_qs
import requests
import json
import numpy as np

# Votre clé API FMP
API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 
RISK_FREE_RATE = 0.04 
SHARPE_THRESHOLD = 1.0 

def calculate_sharpe_ratio(ticker: str, api_key: str):
    """
    MIGRÉ : Utilise le nouvel endpoint FMP *-full* pour l'historique des prix.
    """
    # NOUVEL ENDPOINT FMP
    # Note: On utilise toujours 'historical-price-full' car il n'y a pas d'alternative simple '-full' pour les prix
    historical_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?timeseries=5000&apikey={api_key}"
    
    try:
        data = requests.get(historical_url).json()
        prices = data.get('historical', [])
    except Exception:
        return {"error": "Échec de la récupération des données de prix historiques."}

    if not prices or "Error Message" in data:
        return {"error": "Prix historiques non disponibles pour le Ratio de Sharpe (limite API ?)."}

    prices.sort(key=lambda x: x['date']) 
    adjusted_closes = np.array([item['adjClose'] for item in prices])
    
    daily_returns = (adjusted_closes[1:] / adjusted_closes[:-1]) - 1

    if len(daily_returns) < 252:
        return {"error": "Moins d'un an de données. Ratio de Sharpe impossible à calculer."}

    average_daily_return = np.mean(daily_returns)
    annual_return_Rp = (1 + average_daily_return) ** 252 - 1

    daily_volatility = np.std(daily_returns)
    annual_volatility_sigma_p = daily_volatility * np.sqrt(252)
    
    excess_return = annual_return_Rp - RISK_FREE_RATE
    sharpe_ratio = excess_return / annual_volatility_sigma_p if annual_volatility_sigma_p > 0 else 0

    statut = "Vert" if sharpe_ratio >= SHARPE_THRESHOLD else "Rouge"

    return {
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sharpe_statut": statut,
        "regle": f"Ratio >= {SHARPE_THRESHOLD}"
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
        result = calculate_sharpe_ratio(ticker, API_KEY)
        
        if "error" in result:
            return {"success": False, "error": result["error"]}, 400
            
        return {"success": True, "data": result}
    
    except Exception as e:
        return {"success": False, "error": f"Erreur fatale interne: {e}"}, 500