import { Info } from 'lucide-react';

// Shown above a list when strict category filtering matched nothing and we fell
// back to showing all results, so the tab is never unexpectedly empty.
const FilterNote = ({ bucket }: { bucket?: string }) => (
  <div className="flex items-center gap-1.5 px-4 py-2 text-xs text-muted-foreground bg-muted/30 border-b">
    <Info className="w-3.5 h-3.5 shrink-0" />
    No strong{bucket ? ` “${bucket.replace(/_/g, ' ')}”` : ''} category match — showing all results.
  </div>
);

export default FilterNote;
