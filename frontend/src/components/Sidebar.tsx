import React from 'react';
import { Ship, Gauge, Fuel, LineChart, Bookmark, Terminal } from 'lucide-react';

export type NavTab = 'optimizer' | 'predictor' | 'scenarios' | 'benchmarks' | 'case-studies' | 'api';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'optimizer', label: 'Fleet Optimizer', icon: <Ship size={16} /> },
    { id: 'predictor', label: 'Fuel Predictor', icon: <Gauge size={16} /> },
    { id: 'scenarios', label: 'Fuel Scenarios', icon: <Fuel size={16} /> },
    { id: 'benchmarks', label: 'Benchmarks', icon: <LineChart size={16} /> },
    { id: 'case-studies', label: 'Case Studies', icon: <Bookmark size={16} /> },
    { id: 'api', label: 'API & Diagnostics', icon: <Terminal size={16} /> }
  ];

  return (
    <aside
      style={{
        width: '210px',
        backgroundColor: 'var(--bg-panel)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '16px 0',
        userSelect: 'none'
      }}
    >
      <div>
        <div style={{ padding: '0 16px 12px 16px', fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.6px' }}>
          WORKSPACES
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '9px 16px',
                  width: '100%',
                  background: isActive ? 'var(--color-dark-spruce)' : 'transparent',
                  color: isActive ? 'var(--color-lime-cream)' : 'var(--text-main)',
                  border: 'none',
                  borderLeft: isActive ? '4px solid var(--color-golden-earth)' : '4px solid transparent',
                  fontWeight: isActive ? 700 : 500,
                  fontSize: '13px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'background-color 0.1s ease'
                }}
              >
                <span style={{ color: isActive ? 'var(--color-golden-earth)' : 'var(--text-muted)' }}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid rgba(115, 158, 130, 0.3)', fontSize: '11px', color: 'var(--text-muted)' }}>
        <div>Agastya Engine v1.0.0</div>
        <div>FastAPI &amp; Metaheuristics</div>
        <div style={{ marginTop: '6px', fontSize: '10px', opacity: 0.8 }}>No DB &bull; In-Memory LRU</div>
      </div>
    </aside>
  );
};
