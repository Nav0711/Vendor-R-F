import { ExternalLink } from 'lucide-react';

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
