import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import WardMattersTable from './WardMattersTable';
import { ZoningAuditMatter } from '../../types';

const MATTERS: ZoningAuditMatter[] = [
  {
    record_number: 'O2026-0000001',
    matter_guid: 'guid-1',
    title: 'Zoning Reclassification at 1 N Test St',
    address: '1 N Test St',
    introduction_date: '2026-01-21T00:00:00',
    final_action_date: '2026-03-21T00:00:00',
    status: '90-Final',
    sub_status: null,
    lat: 41.9,
    lon: -87.7,
    near_boundary: true,
    span_days: 59,
    stalled: false,
    pending: false,
    withdrawn: false,
  },
  {
    record_number: 'O2025-0000002',
    matter_guid: 'guid-2',
    title: 'Zoning Reclassification at 2 S Test Ave',
    address: '2 S Test Ave',
    introduction_date: '2025-01-01T00:00:00',
    final_action_date: null,
    status: '4-In Committee',
    sub_status: null,
    lat: null,
    lon: null,
    near_boundary: false,
    span_days: null,
    stalled: true,
    pending: true,
    withdrawn: false,
  },
];

describe('WardMattersTable', () => {
  it('renders one row per matter with dates and span', () => {
    render(<WardMattersTable ward={35} matters={MATTERS} />);
    expect(screen.getByText('O2026-0000001')).toBeInTheDocument();
    expect(screen.getByText('2026-01-21')).toBeInTheDocument();
    expect(screen.getByText('59')).toBeInTheDocument();
  });

  it('links each record number to its eLMS matter page', () => {
    render(<WardMattersTable ward={35} matters={MATTERS} />);
    const link = screen.getByRole('link', { name: 'O2026-0000001' });
    expect(link).toHaveAttribute('href', expect.stringContaining('guid-1'));
  });

  it('flags stalled and near-boundary matters, with em dash for pending final action', () => {
    render(<WardMattersTable ward={35} matters={MATTERS} />);
    expect(screen.getByText('stalled')).toBeInTheDocument();
    expect(screen.getByText('near boundary')).toBeInTheDocument();
    const pendingRow = screen.getByText('O2025-0000002').closest('tr');
    expect(pendingRow).toHaveTextContent('—');
  });

  it('renders an empty state when the ward has no matters', () => {
    render(<WardMattersTable ward={13} matters={[]} />);
    expect(
      screen.getByText(/No zoning reclassifications recorded for Ward 13/)
    ).toBeInTheDocument();
  });
});
