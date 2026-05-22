/**
 * Shared type definitions per §5 of the implementation prompt.
 * Concrete persistence lives in src/lib/storage/db.ts.
 */
export type Portal = 'IT' | 'GST';

export type NoticeCategory = 'Notice' | 'Intimation' | 'Order' | 'Reply' | 'Submission';

export interface Client {
  id: string;
  type: Portal;
  identifier: string;
  legalName: string;
  tradeName?: string;
  lastSyncedAt?: number;
}

export interface NoticeRecord {
  id: string;
  clientId: string;
  portal: Portal;
  category: NoticeCategory;
  formOrSection: string;
  referenceNumber: string;
  taxPeriod: string;
  issuedOn: string;
  dueOn?: string;
  status: string;
  sourceUrl: string;
  localFilePath?: string;
  capturedAt: number;
  syncedAt?: number;
  rawDom?: string;
}
