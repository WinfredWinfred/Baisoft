import { useRouter } from 'next/router';
import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { withAuth, getUserInfo } from '../../utils/auth';
import { apiService } from '../../utils/api';
import config from '../../config';

function DashboardProducts() {
  const router = useRouter();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState({});
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const user = getUserInfo();
  
  // Role-based permissions
  const canEdit = user && (user.role === 'admin' || user.role === 'editor');
  const canChangeStatus = user && user.role === 'admin';
  const canViewAll = user && (user.role === 'admin' || user.role === 'editor' || user.role === 'approver');
  const isViewer = user && user.role === 'viewer';

  useEffect(() => {
    fetchProducts();
    
    // Check for success message from product creation
    if (router.query.created === 'true') {
      const status = router.query.status || 'draft';
      const statusText = status.replace('_', ' ');
      setSuccess(`Product created successfully with status "${statusText}"!`);
      setTimeout(() => setSuccess(''), config.ui.notificationDuration);
      
      // Clean up URL
      router.replace('/dashboard/products', undefined, { shallow: true });
    }
  }, [router.query]);

  const fetchProducts = async () => {
    try {
      setError('');
      let response;
      
      // Viewers can only see approved products from public endpoint
      if (isViewer) {
        response = await apiService.get('/products/public/');
      } else {
        // Admin, Editor, Approver can see all internal products
        response = await apiService.get('/products/internal/');
      }
      
      const data = response.data.results || response.data;
      setProducts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching products:', err);
      if (err.response?.status === 403) {
        setError('You do not have permission to view products.');
      } else {
        setError('Failed to load products. Please try again.');
      }
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (productId, newStatus) => {
    // Prevent editors from setting approved status
    if (user.role === 'editor' && newStatus === 'approved') {
      setError('Editors cannot approve products. Only admins can set approved status.');
      setTimeout(() => setError(''), 5000);
      return;
    }

    setUpdatingStatus(prev => ({ ...prev, [productId]: true }));
    setError('');
    setSuccess('');

    try {
      const product = products.find(p => p.id === productId);
      await apiService.put(`/products/${productId}/`, {
        name: product.name,
        description: product.description,
        price: product.price,
        status: newStatus,
      });
      
      // Update local state
      setProducts(prev => prev.map(p => 
        p.id === productId ? { ...p, status: newStatus } : p
      ));
      
      // Show success message
      const statusText = newStatus.replace('_', ' ');
      setSuccess(`Product status updated to "${statusText}" successfully!`);
      setTimeout(() => setSuccess(''), config.ui.notificationDuration);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update product status');
      setTimeout(() => setError(''), config.ui.notificationDuration);
      console.error('Error updating status:', err);
    } finally {
      setUpdatingStatus(prev => ({ ...prev, [productId]: false }));
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      draft: 'bg-gray-100 text-gray-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
    };

    const statusText = status.replace('_', ' ');
    
    return (
      <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
        statusMap[status] || 'bg-gray-100 text-gray-800'
      }`}>
        {statusText.charAt(0).toUpperCase() + statusText.slice(1)}
      </span>
    );
  };

  // Filter and search products with useMemo for performance
  const filteredProducts = useMemo(() => {
    return products.filter(product => {
      const matchesStatus = filterStatus === 'all' || product.status === filterStatus;
      const matchesSearch = searchTerm === '' || 
        product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.description.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [products, filterStatus, searchTerm]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading products...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center sm:justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Products</h1>
            <p className="mt-1 text-sm text-gray-500">
              {isViewer ? 'View approved products' : 'Manage all products in your business'}
            </p>
          </div>
          {canEdit && (
            <div className="mt-4 sm:mt-0">
              <Link
                href="/dashboard/products/new"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-900 hover:bg-blue-800"
              >
                <svg className="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create Product
              </Link>
            </div>
          )}
        </div>

        {/* Search and Filter */}
        {!isViewer && (
          <div className="mb-6 flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Search products..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                />
              </div>
            </div>
            <div className="sm:w-48">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="draft">Draft</option>
                <option value="pending_approval">Pending Approval</option>
                <option value="approved">Approved</option>
              </select>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="ml-3 text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border-l-4 border-green-400 p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="ml-3 text-sm text-green-700">{success}</p>
            </div>
          </div>
        )}

        <div className="bg-white shadow rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Price
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created By
                  </th>
                  <th scope="col" className="relative px-6 py-3">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredProducts.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-sm text-gray-500">
                      <svg className="mx-auto h-12 w-12 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <p className="font-medium text-gray-900">
                        {searchTerm || filterStatus !== 'all' ? 'No products match your filters' : 'No products found'}
                      </p>
                      {canEdit && !searchTerm && filterStatus === 'all' && (
                        <p className="mt-1">Get started by creating a new product.</p>
                      )}
                      {isViewer && (
                        <p className="mt-1">No approved products available yet.</p>
                      )}
                    </td>
                  </tr>
                ) : (
                  filteredProducts.map((product) => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{product.name}</div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">{product.description}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {canChangeStatus ? (
                          <select
                            value={product.status}
                            onChange={(e) => handleStatusChange(product.id, e.target.value)}
                            disabled={updatingStatus[product.id]}
                            aria-label={`Change status for ${product.name}`}
                            aria-busy={updatingStatus[product.id]}
                            className="text-xs font-semibold rounded-full px-3 py-1 border-0 focus:ring-2 focus:ring-blue-900 disabled:opacity-50 cursor-pointer"
                            style={{
                              backgroundColor: product.status === 'approved' ? '#dcfce7' : 
                                             product.status === 'pending_approval' ? '#fef3c7' : '#f3f4f6',
                              color: product.status === 'approved' ? '#166534' : 
                                     product.status === 'pending_approval' ? '#92400e' : '#1f2937'
                            }}
                            data-testid={`status-select-${product.id}`}
                          >
                            <option value="draft">Draft</option>
                            <option value="pending_approval">Pending Approval</option>
                            {user.role === 'admin' && <option value="approved">Approved</option>}
                          </select>
                        ) : (
                          getStatusBadge(product.status)
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${parseFloat(product.price || 0).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {product.created_by_username || product.created_by?.username || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {canEdit && (
                          <Link
                            href={`/dashboard/products/${product.id}/edit`}
                            className="text-blue-900 hover:text-blue-800 mr-4"
                          >
                            Edit
                          </Link>
                        )}
                        <Link
                          href={`/products/${product.id}`}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default withAuth(DashboardProducts);
