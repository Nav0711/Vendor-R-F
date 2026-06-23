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
