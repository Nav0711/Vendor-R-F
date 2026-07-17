import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  UploadCloud, Send, XCircle, CheckCircle2, ChevronDown,
  Building2, Tag, IdCard, Users, AtSign,
} from 'lucide-react';
import { api } from '../lib/api';

const EMPTY_FORM = {
  legal_name: '',
  website_domain: '',
  registration_number: '',
  jurisdiction_country: '',
  category: '',
  tax_identifier: '',
  registered_address: '',
  director_names: '',
  director_din: '',
  founder_ceo_name: '',
  linkedin_handle: '',
  twitter_handle: '',
  facebook_handle: '',
  corporate_email_domain: '',
  pan_number: '',
  city: '',
  mobile_number: '',
  msmed_certificate_number: '',
};

// Free text — the backend keyword-matches this into a compliance bucket
// (food / packaging / chemical-gas / capex-cooling / services). These suggestions
// just steer the matcher toward a confident bucket.
const CATEGORY_SUGGESTIONS = [
  'Food & Beverage Ingredients', 'Food Packaging', 'Industrial Gas', 'Chemicals',
  'Cooling / Refrigeration Equipment', 'Capital Equipment', 'Logistics',
  'IT Services', 'Consulting', 'Pharmaceuticals', 'Textiles', 'Construction',
];

const Field = ({
  label, value, onChange, placeholder, required, listId, className,
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; required?: boolean; listId?: string; className?: string;
}) => (
  <div className={`space-y-1 ${className ?? ''}`}>
    <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
      {label}{required && <span className="text-destructive ml-0.5">*</span>}
    </label>
    <input
      required={required}
      placeholder={placeholder}
      value={value}
      list={listId}
      onChange={e => onChange(e.target.value)}
      className="flex h-9 w-full rounded-md border bg-background px-2.5 py-1.5 text-sm transition-shadow
        focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
    />
  </div>
);

const Section = ({
  icon, label, children, cols = 3,
}: {
  icon: React.ReactNode; label: string; children: React.ReactNode; cols?: 2 | 3;
}) => (
  <div className="space-y-2.5">
    <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
      <span className="text-primary/70">{icon}</span>{label}
    </div>
    <div className={`grid grid-cols-2 ${cols === 3 ? 'md:grid-cols-3' : ''} gap-3`}>{children}</div>
  </div>
);

const IntakeForm = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [file, setFile] = useState<File | null>(null);
  const [parsedVendors, setParsedVendors] = useState<any[]>([]);
  const [selectedVendorIdx, setSelectedVendorIdx] = useState<number | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const set = (key: keyof typeof EMPTY_FORM) => (v: string) =>
    setFormData(prev => ({ ...prev, [key]: v }));

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setLoading(true);
    setErrorMsg(null);
    setParsedVendors([]);
    setSelectedVendorIdx(null);
    try {
      const payload = new FormData();
      payload.append('file', selectedFile);
      const res = await axios.post(api('/vendor/parse-excel'), payload);
      setParsedVendors(res.data.vendors || []);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Error parsing Excel file');
    } finally {
      setLoading(false);
    }
  };

  const handleVendorSelect = (idx: number) => {
    setSelectedVendorIdx(idx);
    const v = parsedVendors[idx];
    setFormData({
      ...EMPTY_FORM,
      ...v,
      director_names: Array.isArray(v.director_names) ? v.director_names.join('; ') : (v.director_names || ''),
      director_din:   Array.isArray(v.director_din)   ? v.director_din.join('; ')   : (v.director_din   || ''),
    });
  };

  const handleClear = () => {
    setFormData(EMPTY_FORM);
    setFile(null);
    setParsedVendors([]);
    setSelectedVendorIdx(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const formPayload = new FormData();
      const payload = {
        ...formData,
        director_names: formData.director_names
          ? formData.director_names.split(';').map((s: string) => s.trim()).filter(Boolean)
          : [],
        director_din: formData.director_din
          ? formData.director_din.split(';').map((s: string) => s.trim()).filter(Boolean)
          : [],
        social_handles: {
          linkedin: formData.linkedin_handle,
          twitter:  formData.twitter_handle,
          facebook: formData.facebook_handle,
        },
        source_method: file ? 'excel' : 'manual',
      };
      formPayload.append('manual_fields', JSON.stringify(payload));
      const res = await axios.post(api('/vendor/intake'), formPayload, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      navigate(`/scan/${res.data.input_id}`);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Error submitting intake');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 animate-in fade-in duration-300">
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">New Vendor Intake</h2>
        <p className="text-sm text-muted-foreground">Submit vendor data manually or upload the standard Excel template.</p>
      </div>

      {/* ── Excel upload card (file input left, vendor dropdown right) ──── */}
      <div className="bg-card border rounded-xl px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2 text-primary mb-2.5">
          <UploadCloud className="w-4 h-4" />
          <span className="text-sm font-semibold">Excel Upload</span>
        </div>

        <div className="flex items-center gap-4">
          {/* Left: file input + status */}
          <div className="flex-1 min-w-0">
            <input
              type="file"
              ref={fileInputRef}
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              className="block w-full text-xs text-slate-500
                file:mr-3 file:py-1.5 file:px-3 file:rounded-full file:border-0
                file:text-xs file:font-semibold file:bg-primary/10 file:text-primary
                hover:file:bg-primary/20 cursor-pointer"
            />
            {loading && <p className="text-xs text-muted-foreground mt-1">Parsing…</p>}
            {file && !loading && parsedVendors.length === 0 && !errorMsg && (
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-500" /> {file.name}
              </p>
            )}
            {file && parsedVendors.length > 0 && (
              <p className="text-xs text-emerald-600 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                {parsedVendors.length} vendor{parsedVendors.length !== 1 ? 's' : ''} found
              </p>
            )}
            {errorMsg && <p className="text-xs text-red-600 mt-1">{errorMsg}</p>}
          </div>

          {/* Right: vendor dropdown (only when vendors parsed) */}
          {parsedVendors.length > 0 && (
            <div ref={dropdownRef} className="relative shrink-0 w-60">
              <button
                type="button"
                onClick={() => setDropdownOpen(o => !o)}
                className="flex items-center justify-between w-full h-8 px-3 rounded-md border bg-background text-xs font-medium hover:bg-muted/40 transition-colors gap-2"
              >
                <span className="truncate text-foreground">
                  {selectedVendorIdx !== null
                    ? parsedVendors[selectedVendorIdx].legal_name || '—'
                    : 'Select vendor…'}
                </span>
                <ChevronDown className={`w-3.5 h-3.5 text-muted-foreground shrink-0 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {dropdownOpen && (
                <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-card border rounded-lg shadow-lg overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150">
                  <div className="grid grid-cols-[3.5rem_1fr] bg-muted/50 border-b px-3 py-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">ID</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Vendor Name</span>
                  </div>
                  <div className="max-h-40 overflow-y-auto">
                    {parsedVendors.map((v, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => { handleVendorSelect(i); setDropdownOpen(false); }}
                        className={`grid grid-cols-[3.5rem_1fr] w-full px-3 py-2 text-left text-xs border-b last:border-0 transition-colors ${
                          selectedVendorIdx === i
                            ? 'bg-primary/10 text-primary'
                            : 'hover:bg-muted/40 text-foreground'
                        }`}
                      >
                        <span className="font-mono text-muted-foreground truncate">
                          {v.registration_number || String(i + 1).padStart(3, '0')}
                        </span>
                        <span className="font-medium truncate">{v.legal_name || '—'}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* datalist shared by the Category field */}
      <datalist id="category-suggestions">
        {CATEGORY_SUGGESTIONS.map(c => <option key={c} value={c} />)}
      </datalist>

      {/* ── Manual entry form ──────────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="bg-card border rounded-xl p-5 shadow-sm space-y-6">

        <Section icon={<Building2 className="w-3.5 h-3.5" />} label="Business Identity">
          <Field label="Legal Name" value={formData.legal_name} onChange={set('legal_name')} required />
          <Field label="Website Domain" value={formData.website_domain} onChange={set('website_domain')} placeholder="example.com" />
          <Field label="Registration / BP No." value={formData.registration_number} onChange={set('registration_number')} />
          <Field label="Jurisdiction (ISO)" value={formData.jurisdiction_country} onChange={set('jurisdiction_country')} placeholder="US, IN, GB" />
          <Field label="Registered Address" value={formData.registered_address} onChange={set('registered_address')} />
          <Field label="City" value={formData.city} onChange={set('city')} />
        </Section>

        {/* Category — pulled out and highlighted; it drives the compliance filtering */}
        <div className="rounded-lg border border-primary/20 bg-primary/[0.03] p-3 space-y-1">
          <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-primary/80">
            <Tag className="w-3.5 h-3.5" /> Business Category / Sector
          </div>
          <input
            placeholder="e.g. Food Packaging, Industrial Gas, IT Services…"
            value={formData.category}
            list="category-suggestions"
            onChange={e => set('category')(e.target.value)}
            className="flex h-9 w-full rounded-md border bg-background px-2.5 py-1.5 text-sm transition-shadow
              focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
          />
          <p className="text-[11px] text-muted-foreground">
            Focuses adverse-media, web &amp; reviews filtering onto this vendor's real risk profile.
            Leave blank to screen against all results.
          </p>
        </div>

        <Section icon={<IdCard className="w-3.5 h-3.5" />} label="India Identifiers">
          <Field label="GSTIN" value={formData.tax_identifier} onChange={set('tax_identifier')} />
          <Field label="PAN Number" value={formData.pan_number} onChange={set('pan_number')} />
          <Field label="MSMED Cert. No." value={formData.msmed_certificate_number} onChange={set('msmed_certificate_number')} />
        </Section>

        <Section icon={<Users className="w-3.5 h-3.5" />} label="People">
          <Field label="Director Names (;-sep)" value={formData.director_names} onChange={set('director_names')} placeholder="Alice; Bob" />
          <Field label="Director DIN (;-sep)" value={formData.director_din} onChange={set('director_din')} placeholder="00000001; 00000002" />
          <Field label="Founder / CEO" value={formData.founder_ceo_name} onChange={set('founder_ceo_name')} />
        </Section>

        <Section icon={<AtSign className="w-3.5 h-3.5" />} label="Contact &amp; Social">
          <Field label="Corporate Email Domain" value={formData.corporate_email_domain} onChange={set('corporate_email_domain')} placeholder="corp.com" />
          <Field label="Mobile Number" value={formData.mobile_number} onChange={set('mobile_number')} />
          <Field label="LinkedIn Handle" value={formData.linkedin_handle} onChange={set('linkedin_handle')} />
          <Field label="Twitter Handle" value={formData.twitter_handle} onChange={set('twitter_handle')} />
          <Field label="Facebook Handle" value={formData.facebook_handle} onChange={set('facebook_handle')} />
        </Section>

        {errorMsg && (
          <div className="bg-red-50 text-red-700 px-3 py-2 rounded-md border border-red-200 text-xs font-medium">
            {errorMsg}
          </div>
        )}

        {/* Actions — sticky so Submit is always reachable on long forms */}
        <div className="flex gap-3 pt-1 sticky bottom-0 -mx-5 -mb-5 px-5 py-3 bg-card/95 backdrop-blur border-t rounded-b-xl">
          <button
            type="button"
            onClick={handleClear}
            disabled={loading}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-4 disabled:opacity-50 transition-colors"
          >
            <XCircle className="w-3.5 h-3.5 mr-1.5" /> Clear
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Processing…' : <><Send className="w-3.5 h-3.5 mr-1.5" /> Submit &amp; Continue</>}
          </button>
        </div>
      </form>
    </div>
  );
};

export default IntakeForm;
