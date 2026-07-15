import { Landmark, ShieldAlert, Globe, MapPin, FileText } from 'lucide-react';
import Row, { OkBadge, UnavailableBadge } from './Row';
import Section from './Section';
import SectionInsight from './SectionInsight';

const OverviewTab = ({ ss, report }: { ss: any; report: any }) => {
  const sa = report.section_analysis ?? {};
  const aiUnavailable = !!(report.section_analysis?._ai_unavailable);

  // The backend marks every source ok | unavailable | not_applicable. An empty result
  // from a source that FAILED must not be rendered as a clean finding.
  const unavailable = (key: string) => ss.source_status?.[key] === 'unavailable';
  // {} is truthy in JS, so an errored source needs a real emptiness check.
  const hasData = (v: any) => !!v && Object.keys(v).length > 0;

  const Insight = ({ sectionKey }: { sectionKey: string }) =>
    aiUnavailable
      ? <SectionInsight unavailable />
      : sa[sectionKey] ? <SectionInsight {...sa[sectionKey]} /> : null;

  return (
    <div className="space-y-4 animate-in fade-in duration-200">

      {/* Corporate Registry */}
      <Section title="Corporate Registry" icon={<Landmark className="w-4 h-4" />}>
        <Insight sectionKey="corporate_registry" />
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
        <Insight sectionKey="sanctions_watchlists" />
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
        ) : unavailable('opensanctions') ? (
          <Row label="Status" value={<UnavailableBadge msg="Sanctions screening did not run" />} />
        ) : (
          <Row label="Status" value={<OkBadge msg="No watchlist matches" />} />
        )}
      </Section>

      {/* Domain & SSL */}
      <Section title="Domain & SSL" icon={<Globe className="w-4 h-4" />}>
        <Insight sectionKey="domain_ssl" />
        {hasData(ss.whois) && (
          <>
            <Row label="Domain"    value={Array.isArray(ss.whois.domain_name) ? ss.whois.domain_name[0] : ss.whois.domain_name}
              link={`https://whois.domaintools.com/${report.subject.domain}`} linkLabel="WHOIS" />
            <Row label="Registrar" value={ss.whois.registrar} />
            <Row label="Created"   value={ss.whois.creation_date   ? new Date(ss.whois.creation_date).toLocaleDateString()   : '—'} />
            <Row label="Expires"   value={ss.whois.expiration_date ? new Date(ss.whois.expiration_date).toLocaleDateString() : '—'} />
          </>
        )}
        {unavailable('whois') && (
          <Row label="Domain" value={<UnavailableBadge msg="WHOIS lookup unavailable" />} />
        )}
        {hasData(ss.ssl) && (
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
        {unavailable('ssl') && (
          <Row label="SSL" value={<UnavailableBadge msg="SSL check unavailable — not a missing certificate" />} />
        )}
        {ss.microlink?.title && (
          <Row label="Site Title" value={ss.microlink.title}
            link={report.subject.domain?.startsWith('http')
              ? report.subject.domain
              : `https://${report.subject.domain}`}
            linkLabel="Visit" />
        )}
        {ss.source_status?.whois === 'not_applicable' && ss.source_status?.ssl === 'not_applicable' && (
          <Row label="Status" value="No domain provided" />
        )}
      </Section>

      {/* Physical Address */}
      <Section title="Physical Address" icon={<MapPin className="w-4 h-4" />}>
        <Insight sectionKey="physical_address" />
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

      {/* Wikipedia */}
      {ss.wikipedia?.found && (
        <Section title="Wikipedia" icon={<FileText className="w-4 h-4" />}>
          <Insight sectionKey="wikipedia" />
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
  );
};

export default OverviewTab;
