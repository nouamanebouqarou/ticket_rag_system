import React, { useState } from 'react';
import { Send, Loader2, CheckCircle, XCircle, HelpCircle, Tag, FileText, ListChecks } from 'lucide-react';
import { analyzeTicket } from '../services/api';

const TicketAnalyzer = ({ domains, onTicketAnalyzed }) => {
  const [ticketNumber, setTicketNumber] = useState('');
  const [context, setContext] = useState('');
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ticketNumber.trim() || !context.trim()) {
      setError('Please fill in ticket number and context');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeTicket(
        ticketNumber.trim(),
        context.trim(),
        domain || null
      );
      setResult(data);
      if (onTicketAnalyzed) {
        onTicketAnalyzed(data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to analyze ticket');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (isResolved) => {
    if (isResolved === true) return <CheckCircle className="status-icon resolved" />;
    if (isResolved === false) return <XCircle className="status-icon unresolved" />;
    return <HelpCircle className="status-icon uncertain" />;
  };

  const getStatusLabel = (isResolved) => {
    if (isResolved === true) return 'Resolved';
    if (isResolved === false) return 'Unresolved';
    return 'Uncertain';
  };

  return (
    <div className="card">
      <h2 className="card-title">
        <FileText size={20} />
        Analyze Ticket
      </h2>

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="ticketNumber">Ticket Number</label>
          <input
            type="text"
            id="ticketNumber"
            value={ticketNumber}
            onChange={(e) => setTicketNumber(e.target.value)}
            placeholder="e.g., TI0000001"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="domain">Domain (Optional)</label>
          <select
            id="domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            disabled={loading}
          >
            <option value="">Select a domain...</option>
            {domains.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="context">Ticket Context / Description</label>
          <textarea
            id="context"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Paste the ticket description, activity report, or problem details here..."
            rows={6}
            disabled={loading}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="spinner" size={18} />
              Analyzing...
            </>
          ) : (
            <>
              <Send size={18} />
              Analyze Ticket
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {result && (
        <div className="result-section">
          <h3 className="result-title">Analysis Result</h3>

          <div className="result-header">
            <div className="ticket-info">
              <span className="ticket-number">{result.ticket_number}</span>
              {result.domain && <span className="ticket-domain">{result.domain}</span>}
            </div>
            <div className={`status-badge ${result.is_resolved === true ? 'resolved' : result.is_resolved === false ? 'unresolved' : 'uncertain'}`}>
              {getStatusIcon(result.is_resolved)}
              {getStatusLabel(result.is_resolved)}
            </div>
          </div>

          {result.is_resolved === true && (
            <div className="analysis-details">
              {result.cause_summary && (
                <div className="detail-section">
                  <h4>
                    <Tag size={16} />
                    Root Cause
                  </h4>
                  <p>{result.cause_summary}</p>
                </div>
              )}

              {result.keywords && result.keywords.length > 0 && (
                <div className="detail-section">
                  <h4>Keywords</h4>
                  <div className="keywords-list">
                    {result.keywords.map((keyword, index) => (
                      <span key={index} className="keyword-tag">{keyword}</span>
                    ))}
                  </div>
                </div>
              )}

              {result.resolution_summary && (
                <div className="detail-section">
                  <h4>Resolution Summary</h4>
                  <p>{result.resolution_summary}</p>
                </div>
              )}

              {result.resolution_steps && result.resolution_steps.length > 0 && (
                <div className="detail-section">
                  <h4>
                    <ListChecks size={16} />
                    Resolution Steps
                  </h4>
                  <ol className="steps-list">
                    {result.resolution_steps.map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              <div className="meta-info">
                <span className={`badge ${result.embedding_generated ? 'success' : 'warning'}`}>
                  Embedding: {result.embedding_generated ? 'Generated' : 'Not Generated'}
                </span>
                <span className={`badge ${result.saved_to_db ? 'success' : 'warning'}`}>
                  Database: {result.saved_to_db ? 'Saved' : 'Not Saved'}
                </span>
              </div>
            </div>
          )}

          {result.error && (
            <div className="error-message">
              Error: {result.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TicketAnalyzer;