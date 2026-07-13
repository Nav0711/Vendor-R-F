export const RISK: Record<string, { badge: string; dot: string }> = {
  CRITICAL: { badge: 'bg-red-50 text-red-700 border-red-200',    dot: 'bg-red-500' },
  HIGH:     { badge: 'bg-orange-50 text-orange-700 border-orange-200', dot: 'bg-orange-500' },
  MEDIUM:   { badge: 'bg-yellow-50 text-yellow-700 border-yellow-200', dot: 'bg-yellow-500' },
  LOW:      { badge: 'bg-blue-50 text-blue-700 border-blue-200', dot: 'bg-blue-500' },
  CLEAN:    { badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500' },
};

export const getRisk = (lvl?: string) => RISK[lvl ?? ''] ?? RISK.CLEAN;

export function tryHost(url?: string) {
  try { return url ? new URL(url).hostname.replace(/^www\./, '') : ''; } catch { return ''; }
}

// Friendly display name for a link's source, e.g. "Economic Times", "Instagram".
const KNOWN_SITES: Record<string, string> = {
  'instagram.com': 'Instagram',
  'linkedin.com': 'LinkedIn',
  'facebook.com': 'Facebook',
  'twitter.com': 'X (Twitter)',
  'x.com': 'X (Twitter)',
  'youtube.com': 'YouTube',
  'economictimes.indiatimes.com': 'Economic Times',
  'timesofindia.indiatimes.com': 'Times of India',
  'indiatimes.com': 'Times of India',
  'business-standard.com': 'Business Standard',
  'moneycontrol.com': 'Moneycontrol',
  'livemint.com': 'Mint',
  'thehindu.com': 'The Hindu',
  'hindustantimes.com': 'Hindustan Times',
  'reuters.com': 'Reuters',
  'bloomberg.com': 'Bloomberg',
  'trustpilot.com': 'Trustpilot',
  'glassdoor.com': 'Glassdoor',
  'glassdoor.co.in': 'Glassdoor',
  'g2.com': 'G2',
  'ambitionbox.com': 'AmbitionBox',
  'justdial.com': 'Justdial',
  'indiamart.com': 'IndiaMART',
  'tradeindia.com': 'TradeIndia',
  'fssai.gov.in': 'FSSAI',
  'foscos.fssai.gov.in': 'FSSAI (FoSCoS)',
  'cpcb.nic.in': 'CPCB',
  'greentribunal.gov.in': 'NGT',
  'peso.gov.in': 'PESO',
  'bis.gov.in': 'BIS',
  'opencorporates.com': 'OpenCorporates',
  'opensanctions.org': 'OpenSanctions',
  'en.wikipedia.org': 'Wikipedia',
  'wikipedia.org': 'Wikipedia',
};

const COMPOUND_TLDS = new Set(['co.in', 'gov.in', 'nic.in', 'org.in', 'net.in', 'co.uk', 'com.au', 'co.jp']);

export function siteName(url?: string): string {
  const host = tryHost(url);
  if (!host) return '';
  const bare = host.replace(/^(m|amp|mobile)\./, '');
  if (KNOWN_SITES[bare]) return KNOWN_SITES[bare];
  const parts = bare.split('.');
  // registrable label = the brand label just left of the public suffix
  let label = parts[0];
  if (parts.length >= 3 && COMPOUND_TLDS.has(parts.slice(-2).join('.'))) {
    label = parts[parts.length - 3];
  } else if (parts.length >= 2) {
    label = parts[parts.length - 2];
  }
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : bare;
}
