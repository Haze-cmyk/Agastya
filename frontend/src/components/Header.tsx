import React from 'react';
import { ConnectionStatus } from '../types';
import { AlertTriangle, Wifi, WifiOff } from 'lucide-react';

interface HeaderProps {
  status: ConnectionStatus;
  isLocalMode: boolean;
  onRetryConnection: () => void;
}

export const Header: React.FC<HeaderProps> = ({ status, isLocalMode, onRetryConnection }) => {
  return (
    <header
      style={{
        height: '52px',
        backgroundColor: 'var(--color-dark-spruce)',
        color: 'var(--color-lime-cream)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        borderBottom: '2px solid var(--color-golden-earth)',
        zIndex: 10
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
        <h1 style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '0.5px', color: '#FFFFFF' }}>
          AGASTYA
        </h1>
        <span style={{ fontSize: '12px', color: 'var(--color-lime-cream)', opacity: 0.9 }}>
          Quantum-Inspired Green Fleet Optimizer
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {isLocalMode && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--color-toasted-almond)',
              color: '#1B361E',
              padding: '3px 8px',
              borderRadius: '2px',
              fontSize: '11px',
              fontWeight: 700
            }}
          >
            <AlertTriangle size={13} />
            <span>RUNNING LOCALLY (REDUCED MODE)</span>
          </div>
        )}

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)'
          }}
        >
          {status === 'online' ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#A6F29C' }}>
              <Wifi size={14} /> Backend Online
            </span>
          ) : status === 'waking_up' ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#FFDF6D' }}>
              <Wifi size={14} /> Waking Up...
            </span>
          ) : (
            <button
              onClick={onRetryConnection}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                background: 'none',
                border: '1px solid var(--color-muted-teal)',
                color: 'var(--color-lime-cream)',
                borderRadius: '2px',
                padding: '2px 8px',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              <WifiOff size={13} /> Backend Offline (Retry)
            </button>
          )}
        </div>

        <span
          style={{
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            backgroundColor: 'rgba(243, 255, 182, 0.15)',
            padding: '2px 6px',
            borderRadius: '2px'
          }}
        >
          v1.0.0
        </span>
      </div>
    </header>
  );
};
