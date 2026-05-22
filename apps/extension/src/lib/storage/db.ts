import Dexie, { type EntityTable } from 'dexie';
import type { Client, NoticeRecord } from '@/shared/types';

/**
 * Local-first notice register. Idempotency key for NoticeRecord:
 * `${portal}:${referenceNumber}` — see §5 of the implementation prompt.
 *
 * Phase 1 ships the schema only; no writes happen until scrapers land.
 */
export class NoticeDeskDB extends Dexie {
  clients!: EntityTable<Client, 'id'>;
  notices!: EntityTable<NoticeRecord, 'id'>;

  constructor() {
    super('NoticeDesk');
    this.version(1).stores({
      clients: 'id, type, identifier, lastSyncedAt',
      notices:
        'id, clientId, portal, category, formOrSection, referenceNumber, issuedOn, dueOn, status, capturedAt, syncedAt, &[portal+referenceNumber]',
    });
  }
}

export const db = new NoticeDeskDB();
