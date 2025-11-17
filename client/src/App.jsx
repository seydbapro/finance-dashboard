import React, { useState } from 'react';
import './styles.css'; // Assurez-vous d'avoir renommé le fichier CSS en styles.css

function App() {
  const [ticker, setTicker] = useState('MSFT');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [fcfGrowth, setFcfGrowth] = useState(10); // Hypothèse FCF par défaut (10%)
  
  // L'URL de base pour appeler vos fonctions Python Serverless sur Vercel
  const BASE_URL = '/api'; 

  const fetchData = async () => {
    if (!ticker) return;

    setLoading(true);
    setData(null);

    try {
      // --- 1. Récupération du WACC (Taux d'Actualisation) ---
      const waccRes = await fetch(`${BASE_URL}/wacc?ticker=${ticker}`);
      const waccJson = await waccRes.json();
      
      const calculatedWACC = waccJson.success ? waccJson.data.wacc : null;
      
      if (!calculatedWACC) {
        throw new Error(waccJson.error || 'Erreur lors du calcul du WACC');
      }

      // --- 2. Récupération du ROCE (Scoring de Qualité) ---
      const roceRes = await fetch(`${BASE_URL}/roce?ticker=${ticker}`);
      const roceJson = await roceRes.json();

      // --- 3. Récupération du Ratio de Sharpe (Risque Ajusté) ---
      const sharpeRes = await fetch(`${BASE_URL}/sharpe?ticker=${ticker}`);
      const sharpeJson = await sharpeRes.json();

      // --- 4. Calcul du DCF (avec WACC et hypothèse de croissance FCF) ---
      const dcfRes = await fetch(`${BASE_URL}/dcf_model?ticker=${ticker}&wacc=${calculatedWACC}&growth=${fcfGrowth / 100}`);
      const dcfJson = await dcfRes.json();

      // --- 5. Mise à jour de l'état global ---
      setData({
        ticker,
        wacc: waccJson.data,
        roce: roceJson.data,
        sharpe: sharpeJson.data, // Ajout du Ratio de Sharpe
        dcf: dcfJson.data,
        
        // Gestion des erreurs consolidées
        error: dcfJson.error || roceJson.error || waccJson.error || sharpeJson.error
      });

    } catch (error) {
      setData({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>💰 Analyse d'Investissement Interactif</h1>
      
      {/* ----------------- Composant de Recherche ----------------- */}
      <div className="search-bar">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Entrez un Ticker (ex: MSFT)"
        />
        <button onClick={fetchData} disabled={loading}>
          {loading ? 'Analyse en cours...' : 'Analyser le Ticker'}
        </button>
      </div>

      {/* Affichage des Erreurs */}
      {data && data.error && <p className="error-message">Erreur : {data.error}</p>}

      {/* ----------------- AFFICHAGE DES RÉSULTATS ----------------- */}
      {data && !data.error && (
        <div className="results">
          <h2>Résultats Clés pour {data.ticker}</h2>

          <div className="grid-layout">
              
              {/* Carte 1 : SCORING ROCE (Rouge/Vert) */}
              <div className={`kpi-card ${data.roce.roce_statut === 'Vert' ? 'bg-green' : 'bg-red'}`}>
                <h3>ROCE Moyen (Qualité)</h3>
                <p className="kpi-value">{data