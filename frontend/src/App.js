import React, { useState, useEffect } from 'react';
import './App.css';
import {
  analyzeTicket,
  searchSimilarTickets,
  suggestResolution,
  getStats,
  getDomains,
  getSystemStatus,
} from './services/api';
import TicketAnalyzer from './components/TicketAnalyzer';
import TicketSearch from './components/TicketSearch';
import ResolutionSuggester from './components/ResolutionSuggester';
import Dashboard from './components/Dashboard';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [domains, setDomains] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [statsData, domainsData, statusData] = await Promise.all([
        getStats(),
        getDomains(),
        getSystemStatus(),
      ]);
      setStats(statsData);
      setDomains(domainsData);
      setStatus(statusData);
      setError(null);
    } catch (err) {
      setError('Failed to connect to API. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const refreshStats = async () => {
    try {
      const statsData = await getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to refresh stats:', err);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Ticket RAG System</h1>
          <div className="status-badge">
            {status ? (
              <>
                <span className="status-dot online"></span>
                <span>{status.api_type} | {status.models?.llm}</span>
              </>
            ) : (
              <>
                <span className="status-dot offline"></span>
                <span>Disconnected</span>
              </>
            )}
          </div>
        </div>
      </header>

      <nav className="nav">
        <button
          className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`nav-btn ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          Analyze Ticket
        </button>
        <button
          className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          Search Similar
        </button>
        <button
          className={`nav-btn ${activeTab === 'suggest' ? 'active' : ''}`}
          onClick={() => setActiveTab('suggest')}
        >
          Suggest Resolution
        </button>
      </nav>

      <main className="main">
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        ) : error ? (
          <div className="error-container">
            <p className="error">{error}</p>
            <button onClick={loadInitialData} className="btn btn-primary">
              Retry Connection
            </button>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <Dashboard stats={stats} domains={domains} onRefresh={refreshStats} />
            )}
            {activeTab === 'analyze' && (
              <TicketAnalyzer domains={domains} onAnalyze={refreshStats} />
            )}
            {activeTab === 'search' && (
              <TicketSearch domains={domains} />
            )}
            {activeTab === 'suggest' && (
              <ResolutionSuggester domains={domains} />
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <p>Ticket RAG System v3.0 | Powered by RAG & LLM</p>
      </footer>
    </div>
  );
}

export default App;