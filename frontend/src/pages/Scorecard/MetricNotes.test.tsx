import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricNotes from './MetricNotes';
import { MetricDisplayConfig } from '../../types';

const METRICS: MetricDisplayConfig[] = [
  {
    key: 'zoning_median_days',
    label: 'Ward Zoning Delay (median days)',
    description: 'Ward-scoped, not person-scoped.',
    show_in_table: true,
  },
  {
    key: 'hidden_metric',
    label: 'Hidden',
    description: 'Should not render.',
    show_in_table: false,
  },
  {
    key: 'no_description',
    label: 'No Description',
    show_in_table: true,
  },
];

describe('MetricNotes', () => {
  it('renders nothing when there are no visible metrics', () => {
    const { container } = render(<MetricNotes metrics={[]} metricsAsOf={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the description of each visible metric', () => {
    render(<MetricNotes metrics={METRICS} metricsAsOf={null} />);
    expect(screen.getByText(/Ward Zoning Delay \(median days\)/)).toBeInTheDocument();
    expect(screen.getByText(/Ward-scoped, not person-scoped\./)).toBeInTheDocument();
  });

  it('does not render hidden metrics or ones without a description', () => {
    render(<MetricNotes metrics={METRICS} metricsAsOf={null} />);
    expect(screen.queryByText(/Should not render\./)).not.toBeInTheDocument();
    expect(screen.queryByText(/No Description/)).not.toBeInTheDocument();
  });

  it('renders the data vintage when provided', () => {
    render(<MetricNotes metrics={METRICS} metricsAsOf="2026-07-23" />);
    // Exact legacy string — sourceless metrics must keep this line verbatim.
    expect(screen.getByText('Zoning metric data as of 2026-07-23.')).toBeInTheDocument();
  });

  it('omits the vintage line when not provided', () => {
    render(<MetricNotes metrics={METRICS} metricsAsOf={null} />);
    expect(screen.queryByText(/as of/)).not.toBeInTheDocument();
  });

  it('renders one attribution line per source with its own vintage', () => {
    const withSource: MetricDisplayConfig[] = [
      ...METRICS,
      {
        key: 'affordable_share_pct',
        label: 'Affordable Listings (% at 60% AMI)',
        description: 'Share of listings affordable at 60% AMI.',
        show_in_table: true,
        as_of: '2026-07-28',
        source: 'Community Zillow survey',
      },
      {
        key: 'affordability_rank_change',
        label: 'Affordability Rank Change',
        description: 'Rank movement between surveys.',
        show_in_table: true,
        as_of: '2026-07-28',
        source: 'Community Zillow survey',
      },
    ];
    render(<MetricNotes metrics={withSource} metricsAsOf="2026-08-02" />);
    // Legacy line still present for the sourceless zoning metric...
    expect(screen.getByText('Zoning metric data as of 2026-08-02.')).toBeInTheDocument();
    // ...plus exactly one deduplicated line for the shared source.
    expect(
      screen.getAllByText('Community Zillow survey; data as of 2026-07-28.')
    ).toHaveLength(1);
  });

  it('omits the group vintage line when every visible metric has its own source', () => {
    const allSourced: MetricDisplayConfig[] = [
      {
        key: 'affordable_share_pct',
        label: 'Affordable Listings',
        description: 'Share of listings affordable at 60% AMI.',
        show_in_table: true,
        as_of: '2026-07-28',
        source: 'Community Zillow survey',
      },
    ];
    render(<MetricNotes metrics={allSourced} metricsAsOf="2026-08-02" />);
    expect(screen.queryByText(/Zoning metric data/)).not.toBeInTheDocument();
    expect(
      screen.getByText('Community Zillow survey; data as of 2026-07-28.')
    ).toBeInTheDocument();
  });
});
