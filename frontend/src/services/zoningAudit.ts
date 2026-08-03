import api from './api';
import { ZoningAuditResponse } from '../types';

export const zoningAuditService = {
  getZoningAudit: (groupSlug: string) =>
    api.get<ZoningAuditResponse>(`/scorecard/${groupSlug}/zoning-audit`),
};
