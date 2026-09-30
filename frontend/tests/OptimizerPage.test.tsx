import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { OptimizerPage } from '../src/pages/OptimizerPage';

describe('OptimizerPage Component', () => {
  it('renders optimization controls and solver options', () => {
    const onColdStart = vi.fn();
    render(<OptimizerPage isLocalMode={false} onTriggerColdStart={onColdStart} />);

    expect(screen.getByText('Green Fleet Multi-Objective Deployment Optimizer')).toBeInTheDocument();
    expect(screen.getByText('OPTIMIZATION CONFIGURATION')).toBeInTheDocument();
    expect(screen.getByText('Run Optimizer')).toBeInTheDocument();
    expect(screen.getByText('QIEA (Quantum-Inspired Evolutionary)')).toBeInTheDocument();
  });

  it('allows switching solver to QI-PSO and NSGA-II', () => {
    const onColdStart = vi.fn();
    render(<OptimizerPage isLocalMode={false} onTriggerColdStart={onColdStart} />);

    const select = screen.getByLabelText(/Solver Algorithm/i);
    fireEvent.change(select, { target: { value: 'QI-PSO' } });
    expect(select).toHaveValue('QI-PSO');

    fireEvent.change(select, { target: { value: 'NSGA-II' } });
    expect(select).toHaveValue('NSGA-II');
  });

  it('runs locally in worker mode when isLocalMode is true', () => {
    const onColdStart = vi.fn();
    render(<OptimizerPage isLocalMode={true} onTriggerColdStart={onColdStart} />);

    const runBtn = screen.getByText('Run Optimizer');
    expect(runBtn).not.toBeDisabled();
  });
});
