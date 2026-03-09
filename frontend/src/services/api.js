import axios from 'axios';

// Configure base URL - can be set via environment variable
// In production (Docker), nginx proxies /api/ to the backend
const API_BASE_URL = process.env.REACT_APP_API_URL
  ? `${process.env.REACT_APP_API_URL}/api`
  : '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Get system status
export const getSystemStatus = async () => {
  const response = await api.get('/status');
  return response.data;
};

// Get database statistics
export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

// Get all domains
export const getDomains = async () => {
  const response = await api.get('/domains');
  return response.data;
};

// Analyze a single ticket
export const analyzeTicket = async (ticketNumber, context, domain = null) => {
  const response = await api.post('/analyze', {
    ticket_number: ticketNumber,
    context: context,
    domain: domain,
  });
  return response.data;
};

// Batch analyze tickets
export const batchAnalyzeTickets = async (tickets, showProgress = false) => {
  const response = await api.post('/analyze/batch', {
    tickets: tickets,
    show_progress: showProgress,
  });
  return response.data;
};

// Get ticket by number
export const getTicket = async (ticketNumber) => {
  const response = await api.get(`/tickets/${ticketNumber}`);
  return response.data;
};

// Search similar tickets
export const searchSimilarTickets = async (query, domain, topK = 5, similarityThreshold = 0.7) => {
  const response = await api.post('/search', {
    query: query,
    domain: domain,
    top_k: topK,
    similarity_threshold: similarityThreshold,
  });
  return response.data;
};

// Get resolution suggestions
export const suggestResolution = async (problemDescription, domain, topK = 5) => {
  const response = await api.post('/suggest-resolution', {
    problem_description: problemDescription,
    domain: domain,
    top_k: topK,
  });
  return response.data;
};

export default api;