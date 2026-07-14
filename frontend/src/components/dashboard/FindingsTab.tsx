import { ShieldCheck, ShieldAlert } from 'lucide-react';
import Section from './Section';
import FindingRow from './FindingRow';

const FindingsTab = ({ findings, findingsCount }: { findings: any[]; findingsCount: number }) => (
  <div className="animate-in fade-in duration-200">
    {findingsCount > 0 ? (
      <Section
        title={`${findingsCount} Adverse Finding${findingsCount !== 1 ? 's' : ''} — click a row for detail`}
        icon={<ShieldAlert className="w-4 h-4" />}>
        {findings.map((f: any) => (
          <FindingRow key={f.finding_id} finding={f} />
        ))}
      </Section>
    ) : (
      <div className="bg-primary/5 border border-primary/20 rounded-xl p-10 text-center space-y-3">
        <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
          <ShieldCheck className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-foreground">No Adverse Findings</h3>
          <p className="text-sm text-muted-foreground mt-1">All checks passed for this scan depth.</p>
        </div>
      </div>
    )}
  </div>
);

export default FindingsTab;
