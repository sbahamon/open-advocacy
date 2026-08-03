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
  const visible = visibleMetrics(metrics);
  const described = visible.filter(m => m.description);
  if (described.length === 0) return null;

  // The group-level vintage line covers metrics without their own source
  // (historically the zoning metrics). Metrics that declare a source get one
  // attribution line per distinct (source, as_of) pair.
  const hasUnsourced = visible.some(m => !m.source);
  const sourceLines: { source: string; asOf: string | null }[] = [];
  for (const metric of visible) {
    if (!metric.source) continue;
    const asOf = metric.as_of ?? metricsAsOf ?? null;
    if (!sourceLines.some(line => line.source === metric.source && line.asOf === asOf)) {
      sourceLines.push({ source: metric.source, asOf });
    }
  }

  return (
    <Box sx={{ mt: 3 }}>
      {metricsAsOf && hasUnsourced && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          Zoning metric data as of {metricsAsOf}.
        </Typography>
      )}
      {sourceLines.map(line => (
        <Typography
          key={`${line.source}|${line.asOf ?? ''}`}
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mb: 0.5 }}
        >
          {line.source}
          {line.asOf ? `; data as of ${line.asOf}` : ''}.
        </Typography>
      ))}
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
