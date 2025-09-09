import React from 'react';
import AgentTraceSimulator from './components/AgentTrace';

const AgentTraceApp: React.FC = () => {
  return (
    <div className="bg-gray-900 text-white min-h-screen font-mono">
      <div className="max-w-6xl mx-auto p-4">
        <h1 className="text-2xl font-bold text-gray-300 mb-2">
          Google ADK Agent Execution Trace
        </h1>
        <p className="text-gray-400 mb-4 text-sm">
          Visualization of the Google Agent Development Kit (ADK) flow showing API requests, session management, 
          agent processing, tool calls, and responses in a terminal-like interface.
        </p>
        <div className="mb-4 text-xs text-gray-500">
          <div className="flex items-center mb-1">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-400 mr-2"></span>
            <span>API Request/Response</span>
          </div>
          <div className="flex items-center mb-1">
            <span className="inline-block w-3 h-3 rounded-full bg-purple-400 mr-2"></span>
            <span>Session Management</span>
          </div>
          <div className="flex items-center mb-1">
            <span className="inline-block w-3 h-3 rounded-full bg-cyan-400 mr-2"></span>
            <span>Agent Processing</span>
          </div>
          <div className="flex items-center mb-1">
            <span className="inline-block w-3 h-3 rounded-full bg-yellow-400 mr-2"></span>
            <span>Tool Calls</span>
          </div>
          <div className="flex items-center">
            <span className="inline-block w-3 h-3 rounded-full bg-green-400 mr-2"></span>
            <span>User/Agent Messages</span>
          </div>
        </div>
        <AgentTraceSimulator />
      </div>
    </div>
  );
};

export default AgentTraceApp;