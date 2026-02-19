import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { withAuth, getUserInfo } from '../../../../utils/auth';
import { apiService } from '../../../../utils/api';
import Link from 'next/link';

function EditProduct() {
  const router = useRouter();
  const { id } = router.query;
  const user = getUserInfo();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');
  const [product, setProduct] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    status: 'draft',
  });

  // Role-based permissions
  const canEdit = user && (user.role === 'admin' || user.role === 'editor');
  const canDelete = user && user.role === 'admin';
  const canChangeStatus = user && (user.role === 'admin' || user.role === 'editor');

  useEffect(() => {
    if (id) {
      fetchProduct();
    }
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await apiService.get(`/products/${id}/`);
      setProduct(response.data);
      setFormData({
        name: response.data.name,
        description: response.data.description,
        price: response.data.price,
        status: response.data.status,
      });
    } catch (err) {
      setError('Failed to load product');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      const updateData = {
        name: formData.name,
        description: formData.description,
        price: parseFloat(formData.price),
      };

      // Only admins can update status
      if (canChangeStatus) {
        updateData.status = formData.status;
      }

      await apiService.put(`/products/${id}/`, updateData);
      router.push('/dashboard/products');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update product');
      console.error('Error:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);
    setError('');

    try {
      await apiService.delete(`/products/${id}/`);
      router.push('/dashboard/products');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete product');
      console.error('Error:', err);
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-900"></div>
      </div>
    );
  }

  if (!canEdit) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h2 className="mt-4 text-2xl font-bold text-gray-900">Access Denied</h2>
          <p className="mt-2 text-gray-600">You don't have permission to edit products.</p>
          <Link href="/dashboard/products" className="mt-4 inline-block text-blue-900 hover:text-blue-800">
            Back to Products
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link
            href="/dashboard/products"
            className="text-sm text-blue-900 hover:text-blue-800 font-medium"
          >
            ← Back to Products
          </Link>
        </div>

        <div className="bg-white shadow rounded-lg border border-gray-200">
          <div className="px-6 py-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Edit Product</h1>

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

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Product Name
                </label>
                <input
                  type="text"
                  name="name"
                  id="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  id="description"
                  required
                  rows={4}
                  value={formData.description}
                  onChange={handleChange}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-1">
                  Price ($)
                </label>
                <input
                  type="number"
                  name="price"
                  id="price"
                  required
                  step="0.01"
                  min="0"
                  value={formData.price}
                  onChange={handleChange}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                />
              </div>

              {canChangeStatus ? (
                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                    Product Status
                    {user.role === 'admin' && <span className="ml-2 text-xs text-gray-500">(Admin can set any status)</span>}
                    {user.role === 'editor' && <span className="ml-2 text-xs text-gray-500">(Editors can set draft or pending)</span>}
                  </label>
                  <select
                    name="status"
                    id="status"
                    value={formData.status}
                    onChange={handleChange}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                  >
                    <option value="draft">Draft - Not visible to anyone</option>
                    <option value="pending_approval">Pending Approval - Awaiting review</option>
                    {user.role === 'admin' && (
                      <option value="approved">Approved - Visible to public</option>
                    )}
                  </select>
                  <div className={`mt-2 p-3 rounded-lg text-sm ${
                    formData.status === 'approved' ? 'bg-green-50 text-green-700' :
                    formData.status === 'pending_approval' ? 'bg-yellow-50 text-yellow-700' :
                    'bg-gray-50 text-gray-700'
                  }`}>
                    {formData.status === 'draft' && 'Product is saved as draft and can be edited anytime'}
                    {formData.status === 'pending_approval' && 'Product is awaiting approval from an approver'}
                    {formData.status === 'approved' && 'Product is live and visible in the public marketplace'}
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 px-4 py-3 rounded-lg">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Current Status:</span>{' '}
                    <span className="capitalize">{product?.status?.replace('_', ' ')}</span>
                  </p>
                  {product?.status === 'draft' && (
                    <p className="text-xs text-gray-500 mt-1">
                      Submit for approval to make this product visible to approvers
                    </p>
                  )}
                </div>
              )}

              <div className="flex justify-between pt-4 border-t border-gray-200">
                {canDelete ? (
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={deleting}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    {deleting ? 'Deleting...' : 'Delete Product'}
                  </button>
                ) : (
                  <div></div>
                )}

                <div className="flex gap-3">
                  <Link
                    href="/dashboard/products"
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </Link>
                  <button
                    type="submit"
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-900 hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-900 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default withAuth(EditProduct);
