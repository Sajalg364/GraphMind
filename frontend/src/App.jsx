import { useState, useEffect, useRef, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import ReactMarkdown from 'react-markdown'
import { fetchGraph, fetchNodeDetails, fetchNeighbors, sendChat, fetchStats } from './api'

const ENTITY_COLORS = {
  SalesOrder: '#4A90D9',
  Delivery: '#2ECC71',
  BillingDocument: '#E74C3C',
  JournalEntry: '#F39C12',
  Payment: '#9B59B6',
  Customer: '#00BCD4',
  Product: '#FF6F61',
  Plant: '#8BC34A',
}

const EXAMPLE_QUERIES = [
  'Which products are associated with the highest number of billing documents?',
  'Trace the full flow of billing document 90504248',
  'Find sales orders that were delivered but not billed',
  'How many sales orders does each customer have?',
  'Show me the total billing amount by customer',
]

export default function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] })
  const [selectedNode, setSelectedNode] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const graphRef = useRef()
  const messagesEndRef = useRef(null)
  const [graphLoading, setGraphLoading] = useState(true)
  const graphContainerRef = useRef(null)
  const [graphDimensions, setGraphDimensions] = useState({ width: 800, height: 600 })

  useEffect(() => {
    loadGraph()
    fetchStats().then(setStats).catch(() => {})
  }, [])

  useEffect(() => {
    const updateDimensions = () => {
      if (graphContainerRef.current) {
        const { clientWidth, clientHeight } = graphContainerRef.current
        setGraphDimensions({ width: clientWidth, height: clientHeight })
      }
    }
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadGraph = async () => {
    setGraphLoading(true)
    try {
      const data = await fetchGraph(300)
      const nodes = data.nodes || []
      const links = (data.edges || []).map(e => ({
        source: e.source,
        target: e.target,
        relation: e.relation,
      }))
      setGraphData({ nodes, links })
    } catch (err) {
      console.error('Failed to load graph:', err)
    }
    setGraphLoading(false)
  }

  const handleNodeClick = useCallback(async (node) => {
    try {
      const details = await fetchNodeDetails(node.entity, node.entityId)
      setSelectedNode(details)
    } catch {
      setSelectedNode({ entity: node.entity, entityId: node.entityId, details: node, connections: [] })
    }
  }, [])

  const handleExpandNode = useCallback(async (entityType, entityId) => {
    try {
      const neighbors = await fetchNeighbors(entityType, entityId)
      if (neighbors.nodes?.length) {
        setGraphData(prev => {
          const existingIds = new Set(prev.nodes.map(n => n.id))
          const newNodes = neighbors.nodes.filter(n => !existingIds.has(n.id))
          const existingEdges = new Set(prev.links.map(l =>
            `${typeof l.source === 'object' ? l.source.id : l.source}-${typeof l.target === 'object' ? l.target.id : l.target}`
          ))
          const newLinks = neighbors.edges
            .map(e => ({ source: e.source, target: e.target, relation: e.relation }))
            .filter(l => !existingEdges.has(`${l.source}-${l.target}`))

          return {
            nodes: [...prev.nodes, ...newNodes],
            links: [...prev.links, ...newLinks],
          }
        })
      }
    } catch (err) {
      console.error('Failed to expand node:', err)
    }
  }, [])

  const handleSend = async () => {
    const question = input.trim()
    if (!question || loading) return

    const userMsg = { role: 'user', content: question }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      const result = await sendChat(question, history)
      const assistantMsg = {
        role: 'assistant',
        content: result.answer,
        type: result.type,
        sql: result.sql,
        rowCount: result.row_count,
        data: result.data,
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to get a response. Please check if the backend is running.',
        type: 'error',
      }])
    }
    setLoading(false)
  }

  const handleExampleClick = (q) => {
    setInput(q)
  }

  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const size = 4
    const color = node.color || ENTITY_COLORS[node.entity] || '#666'

    ctx.beginPath()
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI)
    ctx.fillStyle = color
    ctx.fill()

    if (globalScale > 1.5) {
      const label = node.label || node.entityId
      const fontSize = Math.max(10 / globalScale, 2)
      ctx.font = `${fontSize}px Sans-Serif`
      ctx.fillStyle = 'rgba(228, 230, 235, 0.8)'
      ctx.textAlign = 'center'
      ctx.fillText(label, node.x, node.y + size + fontSize + 1)
    }
  }, [])

  return (
    <div className="app-container">
      <div className="graph-panel" ref={graphContainerRef}>
        <div className="graph-header">
          <div className="graph-title">
            <h1>SAP O2C Graph Explorer</h1>
            {stats && (
              <div className="stats-bar">
                <span className="stat-chip">{graphData.nodes.length} nodes</span>
                <span className="stat-chip">{graphData.links.length} edges</span>
              </div>
            )}
          </div>
          <div className="graph-controls">
            <button onClick={() => graphRef.current?.zoomToFit(400)}>Fit View</button>
            <button onClick={loadGraph}>Reload</button>
          </div>
        </div>

        {!graphLoading && (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={graphDimensions.width}
            height={graphDimensions.height}
            nodeCanvasObject={nodeCanvasObject}
            nodePointerAreaPaint={(node, color, ctx) => {
              ctx.beginPath()
              ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI)
              ctx.fillStyle = color
              ctx.fill()
            }}
            linkColor={() => 'rgba(74, 144, 217, 0.15)'}
            linkWidth={0.5}
            onNodeClick={handleNodeClick}
            backgroundColor="#0f1117"
            cooldownTicks={100}
            onEngineStop={() => graphRef.current?.zoomToFit(400)}
          />
        )}

        <div className="legend">
          {Object.entries(ENTITY_COLORS).map(([entity, color]) => (
            <div key={entity} className="legend-item">
              <div className="legend-dot" style={{ backgroundColor: color }} />
              <span>{entity}</span>
            </div>
          ))}
        </div>

        {selectedNode && (
          <div className="node-detail-overlay">
            <div className="node-detail-header">
              <h3>
                <span style={{ color: ENTITY_COLORS[selectedNode.entity] }}>
                  {selectedNode.entity}
                </span>
                {' '}{selectedNode.entityId}
              </h3>
              <button onClick={() => setSelectedNode(null)}>✕</button>
            </div>
            {selectedNode.details && Object.entries(selectedNode.details)
              .filter(([k, v]) => v !== null && v !== '' && k !== 'error')
              .map(([key, value]) => (
                <div key={key} className="detail-row">
                  <span className="detail-key">{key}</span>
                  <span className="detail-value">{String(value)}</span>
                </div>
              ))
            }
            {selectedNode.connections?.length > 0 && (
              <div className="connections-section">
                <h4>Connections ({selectedNode.connections.length})</h4>
                {selectedNode.connections.slice(0, 20).map((conn, i) => (
                  <div
                    key={i}
                    className="connection-item"
                    onClick={() => {
                      handleExpandNode(conn.type, conn.id)
                      handleNodeClick({ entity: conn.type, entityId: conn.id })
                    }}
                  >
                    <span
                      className="connection-badge"
                      style={{ backgroundColor: ENTITY_COLORS[conn.type] || '#666' }}
                    >
                      {conn.type}
                    </span>
                    <span>{conn.id}</span>
                    <span style={{ color: 'var(--text-secondary)', marginLeft: 'auto', fontSize: 11 }}>
                      {conn.relation}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="chat-panel">
        <div className="chat-header">
          <div className="chat-header-row">
            <div>
              <h2>Chat with Graph</h2>
              <p>Ask questions about SAP Order-to-Cash data</p>
            </div>
            {messages.length > 0 && (
              <button className="new-chat-btn" onClick={() => setMessages([])}>New Chat</button>
            )}
          </div>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="welcome-msg">
              <h3>SAP O2C Graph Agent</h3>
              <p>Ask anything about sales orders, deliveries, billing, payments, customers, or products.</p>
              <div className="examples">
                {EXAMPLE_QUERIES.map((q, i) => (
                  <span key={i} className="example-query" onClick={() => handleExampleClick(q)}>
                    {q}
                  </span>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role} ${msg.type === 'error' ? 'error' : ''}`}>
              {msg.role === 'assistant' ? (
                <div>
                  <div className="markdown-content">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              ) : (
                msg.content
              )}
            </div>
          ))}

          {loading && (
            <div className="message loading">
              <span className="typing-dots">
                <span>·</span><span>·</span><span>·</span>
              </span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask about the O2C data..."
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
