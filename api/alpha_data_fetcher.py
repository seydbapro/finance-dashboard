from urllib.parse import urlparse, parse_qs
import requests
import json

# Clé API Alpha Vantage fournie par l'utilisateur
ALPHA_KEY = "WSGMIY9CBVGYM3C5" 

def get_alpha_metrics(ticker: str, alpha_key: str):
    """
    Récupère les métriques de base et la valorisation de Alpha Vantage.
    Utilise l'endpoint OVERVIEW pour obtenir les données fondamentales.
    """
    
    # URL de l'API Alpha Vantage pour les données fondamentales d'une entreprise
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={alpha_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Vérification des messages d'erreur courants d'Alpha Vantage
        if not data or data.get('Error Message') or not data.get('Symbol') or data == {}:
             # Capture les messages d'erreur d'API si la clé est invalide ou le taux limite est dépassé
             error_note = data.get('Note', 'Données non disponibles ou limites API atteintes.')
             return {"error": f"Ticker {ticker} invalide ou clé API Alpha Vantage bloquée. ({error_note})"}

        # Fonction utilitaire pour convertir les valeurs en chaînes de caractères de l'API en nombres flottants
        def safe_float(value):
            if isinstance(value, str):
                if value.lower() in ('none', 'n/a', ''):
                    return 0.0
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            return float(value) if value is not None else 0.0

        # Extraction et mise en forme des métriques clés
        return {
            "market_cap": safe_float(data.get('MarketCapitalization', 0)),
            "eps_ttm": data.get('DilutedEPSTTM', 'N/A'),
            "net_debt": safe_float(data.get('TotalDebt', 0)) - safe_float(data.get('CashAndCashEquivalents', 0)),
            "pe_ratio": data.get('PERatio', 'N/A'),
            "shares_outstanding": safe_float(data.get('SharesOutstanding', 1)),
            "beta": safe_float(data.get('Beta', 1.0)),
        }
        
    except Exception as e:
        return {"error": f"Erreur lors de l'extraction des données: {e}"}


# --- Fonction Serverless de Vercel ---
def handler(request):
    """
    Point d'entrée pour la fonction Vercel Serverless.
    """
    try:
        ticker = request.query.get('ticker', 'MSFT').upper()
    except:
        query = urlparse(request.url).query
        params = parse_qs(query)
        ticker = params.get('ticker', ['MSFT'])[0].upper()
    
    try:
        result = get_alpha_metrics(ticker, ALPHA_KEY)
        
        if "error" in result:
            return {"success": False, "error": result["error"]}, 400
            
        return {"success": True, "data": result}
    
    except Exception as e:
        return {"success": False, "error": f"Erreur fatale interne: {e}"}, 500