import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar, NavTab } from './components/Sidebar';
import { ColdStartModal } from './components/ColdStartModal';
import { OptimizerPage } from './pages/OptimizerPage';
import { PredictorPage } from './pages/PredictorPage';
import { ScenariosPage } from './pages/ScenariosPage';
import { BenchmarksPage } from './pages/BenchmarksPage';
import { CaseStudiesPage } from './pages/CaseStudiesPage';
import { ApiDocsPage } from './pages/ApiDocsPage';
import { api } from './lib/api';
import { ConnectionStatus, CaseStudy } from './types';
import './styles/theme.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('optimizer');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('online');
  const [isLocalMode, setIsLocalMode] = useState<boolean>(false);
  const [isColdStartOpen, setIsColdStartOpen] = useState<boolean>(false);
  const [coldStartAttempt, setColdStartAttempt] = useState<number>(1);
  const [presetToLoad, setPresetToLoad] = useState<CaseStudy | null>(null);

  const checkConnection = async () => {
    try {
      await api.checkHealth();
      setConnectionStatus('online');
      setIsColdStartOpen(false);
    } catch {
      setConnectionStatus('offline');
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  const handleTriggerColdStart = (attempt: number) => {
    setColdStartAttempt(attempt);
    setIsColdStartOpen(true);
    setConnectionStatus('waking_up');
  };

  const handleSwitchToLocal = () => {
    setIsLocalMode(true);
    setIsColdStartOpen(false);
  };

  const handleLoadPreset = (preset: CaseStudy) => {
    setPresetToLoad(preset);
    setActiveTab('optimizer');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header
        status={connectionStatus}
        isLocalMode={isLocalMode}
        onRetryConnection={checkConnection}
      />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

        <main style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', backgroundColor: 'var(--bg-app)' }}>
          {activeTab === 'optimizer' && (
            <OptimizerPage
              isLocalMode={isLocalMode}
              onTriggerColdStart={handleTriggerColdStart}
              presetToLoad={presetToLoad}
            />
          )}
          {activeTab === 'predictor' && <PredictorPage isLocalMode={isLocalMode} />}
          {activeTab === 'scenarios' && <ScenariosPage isLocalMode={isLocalMode} />}
          {activeTab === 'benchmarks' && <BenchmarksPage isLocalMode={isLocalMode} />}
          {activeTab === 'case-studies' && <CaseStudiesPage onLoadPreset={handleLoadPreset} />}
          {activeTab === 'api' && <ApiDocsPage />}
        </main>
      </div>

      <ColdStartModal
        isOpen={isColdStartOpen}
        attempt={coldStartAttempt}
        onSwitchToLocal={handleSwitchToLocal}
      />
    </div>
  );
};

export default App;
