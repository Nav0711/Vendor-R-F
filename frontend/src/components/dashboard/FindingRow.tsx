import { useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { getRisk } from './utils';

const FindingRow = ({ finding }: { finding: any }) => {
  const [open, setOpen] = useState(false);
  const s = getRisk(finding.severity?.toUpperCase?.());
  return (
    <div className="border-b last:border-0">
      <div
        className="flex items-center py-2.5 px-4 hover:bg-muted/20 gap-3 cursor-pointer select-none min-h-[40px]"
        onClick={() => setOpen(o => !o)}
      >
        <div className={`w-2 h-2 rounded-full shrink-0 ${s.dot}`} />
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border shrink-0 w-16 text-center ${s.badge}`}>
          {finding.severity?.toUpperCase?.()}
        </span>
        <span className="text-sm font-medium text-foreground flex-1 line-clamp-1">{finding.title}</span>
        <span className="text-[9px] uppercase tracking-wider text-muted-foreground bg-secondary px-1.5 py-0.5 rounded shrink-0 hidden sm:block whitespace-nowrap">
          {(finding.category ?? '').replace(/_/g, ' ')}
        </span>
        <span className="text-xs text-muted-foreground shrink-0 hidden md:block whitespace-nowrap">
          {finding.evidence?.source_name ?? finding.evidence?.source_tool}
        </span>
        {open
          ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
          : <ChevronRight className="w-3.5 h-3.5 text-muted-foreground shrink-0" />}
      </div>
      {open && (
        <div className="mx-4 mb-2.5 px-3 py-2 bg-muted/30 rounded-lg border text-xs text-muted-foreground leading-relaxed space-y-2">
          <p>{finding.detail}</p>
          {finding.evidence?.source_url && (
            <a href={finding.evidence.source_url} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-primary hover:underline font-medium w-fit">
              <ExternalLink className="w-3 h-3" /> View source
            </a>
          )}
        </div>
      )}
    </div>
  );
};

export default FindingRow;
