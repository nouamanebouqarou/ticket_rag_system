import React, { useState } from 'react';
import { suggestResolution } from '../services/api';

const ResolutionSuggester = ({ domains }) => {
  const [problem, setProblem] = useState('');
  const [domain, setDomain] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [suggestion, setSuggestion] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!problem.trim() || !domain) {
      setError('Please provide a problem description and select a domain');
      return;
    }

    setLoading(true);
    setError(null);
    setSuggestion(null);

    try {
      const data = await suggestResolution(problem, domain, topK);
      setSuggestion(data.suggestions);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate suggestions');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Suggest Resolution</h2>
        </div>
        <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
          Get AI-powered resolution suggestions based on historically similar resolved tickets.
          The system will search for similar cases and generate actionable recommendations.
        </p>
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
              placeholder="Describe the current problem in detail. Include symptoms, error messages, affected systems, etc."
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
              rows={6}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Number of Similar Tickets to Consider</label>
            <input
              type="number"
              className="form-input"
              min="1"
              max="10"
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
                Generating Suggestions...
              </>
            ) : (
              'Get Resolution Suggestions'
            )}
          </button>
        </form>
      </div>

      {suggestion && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">AI-Generated Resolution Suggestions</h2>
            <span className="badge badge-info">Domain: {domain}</span>
          </div>
          <div className="result-box">
            <div className="result-content">
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                {suggestion}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResolutionSuggester;