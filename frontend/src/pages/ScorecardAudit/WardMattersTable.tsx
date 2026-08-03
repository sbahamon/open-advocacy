import React, { useState } from 'react';
import {
  Chip,
  Link as MuiLink,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip,
  Typography,
} from '@mui/material';
import { ZoningAuditMatter } from '../../types';

interface WardMattersTableProps {
  ward: number;
  matters: ZoningAuditMatter[];
}

const ELMS_MATTER_URL = 'https://chicityclerkelms.chicago.gov/Matter/?matterId=';

function formatDate(value?: string | null): string {
  return value ? value.slice(0, 10) : '—';
}

/** Drill-down table of the matters behind one ward's delay statistics. */
const WardMattersTable: React.FC<WardMattersTableProps> = ({ ward, matters }) => {
  const [sortDesc, setSortDesc] = useState(true);

  if (matters.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ mt: 2 }}>
        No zoning reclassifications recorded for Ward {ward}.
      </Typography>
    );
  }

  const sorted = [...matters].sort((a, b) => {
    const spanA = a.span_days ?? -1;
    const spanB = b.span_days ?? -1;
    return sortDesc ? spanB - spanA : spanA - spanB;
  });

  return (
    <TableContainer sx={{ mt: 2, overflowX: 'auto' }}>
      <Table size="small" aria-label={`Ward ${ward} zoning matters`}>
        <TableHead>
          <TableRow>
            <TableCell>Record</TableCell>
            <TableCell>Address</TableCell>
            <TableCell>Introduced</TableCell>
            <TableCell>Final action</TableCell>
            <TableCell align="right" sortDirection={sortDesc ? 'desc' : 'asc'}>
              <TableSortLabel
                active
                direction={sortDesc ? 'desc' : 'asc'}
                onClick={() => setSortDesc(d => !d)}
              >
                Days
              </TableSortLabel>
            </TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Flags</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sorted.map(matter => (
            <TableRow key={matter.record_number || matter.matter_guid} hover>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                <MuiLink
                  href={`${ELMS_MATTER_URL}${matter.matter_guid}`}
                  target="_blank"
                  rel="noopener"
                >
                  {matter.record_number || '—'}
                </MuiLink>
              </TableCell>
              <TableCell>
                <Tooltip title={matter.title ?? ''}>
                  <span>{matter.address ?? '—'}</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                {formatDate(matter.introduction_date)}
              </TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                {formatDate(matter.final_action_date)}
              </TableCell>
              <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                {matter.span_days ?? '—'}
              </TableCell>
              <TableCell>{matter.status ?? '—'}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                {matter.stalled && (
                  <Chip label="stalled" color="warning" size="small" sx={{ mr: 0.5 }} />
                )}
                {matter.withdrawn && (
                  <Chip label="withdrawn" size="small" sx={{ mr: 0.5 }} />
                )}
                {matter.near_boundary && (
                  <Tooltip title="Within 30 m of a ward boundary — reassignment risk under the simplified ward polygons.">
                    <Chip label="near boundary" size="small" variant="outlined" />
                  </Tooltip>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default WardMattersTable;
