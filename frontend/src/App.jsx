import React, { useState } from 'react';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import Dashboard from './components/dashboard/Dashboard';
import History from './components/history/History';
import ModelWorkbench from './components/models/ModelWorkbench';
import Documentation from './components/docs/Documentation';
import Home from './components/home/Home';
import Settings from './components/settings/Settings';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('sim_history');
    return saved ? JSON.parse(saved) : [];
  });

  const addToHistory = (params, results) => {
    const newEntry = {
      timestamp: new Date().toISOString(),
      params,
      results
    };
    const updatedHistory = [...history, newEntry].slice(-50); // Keep last 50
    setHistory(updatedHistory);
    localStorage.setItem('sim_history', JSON.stringify(updatedHistory));
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('sim_history');
  };

  const renderContent = () => {
    switch (currentPage) {
      case 'home':
        return <Home onNavigate={setCurrentPage} />;
      case 'dashboard':
        return <Dashboard onSimulationComplete={addToHistory} />;
      case 'benchmarks':
        return <History history={history} onClearHistory={clearHistory} />;
      case 'models':
        return <ModelWorkbench />;
      case 'docs':
        return <Documentation />;
      case 'settings':
        return <Settings />;
      default:
        return <Home onNavigate={setCurrentPage} />;
    }
  };

  if (currentPage === 'home') {
    return (
      <div className="bg-background text-text-main font-sans scrollbar-none">
        {renderContent()}
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background text-text-main overflow-hidden font-sans">
      <Sidebar activePage={currentPage} onNavigate={setCurrentPage} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-auto p-6 scrollbar-thin">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;
