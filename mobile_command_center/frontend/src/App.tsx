import React, { useState, useEffect } from 'react';
import { Activity, Server, Zap, AlertCircle, MessageSquare, Settings } from 'lucide-react';

// Types
interface Agent {
  agent_id: string;
  name: string;
  type: string;
  status: string;
  health: string;
  port?: number;
  description: string;
}

interface Alert {
  alert_id: string;
  severity: string;
  node_id: string;
  message: string;
  timestamp: string;
}

// API Configuration
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8003';

function App() {
  const [activeTab, setActiveTab] = useState<string>('agents');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  // Fetch agents
  useEffect(() => {
    if (!token) return;

    const fetchAgents = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/agents`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setAgents(data.agents || []);
        }
      } catch (error) {
        console.error('Error fetching agents:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 10000); // Refresh every 10s

    return () => clearInterval(interval);
  }, [token]);

  // Fetch alerts
  useEffect(() => {
    if (!token) return;

    const fetchAlerts = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/alerts`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setAlerts(data.alerts || []);
        }
      } catch (error) {
        console.error('Error fetching alerts:', error);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 15000); // Refresh every 15s

    return () => clearInterval(interval);
  }, [token]);

  // Login
  const handleLogin = async (username: string, password: string) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
      } else {
        alert('Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login error');
    }
  };

  // Login screen
  if (!token) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-6 h-6 text-yellow-400" />
            <h1 className="text-xl font-bold">Prime Spark</h1>
          </div>
          <div className="flex items-center space-x-2">
            {alerts.length > 0 && (
              <button className="relative">
                <AlertCircle className="w-6 h-6 text-red-500" />
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {alerts.length}
                </span>
              </button>
            )}
            <Settings className="w-6 h-6" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-4 pb-20">
        {activeTab === 'agents' && <AgentsView agents={agents} loading={loading} />}
        {activeTab === 'infrastructure' && <InfrastructureView />}
        {activeTab === 'alerts' && <AlertsView alerts={alerts} />}
        {activeTab === 'chat' && <ChatView token={token} />}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700">
        <div className="flex justify-around items-center h-16">
          <NavButton
            icon={<Activity className="w-6 h-6" />}
            label="Agents"
            active={activeTab === 'agents'}
            onClick={() => setActiveTab('agents')}
          />
          <NavButton
            icon={<Server className="w-6 h-6" />}
            label="Infrastructure"
            active={activeTab === 'infrastructure'}
            onClick={() => setActiveTab('infrastructure')}
          />
          <NavButton
            icon={<AlertCircle className="w-6 h-6" />}
            label="Alerts"
            active={activeTab === 'alerts'}
            onClick={() => setActiveTab('alerts')}
            badge={alerts.length}
          />
          <NavButton
            icon={<MessageSquare className="w-6 h-6" />}
            label="Chat"
            active={activeTab === 'chat'}
            onClick={() => setActiveTab('chat')}
          />
        </div>
      </nav>
    </div>
  );
}

// Login Screen Component
function LoginScreen({ onLogin }: { onLogin: (username: string, password: string) => void }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin(username, password);
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <Zap className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-white mb-2">Prime Spark</h1>
          <p className="text-gray-400">Mobile Command Center</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
              placeholder="admin"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
              placeholder="Enter password"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold py-3 rounded-lg transition"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}

// Nav Button Component
function NavButton({ icon, label, active, onClick, badge }: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  badge?: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center space-y-1 px-4 py-2 relative ${
        active ? 'text-yellow-400' : 'text-gray-400'
      }`}
    >
      {icon}
      <span className="text-xs">{label}</span>
      {badge && badge > 0 && (
        <span className="absolute top-0 right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          {badge}
        </span>
      )}
    </button>
  );
}

// Agents View Component
function AgentsView({ agents, loading }: { agents: Agent[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold mb-4">Agents</h2>

      {agents.map((agent) => (
        <div key={agent.agent_id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                agent.status === 'running' ? 'bg-green-500' :
                agent.status === 'stopped' ? 'bg-gray-500' : 'bg-red-500'
              }`}></div>
              <h3 className="font-semibold">{agent.name}</h3>
            </div>
            <span className={`text-xs px-2 py-1 rounded ${
              agent.health === 'healthy' ? 'bg-green-500/20 text-green-400' :
              agent.health === 'degraded' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {agent.health}
            </span>
          </div>

          <p className="text-sm text-gray-400 mb-3">{agent.description}</p>

          <div className="flex space-x-2">
            <button className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm py-2 rounded transition">
              Start
            </button>
            <button className="flex-1 bg-red-600 hover:bg-red-700 text-white text-sm py-2 rounded transition">
              Stop
            </button>
            <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 rounded transition">
              Logs
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// Infrastructure View Component
function InfrastructureView() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold mb-4">Infrastructure</h2>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h3 className="font-semibold mb-3">Edge Node</h3>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Pi 5</span>
            <span className="text-green-400">Operational</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">CPU</span>
            <span>24%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Memory</span>
            <span>42%</span>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h3 className="font-semibold mb-3">Cloud Nodes</h3>
        <div className="space-y-3">
          <NodeCard name="PrimeCore1" status="healthy" />
          <NodeCard name="PrimeCore4" status="healthy" />
        </div>
      </div>
    </div>
  );
}

function NodeCard({ name, status }: { name: string; status: string }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${
          status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
        }`}></div>
        <span className="text-sm">{name}</span>
      </div>
      <span className="text-xs text-gray-400 capitalize">{status}</span>
    </div>
  );
}

// Alerts View Component
function AlertsView({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold mb-4">Alerts</h2>

      {alerts.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-8 text-center border border-gray-700">
          <AlertCircle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400">No active alerts</p>
        </div>
      ) : (
        alerts.map((alert) => (
          <div key={alert.alert_id} className="bg-gray-800 rounded-lg p-4 border-l-4 border-red-500">
            <div className="flex items-center justify-between mb-2">
              <span className={`text-xs px-2 py-1 rounded ${
                alert.severity === 'critical' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
              }`}>
                {alert.severity}
              </span>
              <span className="text-xs text-gray-400">{alert.node_id}</span>
            </div>
            <p className="text-sm">{alert.message}</p>
            <button className="mt-3 text-xs text-blue-400 hover:text-blue-300">
              Acknowledge
            </button>
          </div>
        ))
      )}
    </div>
  );
}

// Chat View Component
function ChatView({ token }: { token: string }) {
  const [messages, setMessages] = useState<Array<{role: string; content: string}>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/llm/chat?prompt=${encodeURIComponent(input)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <h2 className="text-2xl font-bold mb-4">LLM Chat</h2>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-3" />
            <p>Start a conversation with Prime Spark AI</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg p-3 ${
              msg.role === 'user' ? 'bg-yellow-500 text-gray-900' : 'bg-gray-700 text-gray-100'
            }`}>
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask Prime Spark AI..."
          className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
        />
        <button
          onClick={handleSend}
          disabled={loading}
          className="px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold rounded-lg transition disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
