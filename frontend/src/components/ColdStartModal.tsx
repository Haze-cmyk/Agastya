import React from 'react';
import { Loader2, Server, Play } from 'lucide-react';

interface ColdStartModalProps {
  isOpen: boolean;
  attempt: number;
  onSwitchToLocal: () => void;
}

export const ColdStartModal: React.FC<ColdStartModalProps> = ({
  isOpen,
  attempt,
  onSwitchToLocal
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(44, 85, 48, 0.65)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}
    >
      <div
        style={{
          width: '440px',
          backgroundColor: 'var(--bg-panel-light)',
          border: '2px solid var(--color-dark-spruce)',
          padding: '24px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
          <Server size={22} color="var(--color-golden-earth)" />
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-dark-spruce)' }}>
            Backend Server Is Waking Up
          </h2>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-main)', marginBottom: '12px', lineHeight: 1.5 }}>
          The cloud backend on Render free tier spins down during periods of inactivity.
          A fresh instance is booting now. Connection retry attempt <strong>{attempt} of 3</strong>.
        </p>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 14px',
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--border-subtle)',
            fontSize: '12px',
            color: 'var(--text-main)',
            marginBottom: '18px'
          }}
        >
          <Loader2 className="animate-spin" size={16} />
          <span>Polling health check endpoint with exponential backoff...</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button
            onClick={onSwitchToLocal}
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <Play size={14} /> Continue Locally (Reduced Worker Mode)
          </button>
        </div>
      </div>
    </div>
  );
};
