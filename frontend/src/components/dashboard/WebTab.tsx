import { Star, Building2, AlertTriangle, Link2 } from 'lucide-react';
import Section from './Section';
import ArticleRow from './ArticleRow';
import Row from './Row';
import SectionInsight from './SectionInsight';
import FilterNote from './FilterNote';
import { tryHost, siteName } from './utils';

const SearchResults = ({ items, emptyMsg }: { items: any[]; emptyMsg: string }) =>
  items.length > 0 ? (
    <>{items.map((r: any, i: number) => (
      <div key={i}>
        <Row label="Result" value={r.title} link={r.link} linkLabel={siteName(r.link) || 'Visit'} />
        {r.snippet && (
          <div className="px-4 py-1.5 text-xs text-muted-foreground border-b last:border-0 pl-[9rem] leading-relaxed">
            {r.snippet}
          </div>
        )}
      </div>
    ))}</>
  ) : <Row label="Status" value={emptyMsg} />;

const WebTab = ({ ss, report }: { ss: any; report: any }) => {
  const sa = report.section_analysis ?? {};
  const aiUnavailable = !!(report.section_analysis?._ai_unavailable);
  const cf = ss.category_filter ?? {};
  const siteUrl = report.subject.domain?.startsWith('http')
    ? report.subject.domain
    : `https://${report.subject.domain}`;

  const Insight = ({ sectionKey }: { sectionKey: string }) =>
    aiUnavailable
      ? <SectionInsight unavailable />
      : sa[sectionKey] ? <SectionInsight {...sa[sectionKey]} /> : null;

  return (
    <div className="space-y-4 animate-in fade-in duration-200">

      <Section title="Customer & Employee Reviews" icon={<Star className="w-4 h-4" />}>
        <Insight sectionKey="reviews" />
        {cf.reviews_fallback && <FilterNote bucket={cf.bucket} />}
        {(ss.serper_reviews?.length ?? 0) > 0
          ? ss.serper_reviews.map((r: any, i: number) => (
              <ArticleRow key={i} source="Reviews" title={r.title} meta={tryHost(r.link)} url={r.link} />
            ))
          : <Row label="Status" value="No review results found" />}
      </Section>

      <Section title="Company Profile" icon={<Building2 className="w-4 h-4" />}>
        <Insight sectionKey="company_profile" />
        {cf.profile_fallback && <FilterNote bucket={cf.bucket} />}
        <SearchResults items={ss.serper_profile ?? []} emptyMsg="No profile results found" />
      </Section>

      <Section title="Adverse Web Search" icon={<AlertTriangle className="w-4 h-4" />}>
        <Insight sectionKey="adverse_web" />
        {cf.adverse_fallback && <FilterNote bucket={cf.bucket} />}
        <SearchResults items={ss.serper_adverse_all ?? ss.serper ?? []} emptyMsg="No adverse search results found" />
      </Section>

      {ss.microlink && !ss.microlink.error && (
        <Section title="Website Metadata (Microlink)" icon={<Link2 className="w-4 h-4" />}>
          <Insight sectionKey="domain_ssl" />
          {ss.microlink.title       && <Row label="Title"       value={ss.microlink.title} link={siteUrl} linkLabel="Visit" />}
          {ss.microlink.description && <Row label="Description" value={ss.microlink.description} />}
          {ss.microlink.publisher   && <Row label="Publisher"   value={ss.microlink.publisher} />}
          <Row label="Status" value={ss.microlink.status ?? '—'} />
        </Section>
      )}

    </div>
  );
};

export default WebTab;
