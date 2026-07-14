import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UploadCloud, Send, XCircle, CheckCircle2, ChevronDown } from 'lucide-react';

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

const Field = ({
  label, value, onChange, placeholder, required,
}: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; required?: boolean;
}) => (
  <div className="space-y-1.5 flex flex-col justify-end">
    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
      {label}{required && <span className="text-destructive ml-1">*</span>}
    </label>
    <input
      required={required}
      placeholder={placeholder}
      value={value}
      onChange={e => onChange(e.target.value)}
      className="flex h-10 w-full rounded-lg border bg-background/50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all placeholder:text-muted-foreground/50 hover:bg-background"
    />
  </div>
);

const FormSection = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div>
    <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-2">{label}</p>
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">{children}</div>
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
      const res = await axios.post('http://localhost:8000/vendor/parse-excel', payload);
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
      const res = await axios.post('http://localhost:8000/vendor/intake', formPayload, {
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
    <div className="max-w-4xl mx-auto space-y-8 pb-12 animate-in slide-in-from-bottom-4 fade-in duration-500">
      <div className="text-center space-y-2 mb-8">
        <h2 className="text-3xl font-bold tracking-tight">New Vendor Intake</h2>
        <p className="text-base text-muted-foreground">Submit vendor data manually or upload the standard Excel template.</p>
      </div>

      {/* ── Excel upload card (file input left, vendor dropdown right) ──── */}
      <div className="bg-card border rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-2 text-primary mb-4">
          <UploadCloud className="w-5 h-5" />
          <span className="text-base font-semibold">Bulk Upload via Excel</span>
        </div>

        <div className="flex flex-col md:flex-row items-stretch gap-6">
          {/* Left: file input + status */}
          <div className="flex-1 min-w-0">
            <div className="relative border-2 border-dashed rounded-xl p-6 hover:bg-muted/30 transition-colors text-center group cursor-pointer">
              <input
                type="file"
                ref={fileInputRef}
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center justify-center gap-2">
                <UploadCloud className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
                <div className="text-sm font-medium text-foreground">Click or drag Excel file here</div>
                <div className="text-xs text-muted-foreground">Supports .xlsx and .xls</div>
              </div>
            </div>
            
            <div className="mt-3 flex items-center justify-between min-h-6">
              {loading && <p className="text-sm text-muted-foreground animate-pulse">Parsing file...</p>}
              {file && !loading && parsedVendors.length === 0 && !errorMsg && (
                <p className="text-sm text-muted-foreground flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> {file.name}
                </p>
              )}
              {file && parsedVendors.length > 0 && (
                <p className="text-sm font-medium text-emerald-600 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  {parsedVendors.length} vendor{parsedVendors.length !== 1 ? 's' : ''} found in {file.name}
                </p>
              )}
              {errorMsg && <p className="text-sm text-destructive font-medium">{errorMsg}</p>}
            </div>
          </div>

          {/* Right: vendor dropdown (only when vendors parsed) */}
          {parsedVendors.length > 0 && (
            <div ref={dropdownRef} className="relative shrink-0 w-full md:w-72">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 block">
                Select Vendor from Sheet
              </label>
              {/* Trigger button */}
              <button
                type="button"
                onClick={() => setDropdownOpen(o => !o)}
                className="flex items-center justify-between w-full h-12 px-4 rounded-xl border-2 bg-background text-sm font-medium hover:border-primary/50 transition-colors gap-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <span className="truncate text-foreground">
                  {selectedVendorIdx !== null
                    ? parsedVendors[selectedVendorIdx].legal_name || '—'
                    : 'Select vendor…'}
                </span>
                <ChevronDown className={`w-4 h-4 text-muted-foreground shrink-0 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown panel */}
              {dropdownOpen && (
                <div className="absolute top-full left-0 right-0 z-20 mt-2 bg-card border rounded-xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                  {/* Grid header */}
                  <div className="grid grid-cols-[4rem_1fr] bg-muted/50 border-b px-4 py-2.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">ID</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Vendor Name</span>
                  </div>
                  {/* Grid rows */}
                  <div className="max-h-60 overflow-y-auto">
                    {parsedVendors.map((v, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => { handleVendorSelect(i); setDropdownOpen(false); }}
                        className={`grid grid-cols-[4rem_1fr] w-full px-4 py-3 text-left text-sm border-b last:border-0 transition-colors ${
                          selectedVendorIdx === i
                            ? 'bg-primary/10 text-primary'
                            : 'hover:bg-muted/40 text-foreground'
                        }`}
                      >
                        <span className="font-mono text-muted-foreground truncate text-xs mt-0.5">
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

      <div className="flex items-center gap-4 py-2">
        <div className="flex-1 h-px bg-border"></div>
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">OR MANUAL ENTRY</span>
        <div className="flex-1 h-px bg-border"></div>
      </div>

      {/* ── Manual entry form ──────────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Core identity */}
        <div className="bg-card border rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b pb-3">
            <h3 className="text-base font-semibold text-foreground">Core Identity</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <Field label="Legal Name" value={formData.legal_name} onChange={set('legal_name')} required />
            <Field label="Website Domain" value={formData.website_domain} onChange={set('website_domain')} placeholder="example.com" />
            <Field label="Registration / BP No." value={formData.registration_number} onChange={set('registration_number')} />
            <Field label="Jurisdiction (ISO)" value={formData.jurisdiction_country} onChange={set('jurisdiction_country')} placeholder="US, IN, GB" />
            <Field label="Registered Address" value={formData.registered_address} onChange={set('registered_address')} />
            <Field label="City" value={formData.city} onChange={set('city')} />
          </div>
        </div>

        {/* India-specific */}
        <div className="bg-card border rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b pb-3">
            <h3 className="text-base font-semibold text-foreground">India Identifiers</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <Field label="GSTIN" value={formData.tax_identifier} onChange={set('tax_identifier')} />
            <Field label="PAN Number" value={formData.pan_number} onChange={set('pan_number')} />
            <Field label="MSMED Cert. No." value={formData.msmed_certificate_number} onChange={set('msmed_certificate_number')} />
          </div>
        </div>

        {/* People */}
        <div className="bg-card border rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b pb-3">
            <h3 className="text-base font-semibold text-foreground">Key Personnel</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <Field label="Director Names (;-sep)" value={formData.director_names} onChange={set('director_names')} placeholder="Alice; Bob" />
            <Field label="Director DIN (;-sep)" value={formData.director_din} onChange={set('director_din')} placeholder="00000001; 00000002" />
            <Field label="Founder / CEO" value={formData.founder_ceo_name} onChange={set('founder_ceo_name')} />
          </div>
        </div>

        {/* Contact & Social */}
        <div className="bg-card border rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b pb-3">
            <h3 className="text-base font-semibold text-foreground">Contact & Social</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <Field label="Corporate Email Domain" value={formData.corporate_email_domain} onChange={set('corporate_email_domain')} placeholder="corp.com" />
            <Field label="Mobile Number" value={formData.mobile_number} onChange={set('mobile_number')} />
            <Field label="LinkedIn Handle" value={formData.linkedin_handle} onChange={set('linkedin_handle')} />
            <Field label="Twitter Handle" value={formData.twitter_handle} onChange={set('twitter_handle')} />
            <Field label="Facebook Handle" value={formData.facebook_handle} onChange={set('facebook_handle')} />
          </div>
        </div>

        {/* Error */}
        {errorMsg && (
          <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-xl border border-destructive/20 text-sm font-medium flex items-center gap-2">
            <XCircle className="w-5 h-5 shrink-0" />
            {errorMsg}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 pt-4 sticky bottom-6 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4 -mx-4 rounded-2xl border shadow-lg z-10">
          <button
            type="button"
            onClick={handleClear}
            disabled={loading}
            className="inline-flex items-center justify-center rounded-xl text-sm font-semibold border-2 bg-background hover:bg-muted h-12 px-8 disabled:opacity-50 transition-colors"
          >
            <XCircle className="w-4 h-4 mr-2" /> Clear Form
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 inline-flex items-center justify-center rounded-xl text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-8 disabled:opacity-50 transition-colors shadow-sm"
          >
            {loading ? 'Processing…' : <><Send className="w-4 h-4 mr-2" /> Save Vendor & Continue</>}
          </button>
        </div>
      </form>
    </div>
  );
};

export default IntakeForm;
