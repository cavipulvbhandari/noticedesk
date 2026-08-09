-- V19: align documents_inbox with Java controller usage
-- Adds routing_error text column and 'rejected' routing_status value

ALTER TABLE documents_inbox
    ADD COLUMN IF NOT EXISTS routing_error TEXT;

-- Widen routing_status to include 'rejected'
ALTER TABLE documents_inbox
    DROP CONSTRAINT IF EXISTS documents_inbox_routing_status_check;

ALTER TABLE documents_inbox
    ADD CONSTRAINT documents_inbox_routing_status_check
    CHECK (routing_status IN (
        'pending', 'routed', 'client_not_found',
        'new_gst_registration_detected', 'pan_gstin_mismatch',
        'no_identifier_found', 'manual_assignment', 'rejected'
    ));
