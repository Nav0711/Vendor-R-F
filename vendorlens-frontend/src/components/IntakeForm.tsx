import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UploadCloud, FileText, Send } from 'lucide-react';

const IntakeForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    legal_name: '',
    website_domain: '',
    registration_number: '',
    jurisdiction_country: '',
    tax_identifier: '',
    registered_address: '',
    director_names: '',
    director_din: '',
    founder_ceo_name: '',
    linkedin_handle: '',
    twitter_handle: '',
    facebook_handle: '',
    corporate_email_domain: ''
  });
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formPayload = new FormData();
      if (file) {
        formPayload.append('excel_file', file);
      } else {
        const payload = {
          ...formData,
          director_names: formData.director_names.split(';').map(s => s.trim()).filter(Boolean),
          director_din: formData.director_din.split(';').map(s => s.trim()).filter(Boolean),
          social_handles: {
            linkedin: formData.linkedin_handle,
            twitter: formData.twitter_handle,
            facebook: formData.facebook_handle
          },
          source_method: 'manual'
        };
        formPayload.append('manual_fields', JSON.stringify(payload));
      }

      const res = await axios.post('http://localhost:8000/vendor/intake', formPayload, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      navigate(`/scan/${res.data.input_id}`);
    } catch (err) {
      console.error(err);
      alert('Error submitting intake');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-semibold tracking-tight">New Vendor Intake</h2>
        <p className="text-muted-foreground">Submit vendor data manually or upload the standard Excel template.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="bg-card border rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-3 text-primary">
            <UploadCloud className="w-6 h-6" />
            <h3 className="text-xl font-medium">Excel Upload</h3>
          </div>
          <p className="text-sm text-muted-foreground">Upload VendorLens_Intake_Template.xlsx.</p>
          <input 
            type="file" 
            accept=".xlsx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
          />
        </div>
        
        <div className="bg-card border rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-3 text-primary">
            <FileText className="w-6 h-6" />
            <h3 className="text-xl font-medium">Manual Intake</h3>
          </div>
          <p className="text-sm text-muted-foreground">Fields will be captured once and reused for all future scans.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-card border rounded-xl p-6 shadow-sm space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Legal Name <span className="text-destructive">*</span></label>
            <input required disabled={!!file} className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50" value={formData.legal_name} onChange={e => setFormData({...formData, legal_name: e.target.value})} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Website Domain <span className="text-destructive">*</span></label>
            <input required disabled={!!file} className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50" placeholder="example.com" value={formData.website_domain} onChange={e => setFormData({...formData, website_domain: e.target.value})} />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium">Registration Number</label>
            <input disabled={!!file} className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50" value={formData.registration_number} onChange={e => setFormData({...formData, registration_number: e.target.value})} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Jurisdiction Country (ISO)</label>
            <input disabled={!!file} className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50" placeholder="US, IN, GB" value={formData.jurisdiction_country} onChange={e => setFormData({...formData, jurisdiction_country: e.target.value})} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Tax Identifier</label>
            <input disabled={!!file} className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50" value={formData.tax_identifier} onChange={e => setFormData({...formData, tax_identifier: e.target.value})} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Registered Address</label>
            <input disabled={!!file} className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50" value={formData.registered_address} onChange={e => setFormData({...formData, registered_address: e.target.value})} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Director Names (semicolon separated)</label>
            <input disabled={!!file} className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50" value={formData.director_names} onChange={e => setFormData({...formData, director_names: e.target.value})} />
          </div>
        </div>

        <button disabled={loading} className="w-full inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 disabled:opacity-50">
          {loading ? 'Saving...' : <><Send className="w-4 h-4 mr-2" /> Save Vendor Intake</>}
        </button>
      </form>
    </div>
  );
};
export default IntakeForm;
