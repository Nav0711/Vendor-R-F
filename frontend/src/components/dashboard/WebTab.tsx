import { Star, Building2, AlertTriangle, Link2 } from 'lucide-react';
import Section from './Section';
import ArticleRow from './ArticleRow';
import Row from './Row';
import SectionInsight from './SectionInsight';
import { tryHost } from './utils';

const WebTab = ({ ss, report }: { ss: any; report: any }) => {
  const sa = report.section_analysis ?? {};
  return (
    <div className="space-y-4 animate-in fade-in duration-200">

      {/* Reviews — Trustpilot / Glassdoor / G2 */}
      <Section title="Customer & Employee Reviews" icon={<Star className="w-4 h-4" />}>
        {sa.reviews && <SectionInsight {...sa.reviews} />}
        {(ss.serper_reviews?.length ?? 0) > 0
          ? ss.serper_reviews.map((r: any, i: number) => (
              <ArticleRow key={i} source="Reviews"
                title={r.title} meta={tryHost(r.link)} url={r.link} />
            ))
          : <Row label="Status" value="No review results found" />}
      </Section>

      {/* Company Profile */}
      <Section title="Company Profile" icon={<Building2 className="w-4 h-4" />}>
        {sa.company_profile && <SectionInsight {...sa.company_profile} />}
        {(ss.serper_profile?.length ?? 0) > 0 ? ss.serper_profile.map((r: any, i: number) => (
          <div key={i}>
            <Row label="Result" value={r.title}
              link={r.link} linkLabel={tryHost(r.link) || 'Visit'} />
            {r.snippet && (
              <div className="px-4 py-1.5 text-xs text-muted-foreground border-b last:border-0 pl-[9rem] leading-relaxed">
                {r.snippet}
              </div>
            )}
          </div>
        )) : <Row label="Status" value="No profile results found" />}
      </Section>

      {/* Adverse Search */}
      <Section title="Adverse Web Search" icon={<AlertTriangle className="w-4 h-4" />}>
        {sa.adverse_web && <SectionInsight {...sa.adverse_web} />}
        {(ss.serper?.length ?? 0) > 0 ? ss.serper.map((r: any, i: number) => (
          <div key={i}>
            <Row label="Result" value={r.title}
              link={r.link} linkLabel={tryHost(r.link) || 'Visit'} />
            {r.snippet && (
              <div className="px-4 py-1.5 text-xs text-muted-foreground border-b last:border-0 pl-[9rem] leading-relaxed">
                {r.snippet}
              </div>
            )}
          </div>
        )) : <Row label="Status" value="No adverse search results found" />}
      </Section>

      {/* Website Metadata */}
      {ss.microlink && !ss.microlink.error && (
        <Section title="Website Metadata (Microlink)" icon={<Link2 className="w-4 h-4" />}>
          {sa.domain_ssl && <SectionInsight {...sa.domain_ssl} />}
          {ss.microlink.title && (
            <Row label="Title" value={ss.microlink.title}
              link={report.subject.domain?.startsWith('http')
                ? report.subject.domain
                : `https://${report.subject.domain}`}
              linkLabel="Visit" />
          )}
          {ss.microlink.description && <Row label="Description" value={ss.microlink.description} />}
          {ss.microlink.publisher  && <Row label="Publisher"   value={ss.microlink.publisher} />}
          <Row label="Status"       value={ss.microlink.status ?? '—'} />
        </Section>
      )}

    </div>
  );
};

export default WebTab;
