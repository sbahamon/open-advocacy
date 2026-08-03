import React from 'react';
import { Card, CardContent, Grid, Typography } from '@mui/material';
import { WardAffordability } from '../../types';

interface AffordabilityCardProps {
  affordability?: WardAffordability | null;
}

function money(value?: number | null): string {
  return value != null ? `$${value.toLocaleString()}` : '—';
}

function pct(value?: number | null): string {
  return value != null ? `${value.toFixed(1)}%` : '—';
}

interface StatProps {
  label: string;
  value: string;
}

const Stat: React.FC<StatProps> = ({ label, value }) => (
  <Grid size={{ xs: 6, sm: 3 }}>
    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
      {label}
    </Typography>
    <Typography sx={{ fontVariantNumeric: 'tabular-nums' }}>{value}</Typography>
  </Grid>
);

/** Ward context from the community Zillow affordability survey. */
const AffordabilityCard: React.FC<AffordabilityCardProps> = ({ affordability }) => {
  if (!affordability) {
    return (
      <Typography color="text.secondary" variant="body2" sx={{ mt: 2 }}>
        No affordability survey data for this ward.
      </Typography>
    );
  }
  const a = affordability;
  const change = a.affordability_rank_change;
  const rankLine =
    a.affordability_rank_2025 != null && a.affordability_rank_2026 != null
      ? `${a.affordability_rank_2025} → ${a.affordability_rank_2026}` +
        (change != null ? ` (${change >= 0 ? '+' : ''}${change})` : '')
      : '—';

  return (
    <Card variant="outlined" sx={{ mt: 2 }}>
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>
          Affordability survey{a.neighborhoods ? ` — ${a.neighborhoods}` : ''}
        </Typography>
        <Grid container spacing={2}>
          <Stat
            label="Affordable at 60% AMI (2026)"
            value={`${pct(a.affordable_share_pct)} (${a.affordable_listings_2026 ?? '—'} of ${a.total_listings_2026 ?? '—'})`}
          />
          <Stat
            label="Affordable at 60% AMI (2025)"
            value={`${pct(a.affordable_share_pct_2025)} (${a.affordable_listings_2025 ?? '—'} of ${a.total_listings_2025 ?? '—'})`}
          />
          <Stat label="Affordability rank 2025 → 2026" value={rankLine} />
          <Stat
            label="Median rent 2025 → 2026"
            value={`${money(a.median_rent_2025)} → ${money(a.median_rent_2026)}`}
          />
          <Stat
            label="Median sale price 2025 → 2026"
            value={`${money(a.median_sale_price_2025)} → ${money(a.median_sale_price_2026)}`}
          />
        </Grid>
      </CardContent>
    </Card>
  );
};

export default AffordabilityCard;
