import React, { useState, useEffect, useRef } from 'react';
import { Send, FileText, RefreshCw, Search, Link2, FileSearch, CheckSquare, Square, BookOpen, Zap, Menu, X } from 'lucide-react';

const API_URL = 'http://localhost:5000';

function usePDFManager() {
  const [pdfs, setPdfs] = useState([]);
  const [selectedPdfs, setSelectedPdfs] = useState([]);
  const [status, setStatus] = useState('disconnected');
  const [error, setError] = useState(null);

  useEffect(() => {
    checkHealth();
    loadPDFs();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      const data = await response.json();
      setStatus(data.status === 'healthy' ? 'connected' : 'disconnected');
    } catch (err) {
      setStatus('disconnected');
      setError('Cannot connect to backend server');
    }
  };

  const loadPDFs = async () => {
    try {
      const response = await fetch(`${API_URL}/api/pdfs`);
      const data = await response.json();
      if (data.success) {
        setPdfs(data.pdfs);
        setSelectedPdfs(data.pdfs.map(pdf => pdf.name));
        setError(null);
      }
    } catch (err) {
      setError('Failed to load PDFs');
    }
  };

  const reloadPDFs = async () => {
    try {
      const response = await fetch(`${API_URL}/api/reload`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        await loadPDFs();
        return { success: true, count: data.count };
      }
    } catch (err) {
      setError('Failed to reload PDFs');
      return { success: false };
    }
  };

  const togglePdfSelection = (pdfName) => {
    setSelectedPdfs(prev =>
      prev.includes(pdfName)
        ? prev.filter(name => name !== pdfName)
        : [...prev, pdfName]
    );
  };

  const selectAll = () => setSelectedPdfs(pdfs.map(pdf => pdf.name));
  const deselectAll = () => setSelectedPdfs([]);

  return {
    pdfs,
    selectedPdfs,
    status,
    error,
    setError,
    loadPDFs,
    reloadPDFs,
    togglePdfSelection,
    selectAll,
    deselectAll
  };
}

function useChatManager() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const askQuestion = async (question, selectedPdfs, mode = 'normal') => {
    const userMessage = { type: 'user', text: question, selectedPdfs };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, mode, selected_pdfs: selectedPdfs })
      });

      const data = await response.json();
      
      if (data.success) {
        setMessages(prev => [...prev, {
          type: 'assistant',
          text: data.answer,
          sources: data.sources,
          mode: mode
        }]);
      }
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const addSystemMessage = (text) => {
    setMessages(prev => [...prev, { type: 'system', text }]);
  };

  return { messages, loading, messagesEndRef, askQuestion, addSystemMessage };
}

function Sidebar({ pdfs, selectedPdfs, onToggle, onSelectAll, onDeselectAll, onReload, loading, isOpen, onClose }) {
  return (
    <>
      <div className={`fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden ${isOpen ? 'block' : 'hidden'}`} onClick={onClose}></div>
      <div className={`fixed lg:static inset-y-0 left-0 w-80 bg-white border-r border-gray-200 z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} flex flex-col h-screen`}>
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Library</h2>
            <button onClick={onClose} className="lg:hidden p-2 hover:bg-gray-100 rounded-lg">
              <X size={20} />
            </button>
          </div>
          <div className="flex gap-2 mb-4">
            <button
              onClick={onSelectAll}
              className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Select All
            </button>
            <button
              onClick={onDeselectAll}
              className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Clear
            </button>
            <button
              onClick={onReload}
              disabled={loading}
              className="p-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
          <div className="text-xs text-gray-600">
            {selectedPdfs.length} of {pdfs.length} selected
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {pdfs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <BookOpen size={48} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">No documents</p>
            </div>
          ) : (
            <div className="p-4 space-y-2">
              {pdfs.map((pdf, idx) => {
                const isSelected = selectedPdfs.includes(pdf.name);
                return (
                  <button
                    key={idx}
                    onClick={() => onToggle(pdf.name)}
                    className={`w-full p-4 rounded-lg border transition-all text-left ${
                      isSelected 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        {isSelected ? (
                          <CheckSquare size={18} className="text-blue-600" />
                        ) : (
                          <Square size={18} className="text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-2 mb-2">
                          <div className="w-12 h-16 bg-gradient-to-br from-gray-100 to-gray-200 rounded border border-gray-300 flex items-center justify-center flex-shrink-0">
                            <FileText size={20} className="text-gray-500" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className={`text-sm font-medium mb-1 line-clamp-2 ${
                              isSelected ? 'text-blue-900' : 'text-gray-900'
                            }`}>
                              {pdf.name}
                            </h3>
                            <p className="text-xs text-gray-500">
                              {pdf.pages} pages
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function QuickActions({ onAction, disabled, selectedCount }) {
  const actions = [
    { 
      id: 'connections', 
      icon: Link2, 
      label: 'Find Connections',
      color: 'from-purple-500 to-purple-600',
      prompt: 'Analyze the selected documents and identify key connections, relationships, and patterns between them.'
    },
    { 
      id: 'summary', 
      icon: FileSearch, 
      label: 'Summarize All',
      color: 'from-blue-500 to-blue-600',
      prompt: 'Provide a comprehensive summary of the selected documents, highlighting main topics and key findings.'
    },
    { 
      id: 'insights', 
      icon: Zap, 
      label: 'Key Insights',
      color: 'from-amber-500 to-amber-600',
      prompt: 'Extract the most important insights and observations from the selected documents.'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {actions.map(action => (
        <button
          key={action.id}
          onClick={() => onAction(action.prompt)}
          disabled={disabled || selectedCount === 0}
          className={`p-6 rounded-xl bg-gradient-to-br ${action.color} text-white hover:shadow-lg transform hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none text-left`}
        >
          <action.icon size={28} className="mb-3" />
          <h3 className="font-semibold text-lg">{action.label}</h3>
        </button>
      ))}
    </div>
  );
}

function MessageBubble({ message }) {
  const formatText = (text) => {
    const lines = text.split('\n');
    return lines.map((line, i) => {
      if (line.match(/^\d+\./)) {
        return <li key={i} className="ml-4 mb-2">{line.replace(/^\d+\.\s*/, '')}</li>;
      }
      if (line.match(/^[•\-\*]/)) {
        return <li key={i} className="ml-4 mb-2">{line.replace(/^[•\-\*]\s*/, '')}</li>;
      }
      if (line.match(/^#{1,3}\s/)) {
        const level = line.match(/^#{1,3}/)[0].length;
        const text = line.replace(/^#{1,3}\s*/, '');
        const className = level === 1 ? 'text-xl font-bold mt-4 mb-2' : level === 2 ? 'text-lg font-semibold mt-3 mb-2' : 'text-base font-medium mt-2 mb-1';
        return <div key={i} className={className}>{text}</div>;
      }
      if (line.match(/^\*\*.*\*\*$/)) {
        return <div key={i} className="font-semibold my-2">{line.replace(/\*\*/g, '')}</div>;
      }
      return line ? <p key={i} className="mb-2">{line}</p> : <br key={i} />;
    });
  };

  if (message.type === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-5 py-3 shadow-sm">
          <p className="text-sm whitespace-pre-wrap">{message.text}</p>
        </div>
      </div>
    );
  }

  if (message.type === 'system') {
    return (
      <div className="flex justify-center mb-4">
        <div className="bg-green-50 text-green-800 border border-green-200 rounded-lg px-4 py-2 text-sm">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%]">
        <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
          <div className="prose prose-sm max-w-none text-gray-900">
            {formatText(message.text)}
          </div>
          {message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs font-medium text-gray-700 mb-2">Sources:</p>
              <div className="flex flex-wrap gap-2">
                {message.sources.map((source, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                    <FileText size={12} />
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const pdfManager = usePDFManager();
  const chatManager = useChatManager();
  const [question, setQuestion] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleReload = async () => {
    const result = await pdfManager.reloadPDFs();
    if (result.success) {
      chatManager.addSystemMessage(`Successfully reloaded ${result.count} documents`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || chatManager.loading || pdfManager.selectedPdfs.length === 0) return;
    
    await chatManager.askQuestion(question, pdfManager.selectedPdfs);
    setQuestion('');
  };

  const handleAnalyze = async (prompt) => {
    await chatManager.askQuestion(prompt, pdfManager.selectedPdfs, 'analysis');
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        pdfs={pdfManager.pdfs}
        selectedPdfs={pdfManager.selectedPdfs}
        onToggle={pdfManager.togglePdfSelection}
        onSelectAll={pdfManager.selectAll}
        onDeselectAll={pdfManager.deselectAll}
        onReload={handleReload}
        loading={chatManager.loading}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
            >
              <Menu size={24} />
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">PDF Analysis Assistant</h1>
              <p className="text-sm text-gray-600">AI-powered document insights</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${pdfManager.status === 'connected' ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600 hidden sm:inline">
              {pdfManager.status === 'connected' ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <QuickActions
            onAction={handleAnalyze}
            disabled={chatManager.loading}
            selectedCount={pdfManager.selectedPdfs.length}
          />

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            {chatManager.messages.length === 0 ? (
              <div className="p-16 text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <Search size={40} className="text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  Hello! How can I help you today?
                </h2>
                <p className="text-gray-600 max-w-md mx-auto mb-6">
                  I'm your AI assistant. I can analyze your documents, find connections, provide summaries, and answer your questions.
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-xs">
                  <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full">Summarize documents</span>
                  <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full">Find connections</span>
                  <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full">Extract insights</span>
                  <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full">Answer questions</span>
                </div>
              </div>
            ) : (
              <div className="p-6 max-h-[500px] overflow-y-auto">
                {chatManager.messages.map((msg, idx) => (
                  <MessageBubble key={idx} message={msg} />
                ))}
                {chatManager.loading && (
                  <div className="flex justify-start mb-4">
                    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.15s'}}></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.3s'}}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatManager.messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            {pdfManager.selectedPdfs.length === 0 && (
              <div className="mb-3 text-sm text-amber-600 text-center">
                Please select at least one document from the library
              </div>
            )}
            <div className="flex gap-3">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit(e)}
                placeholder="Ask me anything..."
                disabled={chatManager.loading || pdfManager.selectedPdfs.length === 0}
                className="flex-1 px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900 placeholder-gray-500"
              />
              <button
                onClick={handleSubmit}
                disabled={chatManager.loading || !question.trim() || pdfManager.selectedPdfs.length === 0}
                className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 font-medium shadow-sm"
              >
                <Send size={18} />
                <span className="hidden sm:inline">Send</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}