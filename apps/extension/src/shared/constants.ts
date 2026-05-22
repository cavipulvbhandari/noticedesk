export const GST_PORTAL_HOSTS = ['gst.gov.in', 'www.gst.gov.in', 'services.gst.gov.in'] as const;
export const IT_PORTAL_HOSTS = ['incometax.gov.in', 'www.incometax.gov.in'] as const;

export type Portal = 'IT' | 'GST';

export function classifyHost(hostname: string): Portal | null {
  if ((GST_PORTAL_HOSTS as readonly string[]).includes(hostname) || hostname.endsWith('.gst.gov.in')) {
    return 'GST';
  }
  if (
    (IT_PORTAL_HOSTS as readonly string[]).includes(hostname) ||
    hostname.endsWith('.incometax.gov.in')
  ) {
    return 'IT';
  }
  return null;
}
