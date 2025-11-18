import React, { useState } from 'react';
import './styles.css'; 

function App() {
  const [ticker, setTicker] = useState('MSFT');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  
  // L'URL de base pour appeler la fonction Python data_fetcher
  const BASE_URL = '/api'; 

  const fetchData = async () => {
    if (!ticker) return;

    setLoading(true);
    setData(null);

    try {
      // --- APPEL UNIQUE pour récupérer TOUTES les métriques de base (data_fetcher.py) ---
      const metricsRes = await fetch(`${BASE_URL}/data_fetcher?ticker=${ticker}`);
      const metricsJson = await metricsRes.json();
      
      if (!metricsJson.success) {
        throw new Error(metricsJson.error || 'Erreur lors de la récupération des données.');
      }

      const metrics = metricsJson.data;

      // Logique d'affichage simple du statut Bêta (Règle: Beta > 1.0 = Rouge)
      const betaStatus = metrics.beta > 1.0 ? 'Rouge' : 'Vert';

      setData({
        ticker,
        metrics,
        betaStatus,
        error: null
      });

    } catch (error) {
      setData({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>💰 Tableau de Bord FMP (Données Brutes)</h1>
      
      {/* ----------------- Composant de Recherche ----------------- */}
      <div className="search-bar">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Entrez un Ticker (ex: MSFT)"
        />
        <button onClick={fetchData} disabled={loading}>
          {loading ? 'Connexion FMP...' : 'Analyser le Ticker'}
        </button>
      </div>

      {/* Affichage des Erreurs */}
      {data && data.error && <p className="error-message">Erreur : {data.error}</p>}

      {/* ----------------- AFFICHAGE DES RÉSULTATS ----------------- */}
      {data && !data.error && (
        <div className="results">
          <h2>Résultats Bruts pour {data.ticker}</h2>

          <div className="grid-layout" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              
              {/* Carte 1 : VALEUR (P/E) */}
              <div className="kpi-card bg-green">
                <h3>Ratio P/E Brut</h3>
                <p className="kpi-value">{data.metrics.pe_ratio}</p>
                <small>Donnée brute de FMP</small>
              </div>

              {/* Carte 2 : VOLATILITÉ (Bêta) */}
              <div className={`kpi-card ${data.betaStatus === 'Vert' ? 'bg-green' : 'bg-red'}`}>
                <h3>Bêta Brut</h3>
                <p className="kpi-value">{data.metrics.beta}</p>
                <small>Volatilité par rapport au marché</small>
              </div>

              {/* Carte 3 : CAP BOURSIERE (Market Cap) */}
              <div className="kpi-card bg-green">
                <h3>Capitalisation Boursière</h3>
                <p className="kpi-value">${(data.metrics.market_cap / 1e9).toFixed(2)} Mds</p>
                <small>Donnée financière brute</small>
              </div>
          </div>
          
          <hr/>
          
          <div className="dcf-panel">
            <h3>Métriques Détaillées</h3>
            <p>EPS TTM : <strong>${data.metrics.eps_ttm}</strong></p>
            <p>Dette Nette : <strong>${(data.metrics.net_debt / 1e9).toFixed(2)} Mds</strong></p>
            <p>Actions en Circulation : <strong>{(data.metrics.shares_outstanding / 1e9).toFixed(2)} Mds</strong></p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;