'use client';

import { TenantResponse } from '@/lib/types';
import { Database, Mail, Key, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { format } from 'date-fns';

interface TenantCardProps {
  tenant: TenantResponse;
}

export default function TenantCard({ tenant }: TenantCardProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(true);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <div className="bg-gradient-to-br from-primary-50 via-blue-50 to-indigo-50 border-2 border-primary-200/50 rounded-xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-primary-600 to-primary-700 p-3 rounded-xl shadow-lg shadow-primary-500/30">
            <Database className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-800">Tenant Created</h3>
            <p className="text-sm text-gray-600">Save these credentials securely</p>
          </div>
        </div>
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-3 py-1.5 rounded-full text-xs font-bold shadow-md">
          Active
        </div>
      </div>

      <div className="space-y-4">
        <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 border-2 border-primary-100 shadow-md hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-primary-100 p-1.5 rounded-lg">
              <Mail className="w-4 h-4 text-primary-600" />
            </div>
            <span className="text-sm font-semibold text-gray-700">Admin Email</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <p className="text-base font-semibold text-gray-800 break-all">{tenant.admin_email}</p>
            <button
              onClick={() => copyToClipboard(tenant.admin_email, 'email')}
              className="p-2 hover:bg-primary-50 rounded-lg transition-colors flex-shrink-0"
              title="Copy email"
            >
              {copiedField === 'email' ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4 text-gray-400 hover:text-primary-600" />
              )}
            </button>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 border-2 border-primary-100 shadow-md hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-primary-100 p-1.5 rounded-lg">
              <Database className="w-4 h-4 text-primary-600" />
            </div>
            <span className="text-sm font-semibold text-gray-700">Database Name</span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <p className="text-base font-mono text-gray-800 break-all text-sm">{tenant.tenant_db}</p>
            <button
              onClick={() => copyToClipboard(tenant.tenant_db, 'db')}
              className="p-2 hover:bg-primary-50 rounded-lg transition-colors flex-shrink-0"
              title="Copy database name"
            >
              {copiedField === 'db' ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4 text-gray-400 hover:text-primary-600" />
              )}
            </button>
          </div>
        </div>

        <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border-2 border-yellow-300/50 rounded-xl p-4 shadow-md">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <div className="bg-yellow-200 p-1.5 rounded-lg">
              <Key className="w-4 h-4 text-yellow-700" />
            </div>
            <span className="text-sm font-bold text-yellow-800">Initial Password</span>
            <span className="text-xs bg-yellow-300 text-yellow-900 px-2.5 py-1 rounded-full font-semibold shadow-sm">
              Show Once
            </span>
          </div>
          <div className="flex items-center justify-between gap-2 mb-3">
            {showPassword ? (
              <>
                <p className="text-base font-mono text-yellow-900 font-bold break-all">{tenant.initial_password}</p>
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => copyToClipboard(tenant.initial_password, 'password')}
                    className="p-2 hover:bg-yellow-100 rounded-lg transition-colors"
                    title="Copy password"
                  >
                    {copiedField === 'password' ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-yellow-700" />
                    )}
                  </button>
                  <button
                    onClick={() => setShowPassword(false)}
                    className="text-xs text-yellow-700 hover:text-yellow-900 font-semibold px-2 py-1 hover:bg-yellow-100 rounded-lg transition-colors"
                  >
                    Hide
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2 w-full">
                <p className="text-sm text-yellow-700 italic">Password hidden</p>
                <button
                  onClick={() => setShowPassword(true)}
                  className="text-xs text-yellow-700 hover:text-yellow-900 font-semibold underline ml-auto"
                >
                  Show Again
                </button>
              </div>
            )}
          </div>
          <div className="bg-yellow-100/50 border border-yellow-200 rounded-lg p-2.5">
            <p className="text-xs text-yellow-800 font-medium flex items-center gap-1.5">
              <span>⚠️</span>
              <span>This password is shown only once. Make sure to save it securely!</span>
            </p>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 border-2 border-primary-100 shadow-md">
          <p className="text-sm text-gray-700 mb-1">
            <span className="font-semibold text-gray-800">Tenant ID:</span> <span className="font-mono">{tenant.tenant_id}</span>
          </p>
          <p className="text-xs text-gray-500">
            Created at {format(new Date(), 'PPpp')}
          </p>
        </div>
      </div>
    </div>
  );
}

