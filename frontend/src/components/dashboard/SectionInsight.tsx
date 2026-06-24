const scoreColor = (score: number) =>
  score <= 33 ? 'bg-emerald-500' : score <= 66 ? 'bg-yellow-500' : 'bg-red-500';

const ScoreBar = ({ label, score }: { label: string; score: number }) => (
  <div className="flex items-center gap-2">
    <span className="text-[10px] text-muted-foreground uppercase tracking-wider whitespace-nowrap w-14 shrink-0">{label}</span>
    <div className="w-20 h-1.5 bg-secondary rounded-full overflow-hidden shrink-0">
      <div className={`h-full rounded-full ${scoreColor(score)}`} style={{ width: `${score}%` }} />
    </div>
    <span className="text-[10px] font-bold text-foreground w-7 text-right shrink-0">{score}%</span>
  </div>
);

const SectionInsight = ({
  summary, relevance, criticality,
}: {
  summary: string; relevance: number; criticality: number;
}) => (
  <div className="flex flex-col sm:flex-row sm:items-center gap-2.5 px-4 py-2.5 bg-primary/5 border-b">
    <span className="text-xs text-foreground/80 flex-1 italic leading-snug">
      <span className="text-primary font-bold mr-1.5">◆</span>{summary}
    </span>
    <div className="flex flex-col gap-1 shrink-0">
      <ScoreBar label="Relevance"   score={relevance} />
      <ScoreBar label="Criticality" score={criticality} />
    </div>
  </div>
);

export default SectionInsight;
