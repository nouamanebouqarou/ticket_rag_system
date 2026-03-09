import React from 'react';

const Dashboard = ({ stats, domains, onRefresh }) => {
  if (!stats) {
    return (
      <div className="card">
        <p>No statistics available</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Database Statistics</h2>
          <button onClick={onRefresh} className="btn btn-secondary">
            Refresh
          </button>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_tickets || 0}</div>
            <div className="stat-label">Total Tickets</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: '#10b981' }}>
              {stats.resolved_tickets || 0}
            </div>
            <div className="stat-label">Resolved</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: '#ef4444' }}>
              {stats.unresolved_tickets || 0}
            </div>
            <div className="stat-label">Unresolved</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: '#0ea5e9' }}>
              {domains?.length || 0}
            </div>
            <div className="stat-label">Domains</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Available Domains</h2>
        </div>
        {domains && domains.length > 0 ? (
          <div className="domain-tags">
            {domains.map((domain, index) => (
              <span key={index} className="domain-tag">
                {domain}
              </span>
            ))}
          </div>
        ) : (
          <p style={{ color: '#94a3b8' }}>No domains found. Analyze some tickets to populate domains.</p>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Quick Start Guide</h2>
        </div>
        <div className="result-content">
          <ol className="steps-list">
            <li>
              <strong>Analyze Ticket</strong> - Submit a ticket for analysis. The system will determine
              if it's resolved, extract the root cause, and generate embeddings for semantic search.
            </li>
            <li>
              <strong>Search Similar</strong> - Find similar resolved tickets based on a problem description.
              Results are filtered by domain for relevance.
            </li>
            <li>
              <strong>Suggest Resolution</strong> - Get AI-powered resolution suggestions based on
              historically similar tickets.
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;