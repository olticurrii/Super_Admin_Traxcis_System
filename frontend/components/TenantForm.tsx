'use client';

import { useState } from 'react';
import { createTenant } from '@/lib/api';
import { TenantResponse } from '@/lib/types';
import { Plus, Loader2, CheckCircle2, XCircle } from 'lucide-react';

interface TenantFormProps {
  onSuccess: (tenant: TenantResponse) => void;
}

export default function TenantForm({ onSuccess }: TenantFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    company_name: '',
    admin_email: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const tenant = await createTenant(formData);
      setSuccess(true);
      onSuccess(tenant);
      setFormData({ name: '', company_name: '', admin_email: '' });
      
      // Reset success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create tenant');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-xl p-8 border border-white/50">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
        <div className="bg-gradient-to-br from-primary-500 to-primary-600 p-2 rounded-lg shadow-lg shadow-primary-500/30">
          <Plus className="w-5 h-5 text-white" />
        </div>
        Create New Tenant
      </h2>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2.5">
            Tenant Name
          </label>
          <input
            type="text"
            id="name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all shadow-sm hover:border-gray-300"
            placeholder="e.g., Acme Corporation"
          />
        </div>

        <div>
          <label htmlFor="company_name" className="block text-sm font-semibold text-gray-700 mb-2.5">
            Company Name <span className="text-primary-600">(for login)</span>
          </label>
          <input
            type="text"
            id="company_name"
            required
            value={formData.company_name}
            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all shadow-sm hover:border-gray-300"
            placeholder="e.g., Traxcis"
          />
          <p className="mt-1.5 text-xs text-gray-500">Users will enter this name when logging in to the HRMS</p>
        </div>

        <div>
          <label htmlFor="admin_email" className="block text-sm font-semibold text-gray-700 mb-2.5">
            Admin Email
          </label>
          <input
            type="email"
            id="admin_email"
            required
            value={formData.admin_email}
            onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all shadow-sm hover:border-gray-300"
            placeholder="admin@example.com"
          />
        </div>

        {error && (
          <div className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-2.5 shadow-sm animate-in fade-in">
            <XCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border-2 border-green-200 text-green-700 px-4 py-3 rounded-xl flex items-center gap-2.5 shadow-sm animate-in fade-in">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">Tenant created successfully!</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-primary-600 to-primary-700 text-white py-3.5 px-6 rounded-xl font-semibold hover:from-primary-700 hover:to-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 flex items-center justify-center gap-2.5 transform hover:scale-[1.02] active:scale-[0.98]"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Creating Tenant...</span>
            </>
          ) : (
            <>
              <Plus className="w-5 h-5" />
              <span>Create Tenant</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

