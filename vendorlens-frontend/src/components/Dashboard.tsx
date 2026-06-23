import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  ArrowLeft, XCircle, ExternalLink, Building2, Globe, ShieldCheck,
  Landmark, ShieldAlert, Newspaper, MapPin, BadgeCheck,
  AlertTriangle, Star, Link2, FileText, CheckCircle2,
  ChevronDown, ChevronRight,
} from 'lucide-react';

type TabKey = 'overview' | 'findings' | 'news' | 'web' | 'india';

// ── Risk helpers ──────────────────────────────────────────────────────────────
const RISK: Record<string, { badge: string; dot: string }> = {
  CRITICAL: { badge: 'bg-red-50 text-red-700 border-red-200',    dot: 'bg-red-500' },
  HIGH:     { badge: 'bg-orange-50 text-orange-700 border-orange-200', dot: 'bg-orange-500' },
  MEDIUM:   { badge: 'bg-yellow-50 text-yellow-700 border-yellow-200', dot: 'bg-yellow-500' },
  LOW:      { badge: 'bg-blue-50 text-blue-700 border-blue-200', dot: 'bg-blue-500' },
  CLEAN:    { badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500' },
};
const getRisk = (lvl?: string) => RISK[lvl ?? ''] ?? RISK.CLEAN;

function tryHost(url?: string) {
  try { return url ? new URL(url).hostname.replace(/^www\./, '') : ''; } catch { return ''; }
}

// ── Reusable atoms ────────────────────────────────────────────────────────────

/** Single horizontal data row: label | value | optional link */
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

/** News / article row: source badge | title | hostname | link */
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

/** Finding row with expandable detail */
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
        <div className="mx-4 mb-2.5 px-3 py-2 bg-muted/30 rounded-lg border text-xs text-muted-foreground leading-relaxed">
          {finding.detail}
        </div>
      )}
    </div>
  );
};

/** Section wrapper: thin header + row children */
const Section = ({
  title, icon, children,
}: {
  title: string; icon: React.ReactNode; children: React.ReactNode;
}) => (
  <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
    <div className="flex items-center gap-2 px-4 py-2.5 border-b bg-muted/30">
      <span className="text-primary">{icon}</span>
      <span className="text-sm font-semibold text-foreground">{title}</span>
    </div>
    {children}
  </div>
);

// ── Main component ────────────────────────────────────────────────────────────
const Dashboard = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus]   = useState('PENDING');
  const [report, setReport]   = useState<any>(null);
  const [tab, setTab]         = useState<TabKey>('overview');

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    const check = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/scan/${scanId}/status`);
        setStatus(res.data.status);
        if (res.data.status === 'COMPLETED') {
          clearInterval(interval);
          const rep = await axios.get(`http://localhost:8000/scan/${scanId}/report`);
          setReport(rep.data);
        }
      } catch (err) { console.error(err); }
    };
    check();
    if (status !== 'COMPLETED') interval = setInterval(check, 3000);
    return () => clearInterval(interval);
  }, [scanId, status]);

  // ── Loading state ──────────────────────────────────────────────────────────
  if (status !== 'COMPLETED') {
    return (
      <div className="max-w-xl mx-auto mt-20 p-8 bg-card border rounded-2xl shadow-sm text-center space-y-5">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">Scan in Progress</h2>
          <p className="text-sm text-muted-foreground mt-1">
            AI agents are querying multiple data sources…
          </p>
        </div>
        <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
          <div className="bg-primary h-1.5 rounded-full animate-pulse w-3/5" />
        </div>
        <button onClick={() => navigate('/')}
          className="inline-flex items-center text-sm text-muted-foreground hover:text-destructive transition-colors">
          <XCircle className="w-4 h-4 mr-1.5" /> Cancel
        </button>
      </div>
    );
  }

  if (!report) return null;

  // ── Derived data ───────────────────────────────────────────────────────────
  const ss            = report.sources_summary ?? {};
  const riskLevel     = report.risk_summary?.overall_risk_level ?? 'UNKNOWN';
  const riskStyles    = getRisk(riskLevel);
  const findingsCount = report.adverse_findings?.length ?? 0;
  const hasIndia      = !!(ss.sandbox_tsp || ss.sandbox_intel);

  // Flatten all news from every source into one list
  const allNews: { source: string; title: string; meta: string; url: string }[] = [
    ...(ss.gdelt         ?? []).map((a: any) => ({ source: 'GDELT',      title: a.title, meta: a.domain,  url: a.url  })),
    ...(ss.newsapi       ?? []).map((a: any) => ({ source: 'NewsAPI',    title: a.title, meta: a.source,  url: a.url  })),
    ...(ss.newsapi_regulatory ?? []).map((a: any) => ({ source: 'Regulatory', title: a.title, meta: a.source, url: a.url })),
    ...(ss.serper_news   ?? []).map((a: any) => ({ source: 'Google',     title: a.title, meta: tryHost(a.link), url: a.link })),
  ].filter(a => a.title);

  // Enrichment news (alternate names via GDELT in sandbox phase 2)
  for (const [name, data] of Object.entries(
    (ss.sandbox_enrichment?.alternate_names_searched ?? {}) as Record<string, any>
  )) {
    for (const item of data.gdelt_results ?? []) {
      if (item.title) allNews.push({
        source: `GDELT·${name.split(' ')[0]}`, title: item.title, meta: item.domain, url: item.url,
      });
    }
  }

  const tabs: { key: TabKey; label: string; count?: number }[] = [
    { key: 'overview',  label: 'Overview' },
    { key: 'findings',  label: 'Findings',     count: findingsCount },
    { key: 'news',      label: 'News & Media',  count: allNews.length },
    { key: 'web',       label: 'Web & Reviews' },
    ...(hasIndia ? [{ key: 'india' as TabKey, label: 'India Verification' }] : []),
  ];

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto space-y-4 pb-12">
      {/* Back */}
      <button onClick={() => navigate('/')}
        className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors">
        <ArrowLeft className="w-4 h-4 mr-1" /> Back
      </button>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="bg-card border rounded-xl px-5 py-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            {report.subject.legal_name ?? 'Unknown Entity'}
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-2">
            <Building2 className="w-3.5 h-3.5" />
            {report.subject.scan_type?.toUpperCase()} SCAN
            {report.subject.domain && (
              <span className="border rounded px-1.5 py-0.5 font-mono text-[10px]">
                {report.subject.domain}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Risk badge */}
          <div className={`px-3 py-1.5 rounded-lg border font-bold text-sm flex items-center gap-2 ${riskStyles.badge}`}>
            <div className={`w-2 h-2 rounded-full animate-pulse ${riskStyles.dot}`} />
            {riskLevel} RISK
          </div>
          {/* Stats */}
          {[
            { label: 'Findings', value: findingsCount },
            { label: 'Tokens Used', value: (report.tokens_used ?? 0).toLocaleString() },
            { label: 'Balance', value: (report.tokens_remaining ?? 0).toLocaleString() },
          ].map(s => (
            <div key={s.label} className="text-center hidden sm:block">
              <div className="text-base font-bold text-foreground">{s.value}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tab bar ─────────────────────────────────────────────────────────── */}
      <div className="flex gap-0 border-b border-border overflow-x-auto">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5 ${
              tab === t.key
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}>
            {t.label}
            {(t.count ?? 0) > 0 && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                t.key === 'findings'
                  ? 'bg-destructive text-destructive-foreground'
                  : 'bg-secondary text-secondary-foreground'
              }`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════════════════
          TAB: OVERVIEW
      ════════════════════════════════════════════════════════════════════ */}
      {tab === 'overview' && (
        <div className="space-y-4 animate-in fade-in duration-200">

          <div className="grid sm:grid-cols-2 gap-4">
            {/* Corporate Registry */}
            <Section title="Corporate Registry" icon={<Landmark className="w-4 h-4" />}>
              {(ss.opencorporates?.length ?? 0) > 0 ? ss.opencorporates.map((c: any, i: number) => (
                <div key={i}>
                  <Row label="Company"       value={c.name}
                    link={`https://opencorporates.com/companies/${c.jurisdiction_code?.toLowerCase()}/${c.company_number}`}
                    linkLabel="OpenCorporates" />
                  <Row label="Reg Number"    value={c.company_number} />
                  <Row label="Jurisdiction"  value={c.jurisdiction_code?.toUpperCase()} />
                  <Row label="Type"          value={c.company_type} />
                  <Row label="Status"        value={
                    <span className={`flex items-center gap-1 font-medium text-xs ${
                      c.current_status === 'Active' ? 'text-emerald-600' : 'text-red-600'
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        c.current_status === 'Active' ? 'bg-emerald-500' : 'bg-red-500'
                      }`} />
                      {c.current_status ?? 'Unknown'}
                    </span>
                  } />
                  {c.incorporation_date && (
                    <Row label="Incorporated" value={new Date(c.incorporation_date).toLocaleDateString()} />
                  )}
                </div>
              )) : (
                <Row label="Status" value="No registry data found" />
              )}
            </Section>

            {/* Sanctions & Watchlists */}
            <Section title="Sanctions & Watchlists" icon={<ShieldAlert className="w-4 h-4" />}>
              {ss.opensanctions?.some((s: any) => s.caption) ? (
                ss.opensanctions.filter((s: any) => s.caption).map((s: any, i: number) => (
                  <div key={i}>
                    <Row label="Match" value={s.caption}
                      link={`https://www.opensanctions.org/search/?q=${encodeURIComponent(s.caption ?? '')}`}
                      linkLabel="OpenSanctions" />
                    <Row label="Schema"  value={s.schema} />
                    {s.properties?.country && <Row label="Country" value={s.properties.country.join(', ')} />}
                    {s.properties?.status  && <Row label="Status"  value={s.properties.status.join(', ')} />}
                  </div>
                ))
              ) : (
                <Row label="Status" value={
                  <span className="text-emerald-600 flex items-center gap-1 font-medium text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5" /> No watchlist matches
                  </span>
                } />
              )}
            </Section>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            {/* Domain & SSL */}
            <Section title="Domain & SSL" icon={<Globe className="w-4 h-4" />}>
              {ss.whois && (
                <>
                  <Row label="Domain"    value={Array.isArray(ss.whois.domain_name) ? ss.whois.domain_name[0] : ss.whois.domain_name}
                    link={`https://whois.domaintools.com/${report.subject.domain}`} linkLabel="WHOIS" />
                  <Row label="Registrar" value={ss.whois.registrar} />
                  <Row label="Created"   value={ss.whois.creation_date   ? new Date(ss.whois.creation_date).toLocaleDateString()   : '—'} />
                  <Row label="Expires"   value={ss.whois.expiration_date ? new Date(ss.whois.expiration_date).toLocaleDateString() : '—'} />
                </>
              )}
              {ss.ssl && (
                <>
                  <Row label="SSL" value={
                    <span className={`font-medium text-xs ${ss.ssl.has_ssl && !ss.ssl.is_expired ? 'text-emerald-600' : 'text-red-600'}`}>
                      {ss.ssl.has_ssl ? (ss.ssl.is_expired ? 'Expired' : 'Valid ✓') : 'No SSL ✗'}
                    </span>
                  }
                    link={`https://www.ssllabs.com/ssltest/analyze.html?d=${report.subject.domain}`}
                    linkLabel="SSL Labs" />
                  <Row label="Issuer"    value={ss.ssl.issuer} />
                </>
              )}
              {ss.microlink?.title && (
                <Row label="Site Title" value={ss.microlink.title}
                  link={report.subject.domain?.startsWith('http')
                    ? report.subject.domain
                    : `https://${report.subject.domain}`}
                  linkLabel="Visit" />
              )}
              {!ss.whois && !ss.ssl && <Row label="Status" value="No domain provided" />}
            </Section>

            {/* Physical Address */}
            <Section title="Physical Address" icon={<MapPin className="w-4 h-4" />}>
              {(ss.google_places?.length ?? 0) > 0 ? ss.google_places.map((p: any, i: number) => (
                <div key={i}>
                  <Row label="Name"    value={p.name} />
                  <Row label="Address" value={p.formatted_address} />
                  <Row label="Status"  value={
                    <span className={`font-medium text-xs ${
                      p.business_status === 'OPERATIONAL' ? 'text-emerald-600' : 'text-orange-600'
                    }`}>
                      {p.business_status ?? 'Unknown'}
                    </span>
                  }
                    link={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                      (p.name ?? '') + ' ' + (p.formatted_address ?? '')
                    )}`}
                    linkLabel="Maps" />
                  {p.rating && <Row label="Rating" value={`${p.rating} ★`} />}
                </div>
              )) : (
                <Row label="Address" value="No location data found" />
              )}
            </Section>
          </div>

          {/* Wikipedia */}
          {ss.wikipedia?.found && (
            <Section title="Wikipedia" icon={<FileText className="w-4 h-4" />}>
              <Row label="Article"     value={ss.wikipedia.title}
                link={ss.wikipedia.page_url} linkLabel="Wikipedia" />
              {ss.wikipedia.description && <Row label="Description" value={ss.wikipedia.description} />}
              {ss.wikipedia.summary && (
                <div className="px-4 py-2.5 text-xs text-muted-foreground leading-relaxed border-t pl-[9rem]">
                  {ss.wikipedia.summary.slice(0, 350)}{ss.wikipedia.summary.length > 350 ? '…' : ''}
                </div>
              )}
            </Section>
          )}

        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB: FINDINGS
      ════════════════════════════════════════════════════════════════════ */}
      {tab === 'findings' && (
        <div className="animate-in fade-in duration-200">
          {findingsCount > 0 ? (
            <Section
              title={`${findingsCount} Adverse Finding${findingsCount !== 1 ? 's' : ''} — click a row for detail`}
              icon={<ShieldAlert className="w-4 h-4" />}>
              {report.adverse_findings.map((f: any) => (
                <FindingRow key={f.finding_id} finding={f} />
              ))}
            </Section>
          ) : (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-10 text-center space-y-3">
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
                <ShieldCheck className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-emerald-800">No Adverse Findings</h3>
                <p className="text-sm text-emerald-700 mt-1">All checks passed for this scan depth.</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB: NEWS & MEDIA
      ════════════════════════════════════════════════════════════════════ */}
      {tab === 'news' && (
        <div className="animate-in fade-in duration-200">
          <Section
            title={`${allNews.length} News & Media Result${allNews.length !== 1 ? 's' : ''}`}
            icon={<Newspaper className="w-4 h-4" />}>
            {allNews.length > 0
              ? allNews.map((a, i) => (
                  <ArticleRow key={i} source={a.source} title={a.title} meta={a.meta} url={a.url} />
                ))
              : <Row label="Status" value="No news articles found across all sources" />}
          </Section>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB: WEB & REVIEWS
      ════════════════════════════════════════════════════════════════════ */}
      {tab === 'web' && (
        <div className="space-y-4 animate-in fade-in duration-200">

          {/* Reviews — Trustpilot / Glassdoor / G2 */}
          <Section title="Customer & Employee Reviews" icon={<Star className="w-4 h-4" />}>
            {(ss.serper_reviews?.length ?? 0) > 0
              ? ss.serper_reviews.map((r: any, i: number) => (
                  <ArticleRow key={i} source="Reviews"
                    title={r.title} meta={tryHost(r.link)} url={r.link} />
                ))
              : <Row label="Status" value="No review results found" />}
          </Section>

          {/* Company Profile */}
          <Section title="Company Profile" icon={<Building2 className="w-4 h-4" />}>
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
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB: INDIA VERIFICATION
      ════════════════════════════════════════════════════════════════════ */}
      {tab === 'india' && (
        <div className="space-y-4 animate-in fade-in duration-200">

          {/* Sandbox TSP — live verification */}
          <Section title="Regulatory Verification (Sandbox TSP)" icon={<ShieldCheck className="w-4 h-4" />}>
            {ss.sandbox_tsp?.gstin ? (
              <>
                <Row label="GSTIN"       value={ss.sandbox_tsp.gstin.gstin} />
                <Row label="GSTIN Status" value={
                  <span className={`font-medium text-xs ${ss.sandbox_tsp.gstin.valid ? 'text-emerald-600' : 'text-red-600'}`}>
                    {ss.sandbox_tsp.gstin.status ?? (ss.sandbox_tsp.gstin.valid ? 'Active ✓' : 'Invalid ✗')}
                  </span>
                } link="https://services.gst.gov.in/services/searchtp" linkLabel="GST Portal" />
                {ss.sandbox_tsp.gstin.taxpayer_name && <Row label="Taxpayer"  value={ss.sandbox_tsp.gstin.taxpayer_name} />}
                {ss.sandbox_tsp.gstin.registration_date && <Row label="Reg Date" value={ss.sandbox_tsp.gstin.registration_date} />}
              </>
            ) : null}

            {ss.sandbox_tsp?.pan ? (
              <>
                <Row label="PAN"        value={ss.sandbox_tsp.pan.pan} />
                <Row label="PAN Status" value={
                  <span className={`font-medium text-xs ${ss.sandbox_tsp.pan.valid ? 'text-emerald-600' : 'text-red-600'}`}>
                    {ss.sandbox_tsp.pan.status ?? (ss.sandbox_tsp.pan.valid ? 'Valid ✓' : 'Invalid ✗')}
                  </span>
                } link="https://eportal.incometax.gov.in/iec/foservices/#/pre-login/verifyYourPAN"
                  linkLabel="IT Portal" />
                {ss.sandbox_tsp.pan.name && <Row label="PAN Holder" value={ss.sandbox_tsp.pan.name} />}
              </>
            ) : null}

            {ss.sandbox_tsp?.msmed ? (
              <>
                <Row label="MSMED"        value={ss.sandbox_tsp.msmed.msmed_number} />
                <Row label="MSMED Status" value={
                  <span className={`font-medium text-xs ${ss.sandbox_tsp.msmed.valid ? 'text-emerald-600' : 'text-red-600'}`}>
                    {ss.sandbox_tsp.msmed.status ?? (ss.sandbox_tsp.msmed.valid ? 'Active ✓' : 'Invalid ✗')}
                  </span>
                } link="https://udyamregistration.gov.in" linkLabel="Udyam Portal" />
                {ss.sandbox_tsp.msmed.enterprise_type && <Row label="Enterprise"  value={ss.sandbox_tsp.msmed.enterprise_type} />}
                {ss.sandbox_tsp.msmed.name            && <Row label="Reg Name"    value={ss.sandbox_tsp.msmed.name} />}
                {ss.sandbox_tsp.msmed.activity        && <Row label="Activity"    value={ss.sandbox_tsp.msmed.activity} />}
              </>
            ) : null}

            {!ss.sandbox_tsp?.gstin && !ss.sandbox_tsp?.pan && !ss.sandbox_tsp?.msmed && (
              <Row label="Status" value="No India verification data — add SANDBOX_API_KEY to enable" />
            )}
          </Section>

          {/* Sandbox Intel — extracted from GSTIN/PAN/MSMED */}
          {ss.sandbox_intel && (
            <Section title="Extracted Intelligence (from GSTIN / PAN / MSMED)" icon={<BadgeCheck className="w-4 h-4" />}>
              {ss.sandbox_intel.business_type && <Row label="Business Type" value={ss.sandbox_intel.business_type} />}
              {ss.sandbox_intel.industry      && <Row label="Industry"      value={ss.sandbox_intel.industry} />}
              {ss.sandbox_intel.location      && <Row label="Location"      value={ss.sandbox_intel.location} />}
              {ss.sandbox_intel.registered_address && (
                <Row label="Reg. Address" value={ss.sandbox_intel.registered_address}
                  link={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(ss.sandbox_intel.registered_address)}`}
                  linkLabel="Maps" />
              )}
              {(ss.sandbox_intel.additional_names?.length ?? 0) > 0 && (
                <Row label="Alternate Names" value={
                  <span className="flex flex-wrap gap-1">
                    {ss.sandbox_intel.additional_names.map((n: string, i: number) => (
                      <span key={i} className="bg-secondary text-secondary-foreground text-xs px-1.5 py-0.5 rounded border">
                        {n}
                      </span>
                    ))}
                  </span>
                } />
              )}
            </Section>
          )}

          {/* Enrichment — searches run for each alternate name */}
          {ss.sandbox_enrichment?.alternate_names_searched &&
            Object.entries(
              ss.sandbox_enrichment.alternate_names_searched as Record<string, any>
            ).map(([name, data]) => (
              <Section key={name} title={`Enrichment: "${name}"`} icon={<Globe className="w-4 h-4" />}>
                {(data.serper_results ?? []).map((r: any, i: number) => (
                  <ArticleRow key={`s${i}`} source="Serper"
                    title={r.title} meta={tryHost(r.link)} url={r.link} />
                ))}
                {(data.gdelt_results ?? []).map((r: any, i: number) => (
                  <ArticleRow key={`g${i}`} source="GDELT"
                    title={r.title} meta={r.domain} url={r.url} />
                ))}
                {(data.sanctions_results?.length ?? 0) > 0
                  ? data.sanctions_results.map((r: any, i: number) => (
                      <Row key={`c${i}`} label="Sanctions Hit" value={r.caption ?? r.id}
                        link={`https://www.opensanctions.org/search/?q=${encodeURIComponent(name)}`}
                        linkLabel="OpenSanctions" />
                    ))
                  : (
                    <Row label="Sanctions" value={
                      <span className="text-emerald-600 flex items-center gap-1 text-xs">
                        <CheckCircle2 className="w-3.5 h-3.5" /> No matches for this name
                      </span>
                    } />
                  )}
                {(data.serper_results?.length ?? 0) === 0 &&
                  (data.gdelt_results?.length  ?? 0) === 0 && (
                  <Row label="Web Results" value="No results found for this alternate name" />
                )}
              </Section>
            ))}

          {/* GSTIN address Places result */}
          {ss.sandbox_enrichment?.gstin_address_places?.results?.length > 0 && (
            <Section title="Google Places — GSTIN Registered Address" icon={<MapPin className="w-4 h-4" />}>
              {ss.sandbox_enrichment.gstin_address_places.results.map((p: any, i: number) => (
                <div key={i}>
                  <Row label="Name"    value={p.name} />
                  <Row label="Address" value={p.formatted_address} />
                  <Row label="Status"  value={
                    <span className={`font-medium text-xs ${
                      p.business_status === 'OPERATIONAL' ? 'text-emerald-600' : 'text-orange-600'
                    }`}>
                      {p.business_status ?? 'Unknown'}
                    </span>
                  }
                    link={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                      (p.name ?? '') + ' ' + (p.formatted_address ?? '')
                    )}`}
                    linkLabel="Maps" />
                  {p.rating && <Row label="Rating" value={`${p.rating} ★`} />}
                </div>
              ))}
            </Section>
          )}

        </div>
      )}
    </div>
  );
};

export default Dashboard;