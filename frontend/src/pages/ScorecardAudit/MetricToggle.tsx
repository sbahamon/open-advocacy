import React from 'react';
import { ToggleButton, ToggleButtonGroup } from '@mui/material';
import { AuditColorMetric, COLOR_METRIC_LABELS } from './wardColorScale';

interface MetricToggleProps {
  value: AuditColorMetric;
  onChange: (metric: AuditColorMetric) => void;
}

/** Picks which metric drives the choropleth coloring. */
const MetricToggle: React.FC<MetricToggleProps> = ({ value, onChange }) => (
  <ToggleButtonGroup
    size="small"
    exclusive
    value={value}
    onChange={(_event, next: AuditColorMetric | null) => {
      if (next !== null) onChange(next);
    }}
    aria-label="Color wards by"
  >
    {(Object.keys(COLOR_METRIC_LABELS) as AuditColorMetric[]).map(key => (
      <ToggleButton key={key} value={key}>
        {COLOR_METRIC_LABELS[key]}
      </ToggleButton>
    ))}
  </ToggleButtonGroup>
);

export default MetricToggle;
