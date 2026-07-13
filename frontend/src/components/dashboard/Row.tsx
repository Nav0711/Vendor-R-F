import { ExternalLink, CheckCircle2 } from 'lucide-react';

export const BoolCell = ({ ok, yes = 'Yes ✓', no = 'No ✗' }: { ok: boolean; yes?: string; no?: string }) => (
  <span className={`text-xs font-medium ${ok ? 'text-emerald-600' : 'text-red-600'}`}>
    {ok ? yes : no}
  </span>
);

export const OkBadge = ({ msg = 'Clear' }: { msg?: string }) => (
  <span className="text-emerald-600 flex items-center gap-1 text-xs font-medium">
    <CheckCircle2 className="w-3.5 h-3.5" /> {msg}
  </span>
);

export const ValidCell = ({ valid, status, ok = 'Active ✓', bad = 'Invalid ✗' }: {
  valid?: boolean; status?: string; ok?: string; bad?: string;
}) => (
  <span className={`font-medium text-xs ${valid ? 'text-emerald-600' : 'text-red-600'}`}>
    {status ?? (valid ? ok : bad)}
  </span>
);

const Row = ({
  label, value, link, linkLabel = 'View',
}: {
  label: string;
  value: React.ReactNode;
  link?: string;
  linkLabel?: string;
}) => (
  <div className="flex items-center py-2 px-4 border-b last:border-0 hover:bg-muted/20 gap-3 min-h-[36px]">
    <span className="text-xs text-muted-foreground w-32 shrink-0 font-medium">{label}</span>
    <span className="text-sm text-foreground flex-1 truncate">{value ?? '—'}</span>
    {link && (
      <a href={link} target="_blank" rel="noopener noreferrer"
        className="flex items-center gap-0.5 text-xs text-primary hover:underline shrink-0 font-medium whitespace-nowrap">
        {linkLabel} <ExternalLink className="w-3 h-3" />
      </a>
    )}
  </div>
);

export default Row;
