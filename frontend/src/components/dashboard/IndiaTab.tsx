import { ShieldCheck, BadgeCheck, Globe, MapPin, Mail, Scale, AlertTriangle, Shield } from 'lucide-react';
import Section from './Section';
import Row, { BoolCell, OkBadge, ValidCell } from './Row';
import ArticleRow from './ArticleRow';
import { tryHost } from './utils';

const RiskBadge = ({ risk }: { risk?: string }) => {
  const r = (risk || 'low').toLowerCase();
  const cls = r === 'critical' ? 'text-destructive' : r === 'high' ? 'text-orange-600 dark:text-orange-400' : r === 'medium' ? 'text-yellow-600 dark:text-yellow-400' : 'text-emerald-600 dark:text-emerald-400';
  return <span className={`font-medium text-xs ${cls}`}>{risk ?? 'Low'}</span>;
};

const IndiaTab = ({ ss }: { ss: any }) => {
  const tsp        = ss.authbridge_tsp        ?? ss.sandbox_tsp        ?? {};
  const intel      = ss.authbridge_intel      ?? ss.sandbox_intel      ?? null;
  const enrichment = ss.authbridge_enrichment ?? ss.sandbox_enrichment ?? null;

  const emailVerif  = tsp.email_verification  ?? ss.authbridge_email_verification;
  const courtCheck  = tsp.court_check         ?? ss.authbridge_court_check         ?? {};
  const defaulting  = tsp.defaulting_director ?? ss.authbridge_defaulting_director ?? {};
  const globalSanc  = tsp.global_sanctions    ?? ss.authbridge_global_sanctions    ?? {};

  const hasIdentity   = !!(tsp.gstin || tsp.pan || tsp.msmed);
  const hasCourt      = Object.keys(courtCheck).length > 0;
  const hasDefault    = Object.keys(defaulting).length > 0;
  const hasGlobalSanc = Object.keys(globalSanc).length > 0;
  const hasEmail      = !!emailVerif;

  return (
    <div className="space-y-4 animate-in fade-in duration-200">

      {hasEmail && (
        <Section title="Email Verification" icon={<Mail className="w-4 h-4" />}>
          <Row label="Domain"       value={emailVerif.domain ?? '—'} />
          <Row label="Risk Level"   value={<RiskBadge risk={emailVerif.risk} />} />
          <Row label="Deliverable"  value={
            <span className={`text-xs font-medium ${emailVerif.deliverable ? 'text-emerald-600 dark:text-emerald-400' : 'text-destructive'}`}>
              {emailVerif.deliverable ? 'Yes ✓' : 'No ✗'}
            </span>
          } />
          <Row label="Disposable"   value={
            <span className={`text-xs font-medium ${emailVerif.disposable ? 'text-destructive' : 'text-emerald-600 dark:text-emerald-400'}`}>
              {emailVerif.disposable ? 'Yes — personal/disposable domain ✗' : 'No ✓'}
            </span>
          } />
          <Row label="MX Records"   value={
            <span className={`text-xs font-medium ${emailVerif.mx_records ? 'text-emerald-600 dark:text-emerald-400' : 'text-orange-600 dark:text-orange-400'}`}>
              {emailVerif.mx_records ? 'Present ✓' : 'Missing ✗'}
            </span>
          } />
        </Section>
      )}

      {hasGlobalSanc && (
        <Section title="Global Sanctions Check (AuthBridge)" icon={<Shield className="w-4 h-4" />}>
          {Object.entries(globalSanc as Record<string, any>).map(([name, data]) => (
            <div key={name} className="mb-2">
              <Row label={name} value={
                data.is_sanctioned
                  ? <span className="text-destructive text-xs font-semibold">⚠ SANCTIONED — {data.matches?.length} match(es)</span>
                  : <span className="text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Clear</span>
              } />
              {(data.matches ?? []).map((m: any, i: number) => (
                <Row key={i} label="Match" value={m.name ?? m.caption ?? JSON.stringify(m)} />
              ))}
            </div>
          ))}
        </Section>
      )}

      {hasCourt && (
        <Section title="Court Check" icon={<Scale className="w-4 h-4" />}>
          {Object.entries(courtCheck as Record<string, any>).map(([name, data]) => (
            <div key={name} className="mb-2">
              <Row label={name} value={
                (data.cases_found ?? 0) > 0
                  ? <span className="text-orange-600 dark:text-orange-400 text-xs font-semibold">⚠ {data.cases_found} case(s) found</span>
                  : <span className="text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> No cases</span>
              } />
              {(data.cases ?? []).slice(0, 3).map((c: any, i: number) => (
                <Row key={i} label={`Case ${i + 1}`} value={c.title ?? c.case_number ?? c.description ?? JSON.stringify(c)} />
              ))}
            </div>
          ))}
        </Section>
      )}

      {hasDefault && (
        <Section title="Defaulting Director Check (MCA)" icon={<AlertTriangle className="w-4 h-4" />}>
          {Object.entries(defaulting as Record<string, any>).map(([name, data]) => (
            <div key={name} className="mb-2">
              <Row label={name} value={
                data.is_defaulter
                  ? <span className="text-destructive text-xs font-semibold">⚠ DEFAULTER — {data.disqualification_reason ?? 'see MCA records'}</span>
                  : <span className="text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Not a defaulter</span>
              } />
              {data.din && <Row label="DIN" value={data.din} />}
            </div>
          ))}
        </Section>
      )}

      {hasIdentity && (
        <Section title="India Identity Verification (AuthBridge)" icon={<ShieldCheck className="w-4 h-4" />}>
          {tsp.gstin && (
            <>
              <Row label="GSTIN"        value={tsp.gstin.gstin} />
              <Row label="GSTIN Status" value={
                <span className={`font-medium text-xs ${tsp.gstin.valid ? 'text-emerald-600 dark:text-emerald-400' : 'text-destructive'}`}>
                  {tsp.gstin.status ?? (tsp.gstin.valid ? 'Active ✓' : 'Invalid ✗')}
                </span>
              } link="https://services.gst.gov.in/services/searchtp" linkLabel="GST Portal" />
              {tsp.gstin.taxpayer_name    && <Row label="Taxpayer"  value={tsp.gstin.taxpayer_name} />}
              {tsp.gstin.registration_date && <Row label="Reg Date" value={tsp.gstin.registration_date} />}
            </>
          )}
          {tsp.pan && (
            <>
              <Row label="PAN"        value={tsp.pan.pan} />
              <Row label="PAN Status" value={
                <span className={`font-medium text-xs ${tsp.pan.valid ? 'text-emerald-600 dark:text-emerald-400' : 'text-destructive'}`}>
                  {tsp.pan.status ?? (tsp.pan.valid ? 'Valid ✓' : 'Invalid ✗')}
                </span>
              } link="https://eportal.incometax.gov.in/iec/foservices/#/pre-login/verifyYourPAN" linkLabel="IT Portal" />
              {tsp.pan.name && <Row label="PAN Holder" value={tsp.pan.name} />}
            </>
          )}
          {tsp.msmed && (
            <>
              <Row label="MSMED"        value={tsp.msmed.msmed_number} />
              <Row label="MSMED Status" value={
                <span className={`font-medium text-xs ${tsp.msmed.valid ? 'text-emerald-600 dark:text-emerald-400' : 'text-destructive'}`}>
                  {tsp.msmed.status ?? (tsp.msmed.valid ? 'Active ✓' : 'Invalid ✗')}
                </span>
              } link="https://udyamregistration.gov.in" linkLabel="Udyam Portal" />
              {tsp.msmed.enterprise_type && <Row label="Enterprise" value={tsp.msmed.enterprise_type} />}
              {tsp.msmed.name            && <Row label="Reg Name"   value={tsp.msmed.name} />}
              {tsp.msmed.activity        && <Row label="Activity"   value={tsp.msmed.activity} />}
            </>
          )}
          {!tsp.gstin && !tsp.pan && !tsp.msmed && (
            <Row label="Status" value="No India verification data — add AUTHBRIDGE_API_KEY to enable" />
          )}
        </Section>
      )}

      {intel && (
        <Section title="Extracted Intelligence (from GSTIN / PAN / MSMED)" icon={<BadgeCheck className="w-4 h-4" />}>
          {intel.business_type && <Row label="Business Type" value={intel.business_type} />}
          {intel.industry      && <Row label="Industry"      value={intel.industry} />}
          {intel.location      && <Row label="Location"      value={intel.location} />}
          {intel.registered_address && (
            <Row label="Reg. Address" value={intel.registered_address}
              link={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(intel.registered_address)}`}
              linkLabel="Maps" />
          )}
          {(intel.additional_names?.length ?? 0) > 0 && (
            <Row label="Alternate Names" value={
              <span className="flex flex-wrap gap-1">
                {intel.additional_names.map((n: string, i: number) => (
                  <span key={i} className="bg-secondary text-secondary-foreground text-xs px-1.5 py-0.5 rounded border">{n}</span>
                ))}
              </span>
            } />
          )}
        </Section>
      )}

      {enrichment?.alternate_names_searched &&
        Object.entries(enrichment.alternate_names_searched as Record<string, any>).map(([name, data]) => (
          <Section key={name} title={`Enrichment: "${name}"`} icon={<Globe className="w-4 h-4" />}>
            {(data.serper_results ?? []).map((r: any, i: number) => (
              <ArticleRow key={`s${i}`} source="Serper" title={r.title} meta={tryHost(r.link)} url={r.link} />
            ))}
            {(data.gdelt_results ?? []).map((r: any, i: number) => (
              <ArticleRow key={`g${i}`} source="GDELT" title={r.title} meta={r.domain} url={r.url} />
            ))}
            {(data.sanctions_results?.length ?? 0) > 0
              ? data.sanctions_results.map((r: any, i: number) => (
                  <Row key={`c${i}`} label="Sanctions Hit" value={r.caption ?? r.id}
                    link={`https://www.opensanctions.org/search/?q=${encodeURIComponent(name)}`}
                    linkLabel="OpenSanctions" />
                ))
              : (
                <Row label="Sanctions" value={
                  <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1 text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5" /> No matches for this name
                  </span>
                } />
              )}
            {(data.serper_results?.length ?? 0) === 0 && (data.gdelt_results?.length ?? 0) === 0 && (
              <Row label="Web Results" value="No results found for this alternate name" />
            )}
          </Section>
        ))}

      {enrichment?.gstin_address_places?.results?.length > 0 && (
        <Section title="Google Places — GSTIN Registered Address" icon={<MapPin className="w-4 h-4" />}>
          {enrichment.gstin_address_places.results.map((p: any, i: number) => (
            <div key={i}>
              <Row label="Name"    value={p.name} />
              <Row label="Address" value={p.formatted_address} />
              <Row label="Status"  value={
                <span className={`font-medium text-xs ${p.business_status === 'OPERATIONAL' ? 'text-emerald-600 dark:text-emerald-400' : 'text-orange-600 dark:text-orange-400'}`}>
                  {p.business_status ?? 'Unknown'}
                </span>
              }
                link={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent((p.name ?? '') + ' ' + (p.formatted_address ?? ''))}`}
                linkLabel="Maps" />
              {p.rating && <Row label="Rating" value={`${p.rating} ★`} />}
            </div>
          ))}
        </Section>
      )}

      {!hasEmail && !hasCourt && !hasDefault && !hasGlobalSanc && !hasIdentity && !intel && !enrichment && (
        <div className="text-center text-muted-foreground text-sm py-8">
          No AuthBridge data available — set AUTHBRIDGE_API_KEY in backend/.env to enable verification checks.
        </div>
      )}

    </div>
  );
};

export default IndiaTab;
