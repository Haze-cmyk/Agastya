import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import App from '../src/App';

describe('App Layout and Navigation', () => {
  it('renders application header with title Agastya', () => {
    render(<App />);
    expect(screen.getByText('AGASTYA')).toBeInTheDocument();
    expect(screen.getByText('Quantum-Inspired Green Fleet Optimizer')).toBeInTheDocument();
  });

  it('navigates between sidebar workspaces', () => {
    render(<App />);

    // Default is Optimizer
    expect(screen.getByText('Green Fleet Multi-Objective Deployment Optimizer')).toBeInTheDocument();

    // Click Fuel Predictor
    const predictorBtn = screen.getByText('Fuel Predictor');
    fireEvent.click(predictorBtn);
    expect(screen.getByText('Hydrodynamic Fuel Prediction & Quantum Regressor Benchmark')).toBeInTheDocument();

    // Click Case Studies
    const caseStudiesBtn = screen.getByText('Case Studies');
    fireEvent.click(caseStudiesBtn);
    expect(screen.getByText('Industrial Maritime Case Studies & Pre-Configured Presets')).toBeInTheDocument();
  });
});
