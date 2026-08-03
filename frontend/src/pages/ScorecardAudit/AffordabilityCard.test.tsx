import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import AffordabilityCard from './AffordabilityCard';
import { WardAffordability } from '../../types';

const AFFORDABILITY: WardAffordability = {
  neighborhoods: 'Wicker Park, Logan Square',
  affordable_share_pct: 1.16,
  affordable_share_pct_2025: 0.7,
  affordable_listings_2025: 4,
  affordable_listings_2026: 6,
  total_listings_2025: 571,
  total_listings_2026: 516,
  affordability_rank_2025: 48,
  affordability_rank_2026: 46,
  affordability_rank_change: 2,
  median_rent_2025: 2500,
  median_rent_2026: 2795,
  median_sale_price_2025: 700000,
  median_sale_price_2026: 770000,
};

describe('AffordabilityCard', () => {
  it('renders shares with their raw listing counts (small-N visible)', () => {
    render(<AffordabilityCard affordability={AFFORDABILITY} />);
    expect(screen.getByText('1.2% (6 of 516)')).toBeInTheDocument();
    expect(screen.getByText('0.7% (4 of 571)')).toBeInTheDocument();
  });

  it('renders rank movement with a signed change', () => {
    render(<AffordabilityCard affordability={AFFORDABILITY} />);
    expect(screen.getByText('48 → 46 (+2)')).toBeInTheDocument();
  });

  it('renders medians and neighborhoods', () => {
    render(<AffordabilityCard affordability={AFFORDABILITY} />);
    expect(screen.getByText(/Wicker Park, Logan Square/)).toBeInTheDocument();
    expect(screen.getByText('$2,500 → $2,795')).toBeInTheDocument();
    expect(screen.getByText('$700,000 → $770,000')).toBeInTheDocument();
  });

  it('renders a fallback when the ward has no survey data', () => {
    render(<AffordabilityCard affordability={null} />);
    expect(screen.getByText(/No affordability survey data/)).toBeInTheDocument();
  });
});
