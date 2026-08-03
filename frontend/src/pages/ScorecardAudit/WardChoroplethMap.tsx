import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { ZoningAuditWard } from '../../types';
import {
  AuditColorMetric,
  colorForValue,
  DIVERGING_METRICS,
  divergingColorForValue,
  quantileBins,
} from './wardColorScale';
import { wardNumberFromDistrictName } from './wardNumberFromDistrictName';

interface WardChoroplethMapProps {
  wards: ZoningAuditWard[];
  geojsonByDistrict: { [districtName: string]: GeoJSON.GeoJsonObject };
  colorMetric: AuditColorMetric;
  selectedWard: number | null;
  onSelectWard: (ward: number) => void;
}

function metricValue(ward: ZoningAuditWard, metric: AuditColorMetric): number | null {
  const raw =
    metric === 'affordable_share_pct' || metric === 'affordability_rank_change'
      ? ward.affordability?.[metric]
      : ward[metric];
  return typeof raw === 'number' ? raw : null;
}

/** Choropleth of the 50 wards colored by the selected metric. */
const WardChoroplethMap: React.FC<WardChoroplethMapProps> = ({
  wards,
  geojsonByDistrict,
  colorMetric,
  selectedWard,
  onSelectWard,
}) => {
  const wardByNumber = new Map(wards.map(w => [w.ward, w]));
  const values = wards
    .map(w => metricValue(w, colorMetric))
    .filter((v): v is number => v !== null);
  const diverging = DIVERGING_METRICS.has(colorMetric);
  const edges = diverging ? [] : quantileBins(values);
  const maxAbs = diverging ? Math.max(0, ...values.map(v => Math.abs(v))) : 0;
  const affordabilityActive =
    colorMetric === 'affordable_share_pct' || colorMetric === 'affordability_rank_change';

  return (
    <MapContainer center={[41.8781, -87.6298]} zoom={10} style={{ height: 520, width: '100%' }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {Object.entries(geojsonByDistrict).map(([districtName, geojson]) => {
        const wardNumber = wardNumberFromDistrictName(districtName);
        const ward = wardNumber != null ? wardByNumber.get(wardNumber) : undefined;
        const value = ward ? metricValue(ward, colorMetric) : null;
        return (
          <GeoJSON
            key={`${districtName}|${colorMetric}|${selectedWard === wardNumber}`}
            data={geojson}
            style={() => ({
              color: selectedWard === wardNumber ? '#000' : '#555',
              weight: selectedWard === wardNumber ? 3 : 1,
              fillColor: diverging
                ? divergingColorForValue(value, maxAbs)
                : colorForValue(value, edges),
              fillOpacity: 0.75,
            })}
            eventHandlers={{
              click: () => {
                if (wardNumber != null) onSelectWard(wardNumber);
              },
            }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            onEachFeature={(_feature: GeoJSON.Feature, layer: any) => {
              let tooltip = `<strong>${districtName}</strong>`;
              if (ward) {
                if (ward.alder_name) tooltip += `<br/>${ward.alder_name}`;
                if (affordabilityActive && ward.affordability) {
                  const a = ward.affordability;
                  tooltip +=
                    `<br/>Affordable listings: ${a.affordable_share_pct ?? '—'}%` +
                    ` (of ${a.total_listings_2026 ?? '—'})` +
                    `<br/>Rank: ${a.affordability_rank_2025 ?? '—'} → ` +
                    `${a.affordability_rank_2026 ?? '—'}` +
                    ` (${(a.affordability_rank_change ?? 0) >= 0 ? '+' : ''}` +
                    `${a.affordability_rank_change ?? '—'})`;
                } else {
                  tooltip +=
                    `<br/>Median delay: ${ward.zoning_median_days ?? '—'} days` +
                    `<br/>Rezonings: ${ward.zoning_matter_count}` +
                    ` (${ward.n_resolved} resolved, ${ward.n_pending} pending)` +
                    `<br/>Stalled >180d: ${ward.zoning_stalled_count}`;
                }
                tooltip += `<br/><em>Click for ward details</em>`;
              }
              layer.bindTooltip(tooltip, { sticky: true });
            }}
          />
        );
      })}
    </MapContainer>
  );
};

export default WardChoroplethMap;
