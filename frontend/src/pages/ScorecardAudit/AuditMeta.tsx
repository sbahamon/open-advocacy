import React, { useState } from 'react';
import { Box, Collapse, Link as MuiLink, Typography } from '@mui/material';

interface AuditMetaProps {
  meta: Record<string, unknown>;
  unassignedCount: number;
}

/** Coverage and caveat block: as-of, geocode coverage, near-boundary counts. */
const AuditMeta: React.FC<AuditMetaProps> = ({ meta, unassignedCount }) => {
  const [showUnassigned, setShowUnassigned] = useState(false);
  const unassignedRecords = Array.isArray(meta.unassigned_record_numbers)
    ? (meta.unassigned_record_numbers as string[])
    : [];

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
        Zoning reclassifications introduced since {String(meta.term_start ?? '—')};
        stalled determination frozen at {String(meta.computed_at ?? '—')}. Ward
        assignment coverage {String(meta.geocode_coverage_pct ?? '—')}% of{' '}
        {String(meta.total_matters ?? '—')} matters; {String(meta.near_boundary_count ?? 0)}{' '}
        assigned points sit within {String(meta.near_boundary_threshold_m ?? 30)} m of a
        ward boundary (flagged in the tables).
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
        {unassignedCount} matters could not be confidently assigned to a ward and are
        excluded from every ward statistic (never guessed).{' '}
        {unassignedRecords.length > 0 && (
          <MuiLink component="button" type="button" onClick={() => setShowUnassigned(s => !s)}>
            {showUnassigned ? 'Hide record numbers' : 'Show record numbers'}
          </MuiLink>
        )}
      </Typography>
      <Collapse in={showUnassigned}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
          {unassignedRecords.join(', ')}
        </Typography>
      </Collapse>
    </Box>
  );
};

export default AuditMeta;
