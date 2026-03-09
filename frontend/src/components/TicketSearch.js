import React, { useState } from 'react';
import { searchSimilarTickets } from '../services/api';

const TicketSearch = ({ domains }) => {
  const [query, setQuery] = useState('');
  const [domain, setDomain] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || !domain) {
      setError('Please provide a query and select a domain');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await searchSimilarTickets(query, domain, topK);
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search tickets');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Search Similar Tickets</h2>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Domain *</label>
            <select
              className="form-select"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
            >
              <option value="">-- Select Domain --</option>
              {domains &&
                domains.map((d, index) => (
                  <option key={index} value={d}>
                    {d}
                  </option>
                ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Problem Description *</label>
            <textarea
              className="form-textarea"
              placeholder="Describe the problem you're looking for similar tickets..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={4}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Number of Results</label>
            <input
              type="number"
              className="form-input"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
              style={{ width: '100px' }}
            />
          </div>

          {error && (
            <div className="result-box" style={{ borderColor: '#ef4444' }}>
              <p style={{ color: '#ef4444' }}>{error}</p>
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner" style={{ width: 16, height: 16 }}></span>
                Searching...
              </>
            ) : (
              'Search Similar Tickets'
            )}
          </button>
        </form>
      </div>

      {results && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              Search Results ({results.length} tickets found)
            </h2>
          </div>

          {results.length > 0 ? (
            <div className="tickets-list">
              {results.map((ticket, index) => (
                <div key={index} className="ticket-item">
                  <div className="ticket-header">
                    <span className="ticket-number">{ticket.ticket_number}</span>
                    <span className="similarity-score">
                      {(ticket.similarity * 100).toFixed(1)}% similar
                    </span>
                  </div>
                  <div className="ticket-detail">
                    <strong>Cause:</strong> {ticket.cause || 'No cause documented'}
                  </div>
                  <div className="ticket-detail">
                    <strong>Resolution:</strong> {ticket.resolution_summary || 'No resolution documented'}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="result-box">
              <p style={{ color: '#94a3b8' }}>
                No similar tickets found in the "{domain}" domain. Try adjusting your search
                or check if there are resolved tickets in this domain.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TicketSearch;