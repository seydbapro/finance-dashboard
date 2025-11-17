from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import json
import numpy as np

API_KEY = "GYU2oxLWxz5XvJKHtrpBghiNSsCLxJUS" 
RISK_FREE_RATE = 0.04 # 4.0% pour le calcul du Ratio de Sharpe annuel
SHARPE_THRESHOLD = 1.0 # Seuil standard : Sharpe > 1.0 est considéré comme bon

def calculate_sharpe_ratio(ticker: str, api_key: str):
    """
    Récupère 5 ans de données historiques annuelles et calcule le Ratio de Sharpe.
    
    NOTE: FMP ne fournit pas toujours les rendements annuels bruts,
    nous allons donc utiliser les prix de clôture pour calculer les rendements.
    """
    
    # Récupérer les prix historiques (Date: 5 ans en arrière jusqu'à aujourd'hui)
    # NOTE: L'endpoint peut être coûteux ou limité en accès gratuit.
    historical_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?timeseries=5000&apikey={api_key}"
    
    try:
        data = requests.get(historical_url).json()
        prices = data.get('historical', [])
    except Exception:
        return {"error": "Échec de la récupération des données de prix historiques."}

    if not prices:
        return {"error": "Prix historiques non disponibles pour le Ratio de Sharpe."}

    # Créer une DataFrame (Pandas) pour faciliter les calculs des rendements
    # Bien que Pandas soit plus simple, nous utilisons la logique NumPy pour rester compatible
    # avec l'environnement Serverless minimal si Pandas n'est pas optimisé.

    # 1. Extraction et tri par date (la plus ancienne en premier)
    prices.sort(key=lambda x: x['date']) 
    
    # Utiliser les prix ajustés pour les rendements (pour tenir compte des dividendes/splits)
    adjusted_closes = np.array([item['adjClose'] for item in prices])
    
    # 2. Calcul des rendements quotidiens
    # Rendement = (Prix Aujourd'hui / Prix Hier) - 1
    daily_returns = (adjusted_closes[1:] / adjusted_closes[:-1]) - 1

    if len(daily_returns) < 252: # 252 jours de trading par an
        return {"error": "Moins d'un an de données. Ratio de Sharpe impossible à calculer."}

    # 3. Composante 1: Rendement Moyen Annuel (Rp)
    # Nous annualisons le rendement moyen quotidien
    average_daily_return = np.mean(daily_returns)
    annual_return_Rp = (1 + average_daily_return) ** 252 - 1

    # 4. Composante 2: Volatilité Annuelle (Sigma p)
    # Nous annualisons l'écart-type quotidien
    daily_volatility = np.std(daily_returns)
    annual_volatility_sigma_p = daily_volatility * np.sqrt(252)
    
    # 5. Calcul du Ratio de Sharpe
    excess_return = annual_return_Rp - RISK_FREE_RATE
    sharpe_ratio = excess_return / annual_volatility_sigma_p if annual_volatility_sigma_p > 0 else 0

    # 6. Scoring
    statut = "Vert" if sharpe_ratio >= SHARPE_THRESHOLD else "Rouge"

    return {
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sharpe_statut": statut,
        "rendement_annuel_pct": round(annual_return_Rp * 100, 2),
        "volatilite_annuelle_pct": round(annual_volatility_sigma_p * 100, 2),
        "regle": f"Ratio >= {SHARPE_THRESHOLD}"
    }

# --- Fonction Serverless de Vercel (Point d'entrée) ---

def handler(request: BaseHTTPRequestHandler):
    query = urlparse(request.url).query
    params = parse_qs(query)
    ticker = params.get('ticker', ['MSFT'])[0].upper()
    
    try:
        sharpe_result = calculate_sharpe_ratio(ticker, API_KEY)
        
        if "error" in sharpe_result:
            return json.dumps({"success": False, "error": sharpe_result["error"]}), 400
        
        return json.dumps({"success": True, "data": sharpe_result}), 200
    
    except Exception as e:
        return json.dumps({"success": False, "error": f"Erreur fatale dans le Ratio de Sharpe: {e}"}), 500
