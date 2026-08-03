import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { ZoningAuditWard } from '../../types';
import { AuditColorMetric, colorForValue, quantileBins } from './wardColorScale';
import { wardNumberFromDistrictName } from './wardNumberFromDistrictName';

interface WardChoroplethMapProps {
  wards: ZoningAuditWard[];
  geojsonByDistrict: { [districtName: string]: GeoJSON.GeoJsonObject };
  colorMetric: AuditColorMetric;
  selectedWard: number | null;
  onSelectWard: (ward: number) => void;
}

/** Choropleth of the 50 wards colored by the selected delay metric. */
const WardChoroplethMap: React.FC<WardChoroplethMapProps> = ({
  wards,
  geojsonByDistrict,
  colorMetric,
  selectedWard,
  onSelectWard,
}) => {
  const wardByNumber = new Map(wards.map(w => [w.ward, w]));
  const values = wards
    .map(w => w[colorMetric])
    .filter((v): v is number => typeof v === 'number');
  const edges = quantileBins(values);

  return (
    <MapContainer center={[41.8781, -87.6298]} zoom={10} style={{ height: 520, width: '100%' }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {Object.entries(geojsonByDistrict).map(([districtName, geojson]) => {
        const wardNumber = wardNumberFromDistrictName(districtName);
        const ward = wardNumber != null ? wardByNumber.get(wardNumber) : undefined;
        const value = ward ? ward[colorMetric] : null;
        return (
          <GeoJSON
            key={`${districtName}|${colorMetric}|${selectedWard === wardNumber}`}
            data={geojson}
            style={() => ({
              color: selectedWard === wardNumber ? '#000' : '#555',
              weight: selectedWard === wardNumber ? 3 : 1,
              fillColor: colorForValue(value, edges),
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
                tooltip +=
                  `<br/>Median delay: ${ward.zoning_median_days ?? '—'} days` +
                  `<br/>Rezonings: ${ward.zoning_matter_count}` +
                  ` (${ward.n_resolved} resolved, ${ward.n_pending} pending)` +
                  `<br/>Stalled >180d: ${ward.zoning_stalled_count}` +
                  `<br/><em>Click for the matter list</em>`;
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
