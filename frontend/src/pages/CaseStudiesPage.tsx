import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { CaseStudy } from '../types';
import { Play, ArrowRight } from 'lucide-react';

interface CaseStudiesPageProps {
  onLoadPreset: (preset: CaseStudy) => void;
}

export const CaseStudiesPage: React.FC<CaseStudiesPageProps> = ({ onLoadPreset }) => {
  const [caseStudies, setCaseStudies] = useState<Record<string, CaseStudy>>({});

  useEffect(() => {
    const fetchCases = async () => {
      try {
        const data = await api.fetchCaseStudies();
        setCaseStudies(data);
      } catch {
        // Fallback default presets
        setCaseStudies({
          asia_europe_container: {
            preset_id: 'asia_europe_container',
            title: 'Asia-Europe ULCV Container Loop',
            category: 'Container',
            description: 'High-volume 14,000 TEU liner loop between Shanghai and Rotterdam across 11,500 nautical miles.',
            cargo_demand: 250000,
            demand_unit: 'TEU',
            route_distance_nm: 11500,
            max_delivery_days: 28,
            emission_cap_tco2e: 180000,
            carbon_price_usd_per_tco2e: 85,
            candidate_vessels: ['Container_14000TEU', 'Feeder_2500TEU'],
            candidate_fuels: ['VLSFO', 'LNG', 'Methanol', 'Ammonia'],
            origin_port: 'CNSHA',
            destination_port: 'NLRTM',
            allow_shore_power: true
          },
          australia_china_bulk: {
            preset_id: 'australia_china_bulk',
            title: 'Australia-China Capesize Iron Ore Corridor',
            category: 'Bulk Carrier',
            description: 'Dedicated bulk mineral commodity shuttle from Port Hedland to Shanghai (3,450 nautical miles).',
            cargo_demand: 2500000,
            demand_unit: 'DWT',
            route_distance_nm: 3450,
            max_delivery_days: 14,
            emission_cap_tco2e: 120000,
            carbon_price_usd_per_tco2e: 60,
            candidate_vessels: ['Capesize_180000DWT', 'Panamax_82000DWT'],
            candidate_fuels: ['VLSFO', 'LNG', 'Ammonia'],
            origin_port: 'AUPHE',
            destination_port: 'CNSHA',
            allow_shore_power: true
          },
          middle_east_europe_tanker: {
            preset_id: 'middle_east_europe_tanker',
            title: 'Arabian Gulf to Rotterdam VLCC Crude Route',
            category: 'Tanker',
            description: 'Long-range crude carrier corridor from Ras Tanura to Rotterdam (6,400 nautical miles).',
            cargo_demand: 3000000,
            demand_unit: 'DWT',
            route_distance_nm: 6400,
            max_delivery_days: 22,
            emission_cap_tco2e: 160000,
            carbon_price_usd_per_tco2e: 90,
            candidate_vessels: ['VLCC_300000DWT', 'Aframax_115000DWT'],
            candidate_fuels: ['VLSFO', 'LNG', 'Methanol'],
            origin_port: 'SARAS',
            destination_port: 'NLRTM',
            allow_shore_power: true
          }
        });
      }
    };
    fetchCases();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Top Banner */}
      <div
        style={{
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-subtle)',
          padding: '10px 16px'
        }}
      >
        <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-dark-spruce)' }}>
          Industrial Maritime Case Studies &amp; Pre-Configured Presets
        </h2>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Real-world trade corridors calibrated with commercial shipping schedules, port bunkering availability, and decarbonization caps.
        </p>
      </div>

      {/* Case Study Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {Object.values(caseStudies).map((study) => (
          <div
            key={study.preset_id}
            style={{
              backgroundColor: 'var(--bg-panel-light)',
              border: '1px solid var(--border-subtle)',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span className="badge badge-feasible" style={{ marginRight: '8px' }}>
                  {study.category}
                </span>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-dark-spruce)' }}>
                  {study.title}
                </span>
              </div>
              <button
                onClick={() => onLoadPreset(study)}
                className="btn btn-primary"
              >
                <Play size={13} /> Load Into Fleet Optimizer <ArrowRight size={13} />
              </button>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: 1.5 }}>
              {study.description}
            </p>

            {/* Parameter Matrix */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 1fr)',
                gap: '10px',
                padding: '10px',
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--border-subtle)',
                fontSize: '12px'
              }}
            >
              <div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>CORRIDOR</div>
                <div style={{ fontWeight: 600 }}>{study.origin_port} &rarr; {study.destination_port}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>ONE-WAY DISTANCE</div>
                <div className="num" style={{ fontWeight: 600 }}>{study.route_distance_nm.toLocaleString()} nm</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>ANNUAL DEMAND</div>
                <div className="num" style={{ fontWeight: 600 }}>{study.cargo_demand.toLocaleString()} {study.demand_unit}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>TRANSIT DEADLINE</div>
                <div className="num" style={{ fontWeight: 600 }}>{study.max_delivery_days} days</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>EMISSION CAP</div>
                <div className="num" style={{ fontWeight: 600 }}>{study.emission_cap_tco2e.toLocaleString()} tCO2e</div>
              </div>
            </div>

            {/* Candidate options */}
            <div style={{ display: 'flex', gap: '20px', fontSize: '12px', color: 'var(--text-muted)' }}>
              <div>
                <strong>Candidate Vessels:</strong> {study.candidate_vessels.join(', ')}
              </div>
              <div>
                <strong>Alternative Fuels:</strong> {study.candidate_fuels.join(', ')}
              </div>
              <div>
                <strong>Shore Power:</strong> {study.allow_shore_power ? 'Enabled' : 'Disabled'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
