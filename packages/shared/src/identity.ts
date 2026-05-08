// PAN-centric identity helpers, shared between web and api.
//
// PAN format: 5 letters + 4 digits + 1 letter (10 chars).
// GSTIN format: 2-digit state code + PAN + 1 alphanumeric entity number +
//               'Z' + 1 alphanumeric checksum (15 chars).

export const PAN_REGEX = /^[A-Z]{5}[0-9]{4}[A-Z]$/;
export const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$/;

export function validatePanFormat(pan: string): boolean {
  return PAN_REGEX.test(pan);
}

export function validateGstinFormat(gstin: string): boolean {
  return GSTIN_REGEX.test(gstin);
}

export function extractPanFromGstin(gstin: string): string {
  if (!validateGstinFormat(gstin)) {
    throw new Error(`invalid GSTIN: ${gstin}`);
  }
  // GSTIN positions 3-12 (1-indexed) === substring(2, 12) (0-indexed).
  return gstin.substring(2, 12);
}

export function extractStateCodeFromGstin(gstin: string): string {
  if (!validateGstinFormat(gstin)) {
    throw new Error(`invalid GSTIN: ${gstin}`);
  }
  return gstin.substring(0, 2);
}

export function reconcilePanGstin(pan: string, gstin: string): boolean {
  if (!validatePanFormat(pan) || !validateGstinFormat(gstin)) {
    return false;
  }
  return extractPanFromGstin(gstin) === pan;
}
