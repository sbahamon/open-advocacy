import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ZoningAuditResponse } from '../../types';

// Mock the services and the Leaflet map (jsdom has no real layout engine).
vi.mock('../../services/zoningAudit', () => ({
  zoningAuditService: { getZoningAudit: vi.fn() },
}));
vi.mock('../../services/jurisdictions', () => ({
  jurisdictionService: { getDistrictGeoJSON: vi.fn() },
}));
vi.mock('./WardChoroplethMap', () => ({
  default: ({ onSelectWard }: { onSelectWard: (w: number) => void }) => (
    <div data-testid="choropleth">
      <button onClick={() => onSelectWard(35)}>select-ward-35</button>
    </div>
  ),
}));

import ScorecardAudit from './index';
import { zoningAuditService } from '../../services/zoningAudit';
import { jurisdictionService } from '../../services/jurisdictions';

const mockAudit: ZoningAuditResponse = {
  group_name: 'Test Group',
  jurisdiction_id: 'jur-1',
  meta: {
    computed_at: '2026-08-02',
    term_start: '2023-05-15',
    total_matters: 3,
    geocode_coverage_pct: 96.5,
    near_boundary_count: 1,
    near_boundary_threshold_m: 30.0,
    unassigned_record_numbers: ['O2026-0000009'],
  },
  affordability_meta: { as_of: '2026-07-28', source: 'Community Zillow survey' },
  wards: Array.from({ length: 50 }, (_, i) => ({
    ward: i + 1,
    alder_name: i === 34 ? 'Quezada, Anthony J.' : null,
    zoning_median_days: 40,
    zoning_matter_count: 2,
    zoning_stalled_count: 1,
    n_resolved: 1,
    n_pending: 1,
    matters: [],
    affordability:
      i === 34
        ? {
            neighborhoods: 'Logan Square',
            affordable_share_pct: 4.26,
            affordable_listings_2026: 21,
            total_listings_2026: 493,
            affordability_rank_2025: 20,
            affordability_rank_2026: 21,
            affordability_rank_change: -1,
          }
        : null,
  })),
  unassigned_matters: [
    {
      record_number: 'O2026-0000009',
      matter_guid: 'guid-9',
      near_boundary: false,
      stalled: false,
      pending: true,
      withdrawn: false,
    },
  ],
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/scorecard/test-group/audit']}>
      <Routes>
        <Route path="/scorecard/:groupSlug/audit" element={<ScorecardAudit />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('ScorecardAudit', () => {
  beforeEach(() => {
    vi.mocked(zoningAuditService.getZoningAudit).mockResolvedValue({
      data: mockAudit,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any);
    vi.mocked(jurisdictionService.getDistrictGeoJSON).mockResolvedValue({});
  });

  it('renders the map, coverage caveats, and select prompt after loading', async () => {
    renderPage();
    expect(await screen.findByTestId('choropleth')).toBeInTheDocument();
    expect(screen.getByText(/Ward assignment coverage 96.5/)).toBeInTheDocument();
    expect(
      screen.getByText(/1 matters could not be confidently assigned/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Select a ward on the map/)
    ).toBeInTheDocument();
  });

  it('shows the affordability card AND the zoning docket on ward selection', async () => {
    renderPage();
    const selectButton = await screen.findByText('select-ward-35');
    fireEvent.click(selectButton);
    // Affordability card...
    expect(await screen.findByText(/Logan Square/)).toBeInTheDocument();
    expect(screen.getByText('4.3% (21 of 493)')).toBeInTheDocument();
    expect(screen.getByText('20 → 21 (-1)')).toBeInTheDocument();
    // ...and the zoning docket area, together.
    expect(
      screen.getByText(/No zoning reclassifications recorded for Ward 35/)
    ).toBeInTheDocument();
  });

  it('shows the affordability source line in the meta block', async () => {
    renderPage();
    expect(
      await screen.findByText(/Affordability: Community Zillow survey; data as of 2026-07-28/)
    ).toBeInTheDocument();
  });

  it('shows an error state when the audit request fails', async () => {
    vi.mocked(zoningAuditService.getZoningAudit).mockRejectedValue(new Error('404'));
    renderPage();
    expect(
      await screen.findByText(/Could not load the zoning audit data/)
    ).toBeInTheDocument();
  });
});
