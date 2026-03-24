const API_BASE = '/api';

export async function fetchGraph(limit = 300) {
  const res = await fetch(`${API_BASE}/graph?limit=${limit}`);
  return res.json();
}

export async function fetchNodeDetails(entityType, entityId) {
  const res = await fetch(`${API_BASE}/node/${entityType}/${entityId}`);
  return res.json();
}

export async function fetchNeighbors(entityType, entityId) {
  const res = await fetch(`${API_BASE}/neighbors/${entityType}/${entityId}`);
  return res.json();
}

export async function sendChat(question, conversationHistory) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_history: conversationHistory }),
  });
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/stats`);
  return res.json();
}
