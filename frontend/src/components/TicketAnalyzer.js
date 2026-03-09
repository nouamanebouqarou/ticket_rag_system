import React, { useState } from 'react';
import { analyzeTicket } from '../services/api';

const TicketAnalyzer = ({ domains, onAnalyze }) => {
  const [ticketNumber, setTicketNumber] = useState('');
  const [context, setContext] = useState('');
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ticketNumber.trim() || !context.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeTicket(ticketNumber, context, domain || null);
      setResult(data);
      if (onAnalyze) {
        onAnalyze();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze ticket');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (isResolved) => {
    if (isResolved === true) {
      return <span className="badge badge-success">Resolved</span>;
    } else if (isResolved === false) {
      return <span className="badge badge-danger">Not Resolved</span>;
    }
    return <span className="badge badge-warning">Uncertain</span>;
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Analyze Ticket</h2>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Ticket Number *</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., TI0000001"
              value={ticketNumber}
              onChange={(e) => setTicketNumber(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Domain (Optional)</label>
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
              <option value="__custom__">Other (type in context)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Ticket Context / Description *</label>
            <textarea
              className="form-textarea"
              placeholder="Paste the full ticket description, including any activity reports, resolution steps, etc."
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={8}
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
                Analyzing...
              </>
            ) : (
              'Analyze Ticket'
            )}
          </button>
        </form>
      </div>

      {result && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Analysis Result</h2>
            {getStatusBadge(result.is_resolved)}
          </div>

          <div className="result-box">
            <div className="result-header">
              <span className="result-title">Ticket: {result.ticket_number}</span>
              {result.domain && <span className="badge badge-info">{result.domain}</span>}
            </div>

            {result.is_resolved === true ? (
              <div className="result-content">
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Cause Summary</strong>
                  <p style={{ marginTop: '0.5rem', color: '#f1f5f9' }}>
                    {result.cause_summary || 'No cause identified'}
                  </p>
                </div>

                {result.keywords && result.keywords.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <strong>Keywords</strong>
                    <div className="keywords">
                      {result.keywords.map((keyword, index) => (
                        <span key={index} className="keyword">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ marginBottom: '1rem' }}>
                  <strong>Resolution Summary</strong>
                  <p style={{ marginTop: '0.5rem', color: '#f1f5f9' }}>
                    {result.resolution_summary || 'No resolution documented'}
                  </p>
                </div>

                {result.resolution_steps && result.resolution_steps.length > 0 && (
                  <div>
                    <strong>Resolution Steps</strong>
                    <ol className="steps-list" style={{ marginTop: '0.5rem' }}>
                      {result.resolution_steps.map((step, index) => (
                        <li key={index}>{step}</li>
                      ))}
                    </ol>
                  </div>
                )}

                <div style={{ marginTop: '1rem', color: '#94a3b8', fontSize: '0.85rem' }}>
                  <span>Embedding Generated: {result.embedding_generated ? 'Yes' : 'No'}</span>
                  <span style={{ marginLeft: '1rem' }}>Saved to DB: {result.saved_to_db ? 'Yes' : 'No'}</span>
                </div>
              </div>
            ) : (
              <div className="result-content">
                <p style={{ color: '#94a3b8' }}>
                  {result.is_resolved === false
                    ? 'This ticket was not resolved. No detailed analysis was performed.'
                    : 'The resolution status could not be determined from the provided context.'}
                </p>
                <div style={{ marginTop: '1rem', color: '#94a3b8', fontSize: '0.85rem' }}>
                  <span>Saved to DB: {result.saved_to_db ? 'Yes' : 'No'}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TicketAnalyzer;