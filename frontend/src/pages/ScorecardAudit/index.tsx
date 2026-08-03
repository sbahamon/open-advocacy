import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  CircularProgress,
  Container,
  Link as MuiLink,
  Stack,
  Typography,
} from '@mui/material';
import { ZoningAuditResponse } from '../../types';
import { zoningAuditService } from '../../services/zoningAudit';
import { jurisdictionService } from '../../services/jurisdictions';
import WardChoroplethMap from './WardChoroplethMap';
import WardMattersTable from './WardMattersTable';
import MetricToggle from './MetricToggle';
import AuditMeta from './AuditMeta';
import { AuditColorMetric } from './wardColorScale';

/**
 * Audit drill-down behind the scorecard's ward zoning metrics: a choropleth
 * of the 50 wards plus the per-matter records each ward's numbers come from.
 */
const ScorecardAudit: React.FC = () => {
  const { groupSlug } = useParams<{ groupSlug: string }>();
  const [audit, setAudit] = useState<ZoningAuditResponse | null>(null);
  const [geojson, setGeojson] = useState<{ [district: string]: GeoJSON.GeoJsonObject }>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedWard, setSelectedWard] = useState<number | null>(null);
  const [colorMetric, setColorMetric] = useState<AuditColorMetric>('zoning_median_days');

  useEffect(() => {
    if (!groupSlug) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await zoningAuditService.getZoningAudit(groupSlug);
        if (cancelled) return;
        setAudit(response.data);
        if (response.data.jurisdiction_id) {
          const boundaries = await jurisdictionService.getDistrictGeoJSON(
            response.data.jurisdiction_id
          );
          if (!cancelled) setGeojson(boundaries);
        }
      } catch {
        if (!cancelled) setError('Could not load the zoning audit data for this group.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [groupSlug]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress aria-label="Loading zoning audit" />
      </Box>
    );
  }

  if (error || !audit) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">{error ?? 'No audit data available.'}</Alert>
      </Container>
    );
  }

  const selected = audit.wards.find(w => w.ward === selectedWard) ?? null;

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Ward Zoning Delay — Audit
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Every number on the{' '}
        <MuiLink component={RouterLink} to={`/scorecard/${groupSlug}`}>
          {audit.group_name} scorecard
        </MuiLink>{' '}
        zoning columns traces back to the City Council matters below. Click a ward to
        see its docket.
      </Typography>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
        <MetricToggle value={colorMetric} onChange={setColorMetric} />
      </Stack>

      <WardChoroplethMap
        wards={audit.wards}
        geojsonByDistrict={geojson}
        colorMetric={colorMetric}
        selectedWard={selectedWard}
        onSelectWard={setSelectedWard}
      />

      <AuditMeta meta={audit.meta} unassignedCount={audit.unassigned_matters.length} />

      {selected ? (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" component="h2">
            Ward {selected.ward}
            {selected.alder_name ? ` — ${selected.alder_name}` : ''}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Median delay {selected.zoning_median_days ?? '—'} days over{' '}
            {selected.n_resolved} resolved matters; {selected.n_pending} pending,{' '}
            {selected.zoning_stalled_count} stalled &gt;180 days.
          </Typography>
          <WardMattersTable ward={selected.ward} matters={selected.matters} />
        </Box>
      ) : (
        <Typography color="text.secondary" sx={{ mt: 3 }}>
          Select a ward on the map to see the matters behind its numbers.
        </Typography>
      )}
    </Container>
  );
};

export default ScorecardAudit;
