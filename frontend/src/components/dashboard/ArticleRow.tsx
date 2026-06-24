import { ExternalLink } from 'lucide-react';

const scoreColor = (score: number) =>
  score <= 33
    ? 'text-emerald-600 bg-emerald-50 border-emerald-200'
    : score <= 66
    ? 'text-yellow-600 bg-yellow-50 border-yellow-200'
    : 'text-red-600 bg-red-50 border-red-200';

const InsightBadge = ({ label, score }: { label: string; score: number }) => (
  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap shrink-0 ${scoreColor(score)}`}>
    {label} {score}%
  </span>
);

const ArticleRow = ({
  source, title, meta, url, summary, relevance, criticality,
}: {
  source: string;
  title?: string;
  meta?: string;
  url?: string;
  summary?: string;
  relevance?: number;
  criticality?: number;
}) => (
  <div className="border-b last:border-0">
    {/* Main article row */}
    <div className="flex items-center py-2 px-4 hover:bg-muted/20 gap-3 min-h-[36px]">
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

    {/* AI insight sub-row */}
    {summary && (
      <div className="flex items-center gap-2 px-4 py-1.5 bg-primary/5 text-xs text-muted-foreground">
        <span className="text-primary font-bold shrink-0">◆</span>
        <span className="flex-1 italic leading-snug">{summary}</span>
        {relevance  !== undefined && <InsightBadge label="Rel"  score={relevance} />}
        {criticality !== undefined && <InsightBadge label="Crit" score={criticality} />}
      </div>
    )}
  </div>
);

export default ArticleRow;
