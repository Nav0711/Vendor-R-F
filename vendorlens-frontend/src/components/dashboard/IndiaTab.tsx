import { ShieldCheck, BadgeCheck, Globe, MapPin, CheckCircle2 } from 'lucide-react';
import Section from './Section';
import Row from './Row';
import ArticleRow from './ArticleRow';
import { tryHost } from './utils';

const IndiaTab = ({ ss }: { ss: any }) => (
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
);

export default IndiaTab;
