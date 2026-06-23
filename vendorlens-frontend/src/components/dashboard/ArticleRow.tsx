import { ExternalLink } from 'lucide-react';

const ArticleRow = ({
  source, title, meta, url,
}: {
  source: string; title?: string; meta?: string; url?: string;
}) => (
  <div className="flex items-center py-2 px-4 border-b last:border-0 hover:bg-muted/20 gap-3 min-h-[36px]">
    <span className="text-[9px] font-bold uppercase tracking-wider bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded w-[5.5rem] text-center shrink-0 truncate">
      {source}
    </span>
    <span className="text-sm text-foreground flex-1 line-clamp-1">{title ?? '—'}</span>
    {meta && (
      <span className="text-xs text-muted-foreground shrink-0 hidden sm:block whitespace-nowrap">{meta}</span>
    )}
    {url ? (
      <a href={url} target="_blank" rel="noopener noreferrer"
        className="flex items-center gap-0.5 text-xs text-primary hover:underline shrink-0">
        Read <ExternalLink className="w-3 h-3" />
      </a>
    ) : <span className="w-12 shrink-0" />}
  </div>
);

export default ArticleRow;
