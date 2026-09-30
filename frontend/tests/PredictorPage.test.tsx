import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { PredictorPage } from '../src/pages/PredictorPage';

describe('PredictorPage Component', () => {
  it('renders fuel calculator and parameter sliders', () => {
    render(<PredictorPage isLocalMode={true} />);

    expect(screen.getByText('Hydrodynamic Fuel Prediction & Quantum Regressor Benchmark')).toBeInTheDocument();
    expect(screen.getByText('OPERATIONAL PARAMETERS')).toBeInTheDocument();
    expect(screen.getByText('Hydrodynamic Calculator')).toBeInTheDocument();
    expect(screen.getByText('Model Benchmark & Training')).toBeInTheDocument();
  });

  it('switches to training and benchmarking tab', () => {
    render(<PredictorPage isLocalMode={true} />);

    const trainTabBtn = screen.getByText('Model Benchmark & Training');
    fireEvent.click(trainTabBtn);

    expect(screen.getByText('Train & Benchmark All Models')).toBeInTheDocument();
    expect(screen.getByText('Sample Dataset Size')).toBeInTheDocument();
  });
});
