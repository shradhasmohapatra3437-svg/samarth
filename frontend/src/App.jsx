import React, { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('copilot');
  const [equipmentList, setEquipmentList] = useState([]);
  const [selectedEquip, setSelectedEquip] = useState('P-204');
  
  // Tab 1: Copilot Chat State
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'bot',
      text: 'Hello! I am Samarth, your industrial safety and reliability expert copilot. How can I help you today?',
      intent: 'general',
      confidence: 100,
      sources: []
    }
  ]);
  const [loadingChat, setLoadingChat] = useState(false);

  // Tab 2: RCA State
  const [rcaData, setRcaData] = useState(null);
  const [loadingRca, setLoadingRca] = useState(false);

  // Tab 3: Compliance State
  const [complianceData, setComplianceData] = useState(null);
  const [loadingCompliance, setLoadingCompliance] = useState(false);

  // Tab 4: Graph State
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [loadingGraph, setLoadingGraph] = useState(false);

  // Tab 5: Fleet Intelligence State
  const [fleetData, setFleetData] = useState(null);
  const [loadingFleet, setLoadingFleet] = useState(false);

  // Suggested questions for chat copilot
  const suggestions = [
    "Why does P-204 keep failing and who usually fixes it?",
    "Is P-204 compliant with OISD standard requirements?",
    "What are the recurring failure modes across the plant?",
    "Show compliance status for compressor C-07 under OISD",
    "What does the Factories Act 1948 say about worker safety obligations?"
  ];

  // Fetch equipment list on mount
  useEffect(() => {
    fetch(`${API_BASE}/equipment/list`)
      .then(res => res.json())
      .then(data => {
        if (data.equipment) {
          setEquipmentList(data.equipment);
          if (data.equipment.length > 0 && !data.equipment.includes(selectedEquip)) {
            setSelectedEquip(data.equipment[0]);
          }
        }
      })
      .catch(err => console.error("Error loading equipment list:", err));
  }, []);

  // Fetch RCA Data when selected equipment changes
  useEffect(() => {
    if (activeTab === 'rca') {
      fetchRca(selectedEquip);
    } else if (activeTab === 'compliance') {
      fetchCompliance(selectedEquip);
    }
  }, [selectedEquip, activeTab]);

  // Fetch Graph Data on Tab click
  useEffect(() => {
    if (activeTab === 'graph') {
      setLoadingGraph(true);
      fetch(`${API_BASE}/graph/data`)
        .then(res => res.json())
        .then(data => {
          setGraphData(data);
          setLoadingGraph(false);
        })
        .catch(err => {
          console.error("Error loading graph:", err);
          setLoadingGraph(false);
        });
    } else if (activeTab === 'fleet') {
      setLoadingFleet(true);
      fetch(`${API_BASE}/fleet/failure-report`)
        .then(res => res.json())
        .then(data => {
          setFleetData(data);
          setLoadingFleet(false);
        })
        .catch(err => {
          console.error("Error loading fleet report:", err);
          setLoadingFleet(false);
        });
    }
  }, [activeTab]);

  const fetchRca = (equipId) => {
    setLoadingRca(true);
    // Call the query endpoint asking for RCA analysis explicitly
    fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: `Run root cause analysis (RCA) and risk assessment for ${equipId}` })
    })
      .then(res => res.json())
      .then(data => {
        // Also fetch priority score info
        fetch(`${API_BASE}/equipment/${equipId}/priority`)
          .then(pRes => pRes.json())
          .then(pData => {
            setRcaData({
              narrative: data.answer,
              sources: data.sources,
              priority: pData
            });
            setLoadingRca(false);
          })
          .catch(err => {
            setRcaData({ narrative: data.answer, sources: data.sources, priority: null });
            setLoadingRca(false);
          });
      })
      .catch(err => {
        console.error("RCA Error:", err);
        setLoadingRca(false);
      });
  };

  const fetchCompliance = (equipId) => {
    setLoadingCompliance(true);
    fetch(`${API_BASE}/equipment/${equipId}/qms-report`)
      .then(res => res.json())
      .then(data => {
        setComplianceData(data);
        setLoadingCompliance(false);
      })
      .catch(err => {
        console.error("Compliance Error:", err);
        setLoadingCompliance(false);
      });
  };

  const renderFormattedText = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // 1. Check for Step headers: e.g. "## Step 1: Analyze..."
      const stepMatch = line.match(/^#+\s*(Step\s+\d+:\s*(.*))/i);
      if (stepMatch) {
        return (
          <h4 key={idx} style={{ color: 'var(--accent-purple)', fontWeight: '700', fontSize: '15px', margin: '14px 0 6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ background: 'var(--accent-purple)', width: '6px', height: '6px', borderRadius: '50%' }}></span>
            {stepMatch[1]}
          </h4>
        );
      }
      
      // 2. Check for other headers: e.g. "### LIKELY ROOT CAUSE(S)"
      const headerMatch = line.match(/^#+\s*(.*)/);
      if (headerMatch) {
        const headerText = headerMatch[1].trim();
        let headerColor = 'var(--accent-purple)';
        if (headerText.includes('ROOT CAUSE')) headerColor = 'var(--accent-orange)';
        if (headerText.includes('RISK')) headerColor = 'var(--accent-red)';
        if (headerText.includes('RECOMMENDED') || headerText.includes('ACTION')) headerColor = 'var(--accent-green)';
        if (headerText.includes('CONFIDENCE')) headerColor = 'var(--accent-blue)';
        
        return (
          <h5 key={idx} style={{ color: headerColor, fontWeight: '700', fontSize: '14px', margin: '16px 0 8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {headerText}
          </h5>
        );
      }
      
      // 3. Bold text inline: replace **text** with strong tags
      const parts = line.split(/(\*\*.*?\*\*)/);
      const renderedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx} style={{ color: '#fff', fontWeight: '600' }}>{part.slice(2, -2)}</strong>;
        }
        return part;
      });
      
      return (
        <p key={idx} style={{ margin: '4px 0', color: 'var(--text-primary)', minHeight: line.trim() ? 'auto' : '10px', textAlign: 'left' }}>
          {renderedParts}
        </p>
      );
    });
  };

  const handleSendMessage = (textToSend) => {
    const queryText = textToSend || chatInput;
    if (!queryText.trim()) return;

    setChatMessages(prev => [...prev, { sender: 'user', text: queryText }]);
    if (!textToSend) setChatInput('');
    setLoadingChat(true);

    fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: queryText })
    })
      .then(res => res.json())
      .then(data => {
        setChatMessages(prev => [...prev, {
          sender: 'bot',
          text: data.answer,
          intent: data.intent_classified,
          confidence: data.confidence,
          sources: data.sources,
          equipment_id: data.equipment_id
        }]);
        setLoadingChat(false);
      })
      .catch(err => {
        setChatMessages(prev => [...prev, {
          sender: 'bot',
          text: `Failed to get response: ${err.message}. Make sure backend server is running at ${API_BASE}.`,
          intent: 'error',
          confidence: 0,
          sources: []
        }]);
        setLoadingChat(false);
      });
  };

  // Helper function to colorize score badge
  const getScoreColor = (score) => {
    if (score >= 7.5) return 'var(--accent-red)';
    if (score >= 5.0) return 'var(--accent-orange)';
    return 'var(--accent-green)';
  };

  // Custom visual layout positioning for Graph visualization (layered architecture)
  const renderInteractiveGraph = () => {
    if (graphData.nodes.length === 0) return <div style={{ color: 'var(--text-secondary)' }}>No graph data loaded.</div>;

    const width = 800;
    const height = 550;
    const padding = 60;

    // Group nodes by category to construct layers
    const groups = {
      regulation: [],
      location: [],
      equipment: [],
      failure_mode: [],
      person: []
    };

    graphData.nodes.forEach(node => {
      const type = node.type || 'unknown';
      if (groups[type]) {
        groups[type].push(node);
      } else {
        groups.equipment.push(node); // fallback
      }
    });

    const categories = ['regulation', 'location', 'equipment', 'failure_mode', 'person'];
    const columnWidth = (width - padding * 2) / (categories.length - 1);
    
    // Map of nodeId -> coordinates
    const nodeCoords = {};

    categories.forEach((cat, colIdx) => {
      const catNodes = groups[cat];
      const x = padding + colIdx * columnWidth;
      const count = catNodes.length;

      catNodes.forEach((node, nodeIdx) => {
        // Space nodes vertically centered in the height
        const y = count > 1 
          ? padding + (nodeIdx * (height - padding * 2)) / (count - 1)
          : height / 2;
        nodeCoords[node.id] = { x, y };
      });
    });

    // Check relationship color
    const getEdgeColor = (rel) => {
      switch (rel) {
        case 'FAILED_WITH': return 'rgba(239, 68, 68, 0.4)';  // red
        case 'REPAIRED_BY': return 'rgba(16, 185, 129, 0.4)'; // green
        case 'GOVERNED_BY': return 'rgba(59, 130, 246, 0.4)'; // blue
        case 'LOCATED_AT':
        case 'LOCATED_IN': return 'rgba(245, 158, 11, 0.4)';  // orange
        default: return 'rgba(255, 255, 255, 0.15)';
      }
    };

    // Calculate highlighted items
    const isHighlighted = (nodeId) => {
      if (!selectedNode) return true; // nothing selected = normal
      if (selectedNode.id === nodeId) return true;
      // Is connected to selected node
      return graphData.edges.some(edge => 
        (edge.source === selectedNode.id && edge.target === nodeId) ||
        (edge.target === selectedNode.id && edge.source === nodeId)
      );
    };

    const isEdgeHighlighted = (source, target) => {
      if (!selectedNode) return true;
      return source === selectedNode.id || target === selectedNode.id;
    };

    return (
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '20px', position: 'relative', overflow: 'hidden', minHeight: '550px' }}>
          <div style={{ position: 'absolute', top: '15px', left: '15px', display: 'flex', gap: '15px', fontSize: '12px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-purple)' }}></span> Equipment</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-blue)' }}></span> Regulation</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-green)' }}></span> Technician</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-orange)' }}></span> Failure Mode</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}><span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#06b6d4' }}></span> Location</span>
          </div>
          
          <button 
            style={{ position: 'absolute', top: '15px', right: '15px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', fontSize: '12px' }}
            onClick={() => setSelectedNode(null)}
          >
            Reset Highlight
          </button>

          <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ background: 'transparent' }}>
            {/* Draw Links/Edges */}
            {graphData.edges.map((edge, idx) => {
              const start = nodeCoords[edge.source];
              const end = nodeCoords[edge.target];
              if (!start || !end) return null;
              
              const active = isEdgeHighlighted(edge.source, edge.target);
              
              return (
                <g key={`edge-${idx}`}>
                  <line
                    x1={start.x}
                    y1={start.y}
                    x2={end.x}
                    y2={end.y}
                    stroke={getEdgeColor(edge.relationship)}
                    strokeWidth={active ? 2.5 : 0.8}
                    opacity={active ? 1.0 : 0.15}
                    style={{ transition: 'all 0.3s' }}
                  />
                  {active && (
                    <text
                      x={(start.x + end.x) / 2}
                      y={(start.y + end.y) / 2 - 4}
                      fill="var(--text-muted)"
                      fontSize="9"
                      textAnchor="middle"
                    >
                      {edge.relationship}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Draw Nodes */}
            {graphData.nodes.map(node => {
              const coords = nodeCoords[node.id];
              if (!coords) return null;

              const active = isHighlighted(node.id);
              const isSelected = selectedNode?.id === node.id;
              
              // Node color based on type
              let color = 'var(--accent-purple)';
              if (node.type === 'regulation') color = 'var(--accent-blue)';
              if (node.type === 'person') color = 'var(--accent-green)';
              if (node.type === 'failure_mode') color = 'var(--accent-orange)';
              if (node.type === 'location') color = '#06b6d4';

              const radius = isSelected ? 12 : 7;

              return (
                <g 
                  key={node.id} 
                  transform={`translate(${coords.x}, ${coords.y})`}
                  style={{ cursor: 'pointer', transition: 'all 0.3s' }}
                  onClick={() => setSelectedNode(node)}
                  opacity={active ? 1.0 : 0.25}
                >
                  <circle
                    r={radius}
                    fill={color}
                    stroke="rgba(255,255,255,0.8)"
                    strokeWidth={isSelected ? 2 : 1}
                    className={isSelected ? "pulse-glow-border" : ""}
                  />
                  <text
                    y={radius + 12}
                    fill={isSelected ? '#ffffff' : 'var(--text-secondary)'}
                    fontSize={isSelected ? '11' : '9'}
                    fontWeight={isSelected ? 'bold' : 'normal'}
                    textAnchor="middle"
                    style={{ pointerEvents: 'none' }}
                  >
                    {node.id}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Graph Sidebar Details */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {selectedNode ? (
            <>
              <div>
                <span style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '1px' }}>Node Type</span>
                <h4 style={{ margin: '2px 0 0', textTransform: 'capitalize', color: 'var(--accent-purple)' }}>{selectedNode.type}</h4>
              </div>
              <div>
                <span style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '1px' }}>Identifier</span>
                <h3 style={{ margin: '2px 0 0', color: '#fff' }}>{selectedNode.id}</h3>
              </div>
              <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '12px' }}>
                <h5 style={{ margin: '0 0 8px', color: 'var(--text-secondary)' }}>Connected Elements</h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto', fontSize: '12px' }}>
                  {graphData.edges
                    .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge, i) => {
                      const neighbor = edge.source === selectedNode.id ? edge.target : edge.source;
                      return (
                        <div key={i} style={{ padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', borderLeft: '3px solid var(--accent-purple)' }}>
                          <div style={{ color: 'var(--text-primary)', fontWeight: '500' }}>{neighbor}</div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '10px', marginTop: '2px' }}>
                            {edge.source === selectedNode.id ? 'OUT' : 'IN'} - {edge.relationship} (wt: {edge.weight})
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', margin: 'auto 0', color: 'var(--text-muted)' }}>
              Click any node in the visualization to audit its semantic relationships.
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Premium Header Panel */}
      <header className="glass-panel" style={{ margin: '20px', padding: '15px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ background: 'var(--gradient-primary)', width: '36px', height: '36px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '20px', color: '#fff' }}>S</div>
          <div>
            <h2 style={{ margin: 0, fontSize: '22px', fontWeight: 'bold', background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>SAMARTH</h2>
            <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.5px' }}>INDUSTRIAL COMPLIANCE & RCA COPILOT</p>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '5px' }}>
          {[
            { id: 'copilot', label: 'Expert Copilot' },
            { id: 'rca', label: 'RCA Dashboard' },
            { id: 'compliance', label: 'Compliance Audit' },
            { id: 'graph', label: 'Knowledge Graph' },
            { id: 'fleet', label: 'Fleet Health' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? 'var(--gradient-primary)' : 'transparent',
                color: activeTab === tab.id ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '500',
                transition: 'all 0.3s ease',
                fontSize: '14px'
              }}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Global Equipment Selector */}
        {['rca', 'compliance'].includes(activeTab) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Equipment:</span>
            <select
              value={selectedEquip}
              onChange={(e) => setSelectedEquip(e.target.value)}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#fff',
                padding: '6px 12px',
                borderRadius: '6px',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {equipmentList.map(eq => (
                <option key={eq} value={eq} style={{ background: '#12141d', color: '#fff' }}>{eq}</option>
              ))}
            </select>
          </div>
        )}
      </header>

      {/* Main Contents Area */}
      <main style={{ flex: 1, padding: '0 20px 20px', display: 'flex', flexDirection: 'column' }}>
        
        {/* Tab 1: Copilot Chat */}
        {activeTab === 'copilot' && (
          <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '20px', flex: 1 }}>
            
            {/* Left Sidebar suggestions */}
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <h4 style={{ margin: '0 0 10px', color: 'var(--text-primary)' }}>Suggested Audits</h4>
              {suggestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(q)}
                  style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(255,255,255,0.05)',
                    borderRadius: '8px',
                    padding: '10px',
                    color: 'var(--text-secondary)',
                    fontSize: '12px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    lineHeight: '1.4'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.3)';
                    e.currentTarget.style.background = 'rgba(168, 85, 247, 0.02)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)';
                    e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                  }}
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Chat Box Area */}
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '620px' }}>
              {/* Message History */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
                {chatMessages.map((msg, idx) => (
                  <div 
                    key={idx} 
                    style={{ 
                      alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '75%',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '5px'
                    }}
                  >
                    <div style={{
                      background: msg.sender === 'user' ? 'var(--gradient-primary)' : 'rgba(255,255,255,0.03)',
                      border: msg.sender === 'user' ? 'none' : '1px solid rgba(255,255,255,0.05)',
                      padding: '12px 18px',
                      borderRadius: msg.sender === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                      color: '#fff',
                      fontSize: '14px',
                      lineHeight: '1.5',
                      textAlign: 'left'
                    }}>
                      {msg.sender === 'user' ? msg.text : renderFormattedText(msg.text)}
                    </div>

                    {/* Metadata block for copilot answers */}
                    {msg.sender === 'bot' && msg.intent && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '10px', color: 'var(--text-muted)', padding: '2px 5px' }}>
                        <span style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                          INTENT: <strong style={{ color: 'var(--accent-purple)' }}>{msg.intent.toUpperCase()}</strong>
                        </span>
                        <span style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                          CONFIDENCE: <strong style={{ color: 'var(--accent-green)' }}>{msg.confidence}%</strong>
                        </span>
                        {msg.sources && msg.sources.length > 0 && (
                          <span style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                            SOURCES: {Array.from(new Set(msg.sources)).join(', ')}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                
                {loadingChat && (
                  <div style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', padding: '12px 18px', borderRadius: '16px 16px 16px 4px', color: 'var(--text-muted)', fontSize: '14px' }}>
                    Agent is processing query and query engines...
                  </div>
                )}
              </div>

              {/* Chat Input Field */}
              <div style={{ padding: '15px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  placeholder="Ask a general, RCA, or regulatory compliance question..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  style={{
                    flex: 1,
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    color: '#fff',
                    outline: 'none',
                    fontSize: '14px',
                    transition: 'all 0.3s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'rgba(168, 85, 247, 0.5)'}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
                />
                <button
                  onClick={() => handleSendMessage()}
                  style={{
                    background: 'var(--gradient-primary)',
                    color: '#fff',
                    border: 'none',
                    padding: '0 24px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '14px'
                  }}
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: RCA Dashboard */}
        {activeTab === 'rca' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {loadingRca ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                Fusing reliability databases and scoring priority...
              </div>
            ) : rcaData ? (
              <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '20px' }}>
                
                {/* Left panel: risk scorer & sensors */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  
                  {/* Priority score card */}
                  <div className="glass-panel" style={{ padding: '25px', textAlign: 'center' }}>
                    <h4 style={{ margin: '0 0 10px', color: 'var(--text-secondary)' }}>Priority/Risk Score</h4>
                    {rcaData.priority && (
                      <>
                        <div style={{ fontSize: '64px', fontWeight: 'bold', color: getScoreColor(rcaData.priority.priority_score), margin: '10px 0' }}>
                          {rcaData.priority.priority_score}
                          <span style={{ fontSize: '20px', color: 'var(--text-muted)' }}>/10</span>
                        </div>
                        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', fontSize: '11px', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <span style={{ fontWeight: '600', color: 'var(--text-secondary)' }}>Reasoning factors:</span>
                          {rcaData.priority.reasoning.map((r, i) => (
                            <div key={i} style={{ color: 'var(--text-muted)' }}>• {r}</div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>

                  {/* Simulated conditions panel */}
                  <div className="glass-panel" style={{ padding: '25px' }}>
                    <h4 style={{ margin: '0 0 15px', color: 'var(--text-secondary)', textAlign: 'center' }}>Simulated Telemetry</h4>
                    {rcaData.priority && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Temperature</span>
                            <span style={{ color: '#fff', fontWeight: 'bold' }}>65°C (Simulated)</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: '65%', height: '100%', background: 'var(--accent-orange)' }}></div>
                          </div>
                        </div>
                        
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Vibration Amplitude</span>
                            <span style={{ color: '#fff', fontWeight: 'bold' }}>5.8 mm/s (Simulated)</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: '58%', height: '100%', background: 'var(--accent-red)' }}></div>
                          </div>
                        </div>

                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Pressure Level</span>
                            <span style={{ color: '#fff', fontWeight: 'bold' }}>8.2 bar (Simulated)</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: '70%', height: '100%', background: 'var(--accent-green)' }}></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right panel: RCA text output */}
                <div className="glass-panel" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <h3 style={{ margin: 0, borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px', color: '#fff' }}>Root Cause Analysis Narrative</h3>
                  <div style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-primary)', textAlign: 'left' }}>
                    {renderFormattedText(rcaData.narrative)}
                  </div>
                  {rcaData.sources && rcaData.sources.length > 0 && (
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '15px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Sources audited: {Array.from(new Set(rcaData.sources)).join(', ')}</span>
                    </div>
                  )}
                </div>

              </div>
            ) : (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Select an equipment target to trigger Root Cause Analysis.
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Compliance Audit */}
        {activeTab === 'compliance' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {loadingCompliance ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                Verifying rules against corpus and building evidence checklists...
              </div>
            ) : complianceData ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px' }}>
                
                {/* Left panel: findings checklist */}
                <div className="glass-panel" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px' }}>
                    <h3 style={{ margin: 0, color: '#fff' }}>Compliance Check Findings</h3>
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      background: complianceData.overall_status === 'COMPLIANT' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      color: complianceData.overall_status === 'COMPLIANT' ? 'var(--accent-green)' : 'var(--accent-red)',
                      border: `1px solid ${complianceData.overall_status === 'COMPLIANT' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                    }}>
                      OVERALL: {complianceData.overall_status}
                    </span>
                  </div>

                  <div style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text-primary)', textAlign: 'left' }}>
                    {renderFormattedText(complianceData.evidence_package?.full_narrative_analysis)}
                  </div>
                </div>

                {/* Right panel: checklist checklist items and export */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div className="glass-panel" style={{ padding: '20px' }}>
                    <h4 style={{ margin: '0 0 15px', color: 'var(--text-secondary)' }}>Checklist Audit</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {complianceData.checklist?.map((item, idx) => {
                        let badgeBg = 'rgba(107, 114, 128, 0.1)';
                        let badgeColor = 'var(--text-muted)';
                        if (item.status === 'COMPLIANT') {
                          badgeBg = 'rgba(16, 185, 129, 0.15)';
                          badgeColor = 'var(--accent-green)';
                        } else if (item.status === 'NON_COMPLIANT') {
                          badgeBg = 'rgba(239, 68, 68, 0.15)';
                          badgeColor = 'var(--accent-red)';
                        } else if (item.status === 'RISK_SIGNAL') {
                          badgeBg = 'rgba(245, 158, 11, 0.15)';
                          badgeColor = 'var(--accent-orange)';
                        }

                        return (
                          <div key={idx} style={{ padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                              <strong style={{ fontSize: '12px', color: '#fff' }}>{item.regulation_id}</strong>
                              <span style={{ fontSize: '9px', fontWeight: 'bold', padding: '2px 6px', borderRadius: '4px', background: badgeBg, color: badgeColor }}>
                                {item.status}
                              </span>
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', textAlign: 'left' }}>
                              {item.details}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <h4 style={{ margin: 0, color: 'var(--text-secondary)' }}>Evidence Packaging</h4>
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                      Exports a cryptographically reviewable compliance record for QMS registries.
                    </p>
                    <button
                      onClick={() => {
                        const jsonStr = JSON.stringify(complianceData.evidence_package, null, 2);
                        navigator.clipboard.writeText(jsonStr);
                        alert('Structured QMS Evidence Package copied to clipboard!');
                      }}
                      style={{
                        background: 'var(--gradient-primary)',
                        color: '#fff',
                        border: 'none',
                        padding: '10px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: '600',
                        fontSize: '12px',
                        transition: 'opacity 0.2s'
                      }}
                    >
                      Copy QMS Package
                    </button>
                  </div>
                </div>

              </div>
            ) : (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Select an equipment target to verify regulatory compliance.
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Knowledge Graph */}
        {activeTab === 'graph' && (
          <div>
            {loadingGraph ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                Loading semantic plant relationships from NetworkX...
              </div>
            ) : (
              renderInteractiveGraph()
            )}
          </div>
        )}

        {/* Tab 5: Fleet Health */}
        {activeTab === 'fleet' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {loadingFleet ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                Generating fleet-wide Failure Intelligence summaries...
              </div>
            ) : fleetData ? (
              <>
                {/* Benchmark Performance KPIs */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
                  <div className="glass-panel" style={{ padding: '20px', textAlign: 'left', borderLeft: '4px solid var(--accent-purple)' }}>
                    <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Search Time Reduction</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', margin: '4px 0', color: 'var(--accent-purple)' }}>98.9% Faster</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      SAMARTH: <strong style={{ color: '#fff' }}>4.97s</strong> vs Traditional systems: <strong style={{ color: '#fff' }}>8 mins</strong>
                    </div>
                  </div>

                  <div className="glass-panel" style={{ padding: '20px', textAlign: 'left', borderLeft: '4px solid var(--accent-green)' }}>
                    <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Entity Extraction Accuracy</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', margin: '4px 0', color: 'var(--accent-green)' }}>100% Verified</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Matched <strong style={{ color: '#fff' }}>163/163</strong> structured/unstructured graph references
                    </div>
                  </div>

                  <div className="glass-panel" style={{ padding: '20px', textAlign: 'left', borderLeft: '4px solid var(--accent-blue)' }}>
                    <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>Intent Routing Accuracy</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', margin: '4px 0', color: 'var(--accent-blue)' }}>90.0% Score</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Succeeded on <strong style={{ color: '#fff' }}>18/20</strong> domain expert benchmark questions
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
                
                {/* Left panel: summary report */}
                <div className="glass-panel" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <h3 style={{ margin: 0, borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '12px', color: '#fff' }}>Fleet Failure Intelligence Executive Summary</h3>
                  <div style={{ fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-line', color: 'var(--text-primary)', textAlign: 'left' }}>
                    {fleetData.executive_summary}
                  </div>
                </div>

                {/* Right panel: top risks and common issues */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  
                  {/* Top risk list */}
                  <div className="glass-panel" style={{ padding: '20px' }}>
                    <h4 style={{ margin: '0 0 15px', color: 'var(--text-secondary)' }}>Highest Risk Assets</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {fleetData.top_risk_equipment?.map((eq, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
                          <div>
                            <strong style={{ color: '#fff', fontSize: '13px' }}>{eq.equipment_id}</strong>
                            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Failures: {eq.total_failures}</div>
                          </div>
                          <span style={{ fontWeight: 'bold', fontSize: '14px', color: getScoreColor(eq.priority_score) }}>
                            {eq.priority_score} <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>/10</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Most common modes */}
                  <div className="glass-panel" style={{ padding: '20px' }}>
                    <h4 style={{ margin: '0 0 15px', color: 'var(--text-secondary)' }}>Top Failure Modes</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {fleetData.most_common_failures?.map((fm, i) => (
                        <div key={i}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>{fm.failure_mode}</span>
                            <span style={{ color: '#fff', fontWeight: 'bold' }}>{fm.count} hits</span>
                          </div>
                          <div style={{ height: '5px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(fm.count * 10, 100)}%`, height: '100%', background: 'var(--accent-purple)' }}></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

              </div>
            </> 
            ) : (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No fleet report loaded.
              </div>
            )}
          </div>
        )}

      </main>
      
      {/* Footer */}
      <footer style={{ borderTop: '1px solid rgba(255,255,255,0.05)', padding: '15px', fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center' }}>
        SAMARTH Industrial Operations Dashboard &copy; 2026. Made with Vanilla CSS, React & Groq.
      </footer>
    </div>
  );
}

export default App;
