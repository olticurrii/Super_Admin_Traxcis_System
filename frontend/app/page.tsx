'use client';

import { useState, useEffect } from 'react';
import TenantForm from '@/components/TenantForm';
import TenantCard from '@/components/TenantCard';
import { TenantResponse } from '@/lib/types';
import { Database, Shield, Zap, AlertCircle } from 'lucide-react';
import { healthCheck } from '@/lib/api';

export default function Home() {
  const [createdTenant, setCreatedTenant] = useState<TenantResponse | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await healthCheck();
        setBackendStatus('online');
      } catch (error) {
        setBackendStatus('offline');
      }
    };
    checkBackend();
  }, []);

  const handleTenantCreated = (tenant: TenantResponse) => {
    setCreatedTenant(tenant);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-lg border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-primary-600 to-primary-700 p-3 rounded-xl shadow-lg shadow-primary-500/30">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Super Admin Service
                </h1>
                <p className="text-sm text-gray-600 mt-0.5">Tenant Database Management</p>
              </div>
            </div>
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
              backendStatus === 'online' 
                ? 'bg-green-50 border border-green-200 text-green-700' 
                : backendStatus === 'offline'
                ? 'bg-red-50 border border-red-200 text-red-700'
                : 'bg-yellow-50 border border-yellow-200 text-yellow-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                backendStatus === 'online' 
                  ? 'bg-green-500 animate-pulse' 
                  : backendStatus === 'offline'
                  ? 'bg-red-500'
                  : 'bg-yellow-500 animate-pulse'
              }`}></div>
              <span>
                {backendStatus === 'online' 
                  ? 'Service Online' 
                  : backendStatus === 'offline'
                  ? 'Service Offline'
                  : 'Checking...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {backendStatus === 'offline' && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-start gap-3 shadow-md">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-bold text-red-900 mb-1">Backend Service Unavailable</h3>
              <p className="text-sm text-red-700 mb-2">
                The FastAPI backend is not running or not accessible at <code className="bg-red-100 px-1.5 py-0.5 rounded text-xs font-mono">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}</code>
              </p>
              <p className="text-xs text-red-600">
                Please start the backend server: <code className="bg-red-100 px-1.5 py-0.5 rounded font-mono">uvicorn app.main:app --reload --port 8001</code>
              </p>
            </div>
          </div>
        )}
        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">
          <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/50 hover:shadow-xl hover:scale-105 transition-all duration-300">
            <div className="bg-gradient-to-br from-primary-500 to-primary-600 w-14 h-14 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-primary-500/30">
              <Database className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-800 mb-2">Database Creation</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Automatically creates new PostgreSQL databases for each tenant
            </p>
          </div>

          <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/50 hover:shadow-xl hover:scale-105 transition-all duration-300">
            <div className="bg-gradient-to-br from-green-500 to-emerald-600 w-14 h-14 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-green-500/30">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-800 mb-2">Auto Migration</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Runs HRMS Alembic migrations on new tenant databases
            </p>
          </div>

          <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-white/50 hover:shadow-xl hover:scale-105 transition-all duration-300">
            <div className="bg-gradient-to-br from-purple-500 to-indigo-600 w-14 h-14 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-purple-500/30">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-800 mb-2">Secure Admin</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Seeds initial admin user with secure random password
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Create Tenant Form */}
          <div>
            <TenantForm onSuccess={handleTenantCreated} />
          </div>

          {/* Created Tenant Card */}
          <div>
            {createdTenant ? (
              <TenantCard tenant={createdTenant} />
            ) : (
              <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg p-12 border-2 border-dashed border-gray-300/50 text-center hover:border-primary-300/50 transition-colors">
                <div className="bg-gray-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Database className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">
                  No Tenant Created Yet
                </h3>
                <p className="text-sm text-gray-500 max-w-xs mx-auto">
                  Fill out the form to create a new tenant database. The credentials will appear here.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-10 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/50 rounded-xl p-6 shadow-md">
          <h3 className="text-lg font-bold text-blue-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Important Information
          </h3>
          <ul className="space-y-3 text-sm text-blue-800">
            <li className="flex items-start gap-3">
              <span className="text-blue-600 font-bold mt-0.5">•</span>
              <span>The initial admin password is shown only once. Make sure to save it securely.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 font-bold mt-0.5">•</span>
              <span>Each tenant gets its own isolated PostgreSQL database.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 font-bold mt-0.5">•</span>
              <span>HRMS migrations are automatically applied to new tenant databases.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 font-bold mt-0.5">•</span>
              <span>Tenant metadata is stored in the central super_admin_db.</span>
            </li>
          </ul>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-md border-t border-gray-200/50 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            Super Admin Service v1.0.0 • Tenant Management System
          </p>
        </div>
      </footer>
    </div>
  );
}

