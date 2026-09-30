import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { ScenarioComparison } from '../types';
import { FuelComparisonChart } from '../charts/FuelComparisonChart';
import { RefreshCw } from 'lucide-react';

interface ScenariosPageProps {
  isLocalMode: boolean;
}

export const ScenariosPage: React.FC<ScenariosPageProps> = ({ isLocalMode }) => {
  const [vesselType, setVesselType] = useState('Container_14000TEU');
  const [annualDistanceNm, setAnnualDistanceNm] = useState(120000);
  const [cruisingSpeedKnots, setCruisingSpeedKnots] = useState(18.0);
  const [carbonPrice, setCarbonPrice] = useState(85.0);

  const [fuelPrices, setFuelPrices] = useState<Record<string, number>>({
    HFO: 550,
    VLSFO: 620,
    MGO: 850,
    LNG: 700,
    Methanol: 650,
    Ammonia: 800,
    Hydrogen: 3500
  });

  const [comparison, setComparison] = useState<ScenarioComparison | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchComparison = async () => {
    setIsLoading(true);
    try {
      if (isLocalMode) {
        // Fallback local comparison generator
        const baseFuelT = (annualDistanceNm / 18.0 / 24.0) * 165.0; // approx 165 t/day
        const lhvs: Record<string, number> = { HFO: 40.2, VLSFO: 41.0, MGO: 42.7, LNG: 48.0, Methanol: 19.9, Ammonia: 18.6, Hydrogen: 120.0 };
        const wtts: Record<string, number> = { HFO: 13.5, VLSFO: 14.1, MGO: 15.0, LNG: 18.5, Methanol: 25.0, Ammonia: 15.0, Hydrogen: 20.0 };
        const ttws: Record<string, number> = { HFO: 77.4, VLSFO: 76.5, MGO: 74.5, LNG: 56.1, Methanol: 30.0, Ammonia: 0.0, Hydrogen: 0.0 };

        const fuelsComp: Record<string, any> = {};
        for (const f of ['HFO', 'VLSFO', 'MGO', 'LNG', 'Methanol', 'Ammonia', 'Hydrogen']) {
          const neededT = (baseFuelT * 41.0) / lhvs[f];
          const energyMJ = neededT * 1000 * lhvs[f];
          const wtt = (energyMJ * wtts[f]) / 1e6;
          const ttw = (energyMJ * ttws[f]) / 1e6;
          const slip = f === 'LNG' ? neededT * 0.022 * 28 : f === 'Ammonia' ? neededT * 0.0004 * 273 : 0;
          const totalGHG = wtt + ttw + slip;
          const fCost = neededT * (fuelPrices[f] || 600);
          const cTax = totalGHG * carbonPrice;

          fuelsComp[f] = {
            fuel_name: f,
            annual_fuel_consumed_tonnes: Math.round(neededT),
            lhv_mj_per_kg: lhvs[f],
            wtt_ghg_tco2e: Math.round(wtt),
            ttw_ghg_tco2e: Math.round(ttw),
            methane_slip_tco2e: Math.round(f === 'LNG' ? slip : 0),
            n2o_slip_tco2e: Math.round(f === 'Ammonia' ? slip : 0),
            boil_off_tonnes: 0,
            berth_ghg_tco2e: 450,
            total_wtw_ghg_tco2e: Math.round(totalGHG),
            fuel_cost_usd: Math.round(fCost),
            carbon_tax_usd: Math.round(cTax),
            berth_cost_usd: 850000,
            total_annual_cost_usd: Math.round(fCost + cTax + 850000),
            requires_cryo_tanks: ['LNG', 'Ammonia', 'Hydrogen'].includes(f)
          };
        }

        setComparison({
          vessel_type: vesselType,
          annual_distance_nm: annualDistanceNm,
          cruising_speed_knots: cruisingSpeedKnots,
          carbon_price_usd_per_tco2e: carbonPrice,
          fuels_comparison: fuelsComp
        });
      } else {
        const res = await api.compareScenarios({
          vessel_type: vesselType,
          annual_distance_nm: annualDistanceNm,
          cruising_speed_knots: cruisingSpeedKnots,
          carbon_price_usd_per_tco2e: carbonPrice,
          fuel_price_adjustments: fuelPrices
        });
        setComparison(res);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchComparison, 200);
    return () => clearTimeout(timer);
  }, [vesselType, annualDistanceNm, cruisingSpeedKnots, carbonPrice, fuelPrices]);

  const handlePriceChange = (fuel: string, val: number) => {
    setFuelPrices(prev => ({ ...prev, [fuel]: val }));
  };

  const vlsfoTotalCost = comparison?.fuels_comparison['VLSFO']?.total_annual_cost_usd || 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Top Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: 'var(--bg-panel)',
          border: '1px solid var(--border-subtle)',
          padding: '10px 16px'
        }}
      >
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-dark-spruce)' }}>
            Alternative Fuel Decarbonization &amp; Sensitivity Analyzer
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Evaluates Well-to-Wake (WTW) lifecycle emissions, boil-off losses, methane/N2O slip, and carbon tax sensitivities.
          </p>
        </div>
        <button onClick={fetchComparison} disabled={isLoading} className="btn btn-secondary">
          <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} /> Recalculate
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '16px', alignItems: 'start' }}>
        {/* Sensitivity Sliders Column */}
        <div
          style={{
            backgroundColor: 'var(--bg-panel-light)',
            border: '1px solid var(--border-subtle)',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px'
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-dark-spruce)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
            SCENARIO SENSITIVITY CONTROLS
          </div>

          <div>
            <label>Vessel Specification</label>
            <select
              value={vesselType}
              onChange={(e) => setVesselType(e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="Container_14000TEU">Ultra Large Container (14,000 TEU)</option>
              <option value="Feeder_2500TEU">Regional Feeder Container (2,500 TEU)</option>
              <option value="Capesize_180000DWT">Capesize Ore Carrier (180,000 DWT)</option>
              <option value="Panamax_82000DWT">Panamax Bulk Carrier (82,000 DWT)</option>
              <option value="VLCC_300000DWT">VLCC Crude Tanker (300,000 DWT)</option>
            </select>
          </div>

          <div>
            <label>Annual Sailing Distance: {annualDistanceNm.toLocaleString()} nm</label>
            <input
              type="range"
              min="40000"
              max="200000"
              step="5000"
              value={annualDistanceNm}
              onChange={(e) => setAnnualDistanceNm(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <label>Cruising Speed: {cruisingSpeedKnots} knots</label>
            <input
              type="range"
              min="10.0"
              max="24.0"
              step="0.5"
              value={cruisingSpeedKnots}
              onChange={(e) => setCruisingSpeedKnots(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label>Carbon Price Tax: ${carbonPrice} / tCO2e</label>
            </div>
            <input
              type="range"
              min="0"
              max="300"
              step="10"
              value={carbonPrice}
              onChange={(e) => setCarbonPrice(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
            <label style={{ marginBottom: '8px' }}>Bunker Fuel Prices ($ / tonne)</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
              {Object.keys(fuelPrices).map((fuel) => (
                <div key={fuel} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600 }}>{fuel}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>$</span>
                    <input
                      type="number"
                      value={fuelPrices[fuel]}
                      onChange={(e) => handlePriceChange(fuel, parseFloat(e.target.value) || 0)}
                      style={{ width: '80px', padding: '3px 6px', textAlign: 'right' }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Results & Comparison Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Chart */}
          {comparison && (
            <FuelComparisonChart fuelsData={comparison.fuels_comparison} />
          )}

          {/* Side-by-Side Detailed Comparison Table */}
          {comparison && (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Fuel Pathway</th>
                    <th className="num">LHV (MJ/kg)</th>
                    <th className="num">Annual Fuel (t)</th>
                    <th className="num">Fuel Cost ($/yr)</th>
                    <th className="num">Carbon Tax ($/yr)</th>
                    <th className="num">WTW GHG (tCO2e)</th>
                    <th className="num">Total OPEX ($/yr)</th>
                    <th>Cost vs VLSFO</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(comparison.fuels_comparison).map(([fuelKey, detail]) => {
                    const deltaCost = detail.total_annual_cost_usd - vlsfoTotalCost;
                    const deltaPct = (deltaCost / vlsfoTotalCost) * 100;
                    const isBase = fuelKey === 'VLSFO';

                    return (
                      <tr key={fuelKey} style={{ fontWeight: isBase ? 700 : 400 }}>
                        <td>{detail.fuel_name}</td>
                        <td className="num">{detail.lhv_mj_per_kg}</td>
                        <td className="num">{detail.annual_fuel_consumed_tonnes.toLocaleString()}</td>
                        <td className="num">${(detail.fuel_cost_usd / 1e6).toFixed(2)}M</td>
                        <td className="num">${(detail.carbon_tax_usd / 1e6).toFixed(2)}M</td>
                        <td className="num">{detail.total_wtw_ghg_tco2e.toLocaleString()}</td>
                        <td className="num">${(detail.total_annual_cost_usd / 1e6).toFixed(2)}M</td>
                        <td className="num">
                          {isBase ? (
                            <span style={{ color: 'var(--text-muted)' }}>Baseline</span>
                          ) : deltaPct > 0 ? (
                            <span style={{ color: 'var(--danger)' }}>+{deltaPct.toFixed(1)}%</span>
                          ) : (
                            <span style={{ color: 'var(--color-dark-spruce)', fontWeight: 700 }}>{deltaPct.toFixed(1)}%</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
