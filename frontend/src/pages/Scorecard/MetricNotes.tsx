import React from 'react';
import { Box, Typography } from '@mui/material';
import { MetricDisplayConfig } from '../../types';
import { visibleMetrics } from './metricDisplay';

interface MetricNotesProps {
  metrics?: MetricDisplayConfig[];
  metricsAsOf?: string | null;
}

/**
 * Always-visible footnotes for the metric columns: what each one measures and
 * the data vintage. Desktop tooltips carry the same text on hover, but tooltip
 * content is unreachable on touch devices, so this block is the guaranteed
 * path to the ward-scoped caveats on every layout.
 */
const MetricNotes: React.FC<MetricNotesProps> = ({ metrics, metricsAsOf }) => {
  const described = visibleMetrics(metrics).filter(m => m.description);
  if (described.length === 0) return null;

  return (
    <Box sx={{ mt: 3 }}>
      {metricsAsOf && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          Zoning metric data as of {metricsAsOf}.
        </Typography>
      )}
      {described.map(metric => (
        <Typography
          key={metric.key}
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mb: 0.5 }}
        >
          <strong>{metric.label}:</strong> {metric.description}
        </Typography>
      ))}
    </Box>
  );
};

export default MetricNotes;
