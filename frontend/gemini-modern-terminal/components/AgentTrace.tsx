import React, { useState, useEffect } from 'react';

// --- Helper Components for Terminal UI ---

const Spinner: React.FC = () => (
  <span className="inline-block w-2 h-4 bg-gray-200 animate-blink -mb-0.5 ml-0.5" />
);

const Icon: React.FC<{ type: 'request' | 'response' | 'session' | 'agent' | 'tool' | 'user' | 'model' | 'functionCall' | 'functionResponse' | 'graph' | 'error' | 'info' | 'select' | 'chat' }> = ({ type }) => {
  const icons = {
    request: { char: '➡️', color: 'text-blue-400', label: 'Request' },
    response: { char: '⬅️', color: 'text-green-400', label: 'Response' },
    session: { char: '🔌', color: 'text-purple-400', label: 'Session' },
    agent: { char: '🤖', color: 'text-cyan-400', label: 'Agent' },
    tool: { char: '🔧', color: 'text-yellow-400', label: 'Tool' },
    user: { char: '👤', color: 'text-blue-300', label: 'User' },
    model: { char: '🧠', color: 'text-purple-300', label: 'Model' },
    functionCall: { char: 'CALLTYPE', color: 'text-yellow-300', label: 'Tool Call' },
    functionResponse: { char: 'CALLTYPE', color: 'text-orange-300', label: 'Tool Response' },
    graph: { char: '📊', color: 'text-pink-400', label: 'Graph' },
    error: { char: '❌', color: 'text-red-400', label: 'Error' },
    info: { char: 'ℹ️', color: 'text-gray-400', label: 'Info' },
    select: { char: '🔍', color: 'text-yellow-400', label: 'Selection' },
    chat: { char: '💬', color: 'text-green-400', label: 'Chat' },
  };
  
  // Special handling for functionCall and functionResponse to show the actual type
  if (type === 'functionCall' || type === 'functionResponse') {
    return <span className={`mr-2 ${icons[type].color}`} title={icons[type].label}>{icons[type].char}</span>;
  }
  
  const { char, color, label } = icons[type];
  return <span className={`mr-2 ${color}`} title={label}>{char}</span>;
};

// --- Types for ADK Flow ---

interface TraceLine {
  id: number;
  type: 'request' | 'response' | 'session' | 'agent' | 'tool' | 'user' | 'model' | 'functionCall' | 'functionResponse' | 'graph' | 'error' | 'info' | 'select' | 'chat';
  indent: number;
  text: string | JSX.Element;
  status?: 'sending' | 'receiving' | 'done';
  isJson?: boolean;
  fullData?: any; // Store full data for detailed view
}

interface App {
  name: string;
}

interface Session {
  id: string;
  appName: string;
  userId: string;
  state: Record<string, any>;
  lastUpdateTime: number;
}

interface Event {
  id: string;
  role: string;
  parts: { text?: string }[];
  functionCall?: any;
  functionResponse?: any;
}

// --- Main Component ---

const AgentTraceSimulator: React.FC = () => {
  const [trace, setTrace] = useState<TraceLine[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [apps, setApps] = useState<App[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [sessionData, setSessionData] = useState<Session & { events: Event[] } | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<string | null>(null);
  const [detailedView, setDetailedView] = useState<any>(null);

  // Update time for terminal header
  useEffect(() => {
    const timerId = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timerId);
  }, []);

  // Format time for terminal header
  const time = currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  const date = currentTime.toLocaleDateString([], { day: '2-digit', month: 'short', year: 'numeric' });

  // Fetch available apps
  const fetchApps = async () => {
    setIsLoading(true);
    const newTrace: TraceLine[] = [];
    let currentId = 0;
    
    try {
      newTrace.push({
        id: currentId++,
        type: 'request',
        indent: 0,
        text: '> GET /api/list-apps?relative_path=./'
      });
      
      const appsResponse = await fetch('/api/list-apps?relative_path=./');
      const appsData: string[] = await appsResponse.json();
      
      newTrace.push({
        id: currentId++,
        type: 'response',
        indent: 0,
        text: (
          <div>
            <div className="text-green-400">← 200 OK</div>
            <div className="text-gray-300 mt-1">Available apps:</div>
            {appsData.map((app, index) => (
              <div key={index} className="text-gray-300 ml-4">• {app}</div>
            ))}
          </div>
        ),
        isJson: true
      });
      
      const appList = appsData.map(name => ({ name }));
      setApps(appList);
      
      setTrace(newTrace);
      setIsComplete(true);
    } catch (error) {
      setTrace([{
        id: currentId++,
        type: 'error',
        indent: 0,
        text: `❌ Error fetching apps: ${error instanceof Error ? error.message : 'Unknown error'}`
      }]);
      setIsComplete(true);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch sessions for selected app
  const fetchSessions = async (appName: string) => {
    setIsLoading(true);
    const newTrace: TraceLine[] = [];
    let currentId = 0;
    
    try {
      newTrace.push({
        id: currentId++,
        type: 'request',
        indent: 0,
        text: `> GET /api/apps/${appName}/users/user/sessions`
      });
      
      const sessionsResponse = await fetch(`/api/apps/${appName}/users/user/sessions`);
      const sessionsData: Session[] = await sessionsResponse.json();
      
      newTrace.push({
        id: currentId++,
        type: 'response',
        indent: 0,
        text: (
          <div>
            <div className="text-green-400">← 200 OK</div>
            <div className="text-gray-300 mt-1">Found {sessionsData.length} session(s):</div>
            {sessionsData.map((session, index) => (
              <div key={session.id} className="text-gray-300 ml-4">
                • {session.id} (Updated: {new Date(session.lastUpdateTime * 1000).toLocaleString()})
              </div>
            ))}
          </div>
        ),
        isJson: true,
        fullData: sessionsData
      });
      
      setSessions(sessionsData);
      setTrace(newTrace);
      setIsComplete(true);
    } catch (error) {
      setTrace([{
        id: currentId++,
        type: 'error',
        indent: 0,
        text: `❌ Error fetching sessions: ${error instanceof Error ? error.message : 'Unknown error'}`
      }]);
      setIsComplete(true);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch session details
  const fetchSessionDetails = async (appName: string, sessionId: string) => {
    setIsLoading(true);
    const newTrace: TraceLine[] = [];
    let currentId = 0;
    
    try {
      newTrace.push({
        id: currentId++,
        type: 'request',
        indent: 0,
        text: `> GET /api/apps/${appName}/users/user/sessions/${sessionId}`
      });
      
      const sessionResponse = await fetch(`/api/apps/${appName}/users/user/sessions/${sessionId}`);
      const sessionData = await sessionResponse.json();
      
      newTrace.push({
        id: currentId++,
        type: 'response',
        indent: 0,
        text: `← 200 OK (Session loaded)`,
        fullData: sessionData
      });
      
      setSessionData(sessionData);
      const sessionEvents = sessionData.events || [];
      setEvents(sessionEvents);
      
      // Process events for clean display
      sessionEvents.forEach((event, index) => {
        if (event.role === 'user') {
          const userMessage = event.parts?.map(part => part.text).join(' ') || '';
          newTrace.push({
            id: currentId++,
            type: 'user',
            indent: 0,
            text: (
              <div>
                <span className="text-blue-300">👤 User:</span>
                <div className="ml-4 text-gray-300 whitespace-pre-wrap">{userMessage}</div>
              </div>
            ),
            fullData: event
          });
        } else if (event.role === 'model') {
          const modelResponse = event.parts?.map(part => part.text).join(' ') || '';
          newTrace.push({
            id: currentId++,
            type: 'model',
            indent: 0,
            text: (
              <div>
                <span className="text-purple-300">🧠 Agent:</span>
                <div className="ml-4 text-gray-300 whitespace-pre-wrap">{modelResponse}</div>
              </div>
            ),
            fullData: event
          });
        } else if (event.functionCall) {
          newTrace.push({
            id: currentId++,
            type: 'functionCall',
            indent: 0,
            text: (
              <div>
                <span className="text-yellow-300">🔧 Tool Call:</span>
                <div className="ml-4 text-gray-300">{event.functionCall.name}</div>
                <div className="ml-6 text-gray-400 text-xs">
                  {JSON.stringify(event.functionCall.args, null, 2)}
                </div>
              </div>
            ),
            fullData: event
          });
        } else if (event.functionResponse) {
          const toolName = Object.keys(event.functionResponse)[0];
          newTrace.push({
            id: currentId++,
            type: 'functionResponse',
            indent: 0,
            text: (
              <div>
                <span className="text-yellow-300">🔧 Tool Response:</span>
                <div className="ml-4 text-gray-300">{toolName}</div>
                <div className="ml-6 text-gray-400 text-xs">
                  {JSON.stringify(event.functionResponse[toolName], null, 2)}
                </div>
              </div>
            ),
            fullData: event
          });
        }
      });
      
      setTrace(prev => [...prev, ...newTrace]);
      setIsComplete(true);
    } catch (error) {
      setTrace(prev => [...prev, {
        id: currentId++,
        type: 'error',
        indent: 0,
        text: `❌ Error fetching session details: ${error instanceof Error ? error.message : 'Unknown error'}`
      }]);
      setIsComplete(true);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch data when component mounts
  useEffect(() => {
    fetchApps();
  }, []);

  // Handle app selection
  const handleAppSelect = (appName: string) => {
    setSelectedApp(appName);
    setTrace(prev => [...prev, {
      id: prev.length,
      type: 'select',
      indent: 0,
      text: `🔍 Selected app: ${appName}`
    }]);
    fetchSessions(appName);
  };

  // Handle session selection
  const handleSessionSelect = (sessionId: string) => {
    setSelectedSession(sessionId);
    setTrace(prev => [...prev, {
      id: prev.length,
      type: 'select',
      indent: 0,
      text: `🔍 Selected session: ${sessionId}`
    }]);
    if (selectedApp) {
      fetchSessionDetails(selectedApp, sessionId);
    }
  };

  // Handle event selection for detailed view
  const handleEventSelect = (event: Event) => {
    setSelectedEvent(event.id);
    setDetailedView(event);
    setTrace(prev => [...prev, {
      id: prev.length,
      type: 'info',
      indent: 0,
      text: `🔍 Showing details for event: ${event.id}`
    }]);
  };

  // Close detailed view
  const closeDetailedView = () => {
    setSelectedEvent(null);
    setDetailedView(null);
    setTrace(prev => [...prev, {
      id: prev.length,
      type: 'info',
      indent: 0,
      text: '🔍 Closed detailed view'
    }]);
  };

  return (
    <div className="w-full bg-gray-900 flex flex-col rounded-lg border border-gray-700/50 shadow-2xl shadow-black/50">
      {/* Terminal Header */}
      <div className="flex-shrink-0 h-8 grid grid-cols-[1fr_auto_1fr] items-center px-3 bg-gray-800 border-b border-gray-700 rounded-t-lg">
        <div className="flex items-center space-x-2">
          <span className="h-3 w-3 rounded-full bg-red-500" aria-hidden="true"></span>
          <span className="h-3 w-3 rounded-full bg-yellow-500" aria-hidden="true"></span>
          <span className="h-3 w-3 rounded-full bg-green-500" aria-hidden="true"></span>
        </div>
        <div className="text-center text-sm text-gray-400 font-medium">
          user@adk-terminal
        </div>
        <div className="text-right text-xs text-gray-500 whitespace-nowrap">
          {`${date} ${time}`}
        </div>
      </div>

      {/* Terminal Body */}
      <div className="flex-grow p-4 overflow-y-auto text-sm font-mono">
        <div className="mb-2">
          <div className="flex items-center text-gray-400">
            <span className="text-green-500">➜</span>
            <span className="ml-2">ADK Agent Execution Trace</span>
          </div>
        </div>
        
        {/* App Selection */}
        {apps.length > 0 && !selectedApp && (
          <div className="mb-4">
            <div className="text-gray-300 mb-2">Available Apps (click to select):</div>
            <div className="space-y-1">
              {apps.map((app, index) => (
                <div 
                  key={index} 
                  className="cursor-pointer hover:bg-gray-800 p-2 rounded"
                  onClick={() => handleAppSelect(app.name)}
                >
                  <span className="text-cyan-400">├──</span> {app.name}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Session Selection */}
        {sessions.length > 0 && selectedApp && !selectedSession && (
          <div className="mb-4">
            <div className="text-gray-300 mb-2">Sessions for {selectedApp} (click to select):</div>
            <div className="space-y-1">
              {sessions.map((session, index) => (
                <div 
                  key={session.id} 
                  className="cursor-pointer hover:bg-gray-800 p-2 rounded"
                  onClick={() => handleSessionSelect(session.id)}
                >
                  <span className="text-purple-400">├──</span> {session.id} (Last updated: {new Date(session.lastUpdateTime * 1000).toLocaleString()})
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Trace Output */}
        <div className="space-y-2">
          {trace.map(line => (
            <div 
              key={line.id} 
              style={{ paddingLeft: `${line.indent * 1.5}rem` }} 
              className={`flex items-start ${line.fullData ? 'cursor-pointer hover:bg-gray-800/50 p-1 rounded' : ''}`}
              onClick={() => {
                // If this line has associated full data, show it in detailed view
                if (line.fullData) {
                  setDetailedView(line.fullData);
                }
              }}
            >
              <div><Icon type={line.type} /></div>
              <div className="flex-1">
                {typeof line.text === 'string' ? (
                  <span className={
                    line.type === 'response' ? 'text-green-300 font-semibold' :
                    line.type === 'user' ? 'text-blue-300' :
                    line.type === 'model' ? 'text-purple-300' :
                    line.type === 'functionCall' || line.type === 'functionResponse' ? 'text-yellow-300' :
                    line.type === 'error' ? 'text-red-400' :
                    'text-gray-300'
                  }>
                    {line.text}
                  </span>
                ) : (
                  <div className="text-gray-300">{line.text}</div>
                )}
                {line.status === 'sending' && <Spinner />}
              </div>
            </div>
          ))}
        </div>

        {/* Detailed View */}
        {detailedView && (
          <div className="mt-4 bg-gray-800/50 p-4 rounded-md border border-gray-700">
            <div className="flex justify-between items-center mb-2">
              <div className="text-gray-300 font-semibold">Event Details</div>
              <button 
                onClick={closeDetailedView}
                className="text-gray-400 hover:text-gray-200"
              >
                ✕ Close
              </button>
            </div>
            <pre className="text-gray-300 text-xs overflow-x-auto">
              {JSON.stringify(detailedView, null, 2)}
            </pre>
          </div>
        )}

        {/* Prompt */}
        <div className="flex items-center mt-2">
          <span className="text-green-500">➜</span>
          <span className="ml-2 text-gray-300 flex-1">
            {isLoading ? 'Processing...' : 
             isComplete ? '✅ Ready' : 'Waiting for selection...'}
          </span>
          {isLoading && <span className="inline-block w-2 h-4 bg-gray-200 animate-blink -mb-0.5 ml-0.5" />}
        </div>
        
        {/* Control buttons */}
        <div className="mt-2 flex flex-wrap gap-2">
          <button 
            onClick={fetchApps}
            disabled={isLoading}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-gray-300 rounded text-sm font-mono"
          >
            {isLoading ? '🔄 Refreshing...' : '🔄 Refresh Apps'}
          </button>
          
          {selectedApp && (
            <button 
              onClick={() => fetchSessions(selectedApp)}
              disabled={isLoading}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-gray-300 rounded text-sm font-mono"
            >
              {isLoading ? '🔄 Refreshing...' : '🔄 Refresh Sessions'}
            </button>
          )}
          
          {selectedSession && (
            <button 
              onClick={() => fetchSessionDetails(selectedApp, selectedSession)}
              disabled={isLoading}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-gray-300 rounded text-sm font-mono"
            >
              {isLoading ? '🔄 Refresh Session' : '🔄 Refresh Chat'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentTraceSimulator;