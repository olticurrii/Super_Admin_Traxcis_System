'use client';

import { useState, useEffect, useMemo } from 'react';
import { TenantInfo } from '@/lib/types';
import { getTenants, deleteTenant, toggleTenantStatus } from '@/lib/api';
import { 
  Database, 
  Mail, 
  Server, 
  Calendar, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle, 
  XCircle,
  Search,
  Trash2,
  X,
  AlertTriangle,
  Power,
  PowerOff
} from 'lucide-react';
import { format } from 'date-fns';

export default function TenantList() {
  const [tenants, setTenants] = useState<TenantInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [tenantToDelete, setTenantToDelete] = useState<TenantInfo | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [togglingStatus, setTogglingStatus] = useState<number | null>(null);

  const fetchTenants = async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await getTenants();
      setTenants(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tenants');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchTenants();
    setRefreshing(false);
  };

  const handleDeleteClick = (tenant: TenantInfo) => {
    setTenantToDelete(tenant);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!tenantToDelete) return;

    try {
      setDeleting(true);
      await deleteTenant(tenantToDelete.id);
      // Remove from local state
      setTenants(tenants.filter(t => t.id !== tenantToDelete.id));
      setDeleteModalOpen(false);
      setTenantToDelete(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete tenant');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setTenantToDelete(null);
  };

  const handleToggleStatus = async (tenant: TenantInfo) => {
    try {
      setTogglingStatus(tenant.id);
      const updatedTenant = await toggleTenantStatus(tenant.id);
      
      // Update the tenant in the local state
      setTenants(tenants.map(t => 
        t.id === tenant.id ? updatedTenant : t
      ));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to toggle tenant status');
    } finally {
      setTogglingStatus(null);
    }
  };

  useEffect(() => {
    fetchTenants();
  }, []);

  // Filter and search tenants
  const filteredTenants = useMemo(() => {
    let filtered = tenants;

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(tenant => tenant.status === statusFilter);
    }

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(tenant => 
        tenant.name.toLowerCase().includes(query) ||
        tenant.db_name.toLowerCase().includes(query) ||
        tenant.admin_email.toLowerCase().includes(query) ||
        tenant.id.toString().includes(query)
      );
    }

    return filtered;
  }, [tenants, searchQuery, statusFilter]);

  if (loading && !refreshing) {
    return (
      <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg p-12 border border-white/50">
        <div className="flex flex-col items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-600">Loading tenants...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg p-8 border border-white/50">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Error Loading Tenants</h3>
            <p className="text-sm text-red-600 mb-4">{error}</p>
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (tenants.length === 0) {
    return (
      <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg p-12 border-2 border-dashed border-gray-300/50 text-center">
        <div className="bg-gray-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
          <Database className="w-10 h-10 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          No Tenants Found
        </h3>
        <p className="text-sm text-gray-500 max-w-xs mx-auto">
          Create your first tenant using the form above to get started.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white/70 backdrop-blur-sm rounded-xl shadow-lg border border-white/50 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Database className="w-6 h-6 text-white" />
              <div>
                <h2 className="text-xl font-bold text-white">Tenant Databases</h2>
                <p className="text-sm text-primary-100">
                  {filteredTenants.length} of {tenants.length} {tenants.length === 1 ? 'tenant' : 'tenants'}
                  {searchQuery || statusFilter !== 'all' ? ' (filtered)' : ''}
                </p>
              </div>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 hover:bg-primary-500/50 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh list"
            >
              <RefreshCw className={`w-5 h-5 text-white ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Search and Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Search Input */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name, email, database, or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-10 py-2 rounded-lg border border-white/30 bg-white/20 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50 focus:bg-white/30"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/60 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Status Filter */}
            <div className="flex gap-2">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  statusFilter === 'all'
                    ? 'bg-white text-primary-700'
                    : 'bg-white/20 text-white hover:bg-white/30'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setStatusFilter('active')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  statusFilter === 'active'
                    ? 'bg-white text-primary-700'
                    : 'bg-white/20 text-white hover:bg-white/30'
                }`}
              >
                Active
              </button>
              <button
                onClick={() => setStatusFilter('inactive')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  statusFilter === 'inactive'
                    ? 'bg-white text-primary-700'
                    : 'bg-white/20 text-white hover:bg-white/30'
                }`}
              >
                Inactive
              </button>
            </div>
          </div>
        </div>

        {/* Tenant List */}
        {filteredTenants.length === 0 ? (
          <div className="p-12 text-center">
            <Search className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              No tenants match your filters
            </h3>
            <p className="text-sm text-gray-500">
              Try adjusting your search or filter criteria
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('all');
              }}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredTenants.map((tenant) => (
              <div
                key={tenant.id}
                className={`p-6 transition-colors ${
                  tenant.status === 'inactive' 
                    ? 'bg-gray-100/50 opacity-75' 
                    : 'hover:bg-gray-50/50'
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className={`text-lg font-bold ${
                        tenant.status === 'inactive' ? 'text-gray-500' : 'text-gray-800'
                      }`}>
                        {tenant.name}
                      </h3>
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                          tenant.status === 'active'
                            ? 'bg-green-100 text-green-700 border border-green-200'
                            : 'bg-red-100 text-red-700 border border-red-200'
                        }`}
                      >
                        {tenant.status === 'active' ? (
                          <span className="flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            Active
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <XCircle className="w-3 h-3" />
                            Disabled
                          </span>
                        )}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 flex items-center gap-1.5">
                      <span className="font-semibold">ID:</span>
                      <span className="font-mono">{tenant.id}</span>
                    </p>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex items-center gap-2">
                    {/* Toggle Status Button */}
                    <button
                      onClick={() => handleToggleStatus(tenant)}
                      disabled={togglingStatus === tenant.id}
                      className={`p-2 rounded-lg transition-colors group ${
                        tenant.status === 'active'
                          ? 'text-orange-600 hover:bg-orange-50'
                          : 'text-green-600 hover:bg-green-50'
                      } disabled:opacity-50`}
                      title={tenant.status === 'active' ? 'Disable tenant' : 'Enable tenant'}
                    >
                      {togglingStatus === tenant.id ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-current"></div>
                      ) : tenant.status === 'active' ? (
                        <PowerOff className="w-5 h-5 group-hover:scale-110 transition-transform" />
                      ) : (
                        <Power className="w-5 h-5 group-hover:scale-110 transition-transform" />
                      )}
                    </button>
                    
                    {/* Delete Button */}
                    <button
                      onClick={() => handleDeleteClick(tenant)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors group"
                      title="Delete tenant"
                    >
                      <Trash2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                    </button>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  {/* Database Info */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200/50">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="bg-blue-100 p-1.5 rounded-lg">
                        <Database className="w-4 h-4 text-blue-600" />
                      </div>
                      <span className="text-sm font-semibold text-blue-900">Database</span>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <p className="text-xs text-blue-700 font-medium">Name</p>
                        <p className="text-sm font-mono text-blue-900 break-all">{tenant.db_name}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <p className="text-xs text-blue-700 font-medium">User</p>
                          <p className="text-sm font-mono text-blue-900">{tenant.db_user}</p>
                        </div>
                        <div>
                          <p className="text-xs text-blue-700 font-medium">Port</p>
                          <p className="text-sm font-mono text-blue-900">{tenant.db_port}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Server & Admin Info */}
                  <div className="space-y-4">
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200/50">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="bg-purple-100 p-1.5 rounded-lg">
                          <Server className="w-4 h-4 text-purple-600" />
                        </div>
                        <span className="text-sm font-semibold text-purple-900">Host</span>
                      </div>
                      <p className="text-sm font-mono text-purple-900">{tenant.db_host}</p>
                    </div>

                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200/50">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="bg-green-100 p-1.5 rounded-lg">
                          <Mail className="w-4 h-4 text-green-600" />
                        </div>
                        <span className="text-sm font-semibold text-green-900">Admin</span>
                      </div>
                      <p className="text-sm text-green-900 break-all">{tenant.admin_email}</p>
                    </div>
                  </div>
                </div>

                {/* Created At */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Created on {format(new Date(tenant.created_at), 'PPpp')}</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && tenantToDelete && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="bg-red-100 p-3 rounded-full">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">Delete Tenant?</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Are you sure you want to delete this tenant? This action cannot be undone.
                </p>
                <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                  <p className="text-sm font-semibold text-gray-900 mb-1">{tenantToDelete.name}</p>
                  <p className="text-xs text-gray-600 font-mono">{tenantToDelete.db_name}</p>
                  <p className="text-xs text-gray-600">{tenantToDelete.admin_email}</p>
                </div>
                <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-xs text-yellow-800 font-medium">
                    ⚠️ Note: This only removes the tenant record. The PostgreSQL database will NOT be automatically deleted.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={handleDeleteCancel}
                disabled={deleting}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50 flex items-center gap-2"
              >
                {deleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete Tenant
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
