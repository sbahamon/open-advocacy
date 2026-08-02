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
    expect(screen.getByText(/as of 2026-07-23/)).toBeInTheDocument();
  });

  it('omits the vintage line when not provided', () => {
    render(<MetricNotes metrics={METRICS} metricsAsOf={null} />);
    expect(screen.queryByText(/as of/)).not.toBeInTheDocument();
  });
});
