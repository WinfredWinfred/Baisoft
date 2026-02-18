'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getDashboardProducts, approveProduct, logout, getCurrentUser } from '../lib/api';

interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  status: string;
  created_at: string;
}

interface User {
  id: number;
  username: string;
  role: string;
}

export default function DashboardPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('token');

    if (!token) {
      router.push('/login');
      return;
    }

    fetchUserAndProducts();
  }, [router]);

  const fetchUserAndProducts = async () => {
    try {
      setLoading(true);
      
      // Fetch current user info
      const userData = await getCurrentUser();
      if (userData) {
        setUser(userData);
      }
      
      // Fetch products
      await fetchProducts();
    } catch (err: any) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await getDashboardProducts();
      setProducts(response.results || response);
    } catch (err: any) {
      setError('Failed to load products');
      console.error(err);
    }
  };

  const handleApprove = async (productId: number) => {
    try {
      await approveProduct(productId);
      // Refresh products list
      fetchProducts();
    } catch (err: any) {
      alert('Failed to approve product');
      console.error(err);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Product Dashboard</h1>
            {user && <p className="text-gray-600 mt-1">{user.username} ({user.role})</p>}
          </div>
          <button
            onClick={handleLogout}
            className="bg-red-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading products...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No products found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <div key={product.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-bold text-gray-900">{product.name}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(product.status)}`}>
                    {product.status}
                  </span>
                </div>

                <p className="text-gray-600 text-sm mb-4">{product.description}</p>

                <div className="mb-4">
                  <p className="text-2xl font-bold text-blue-600">${product.price}</p>
                </div>

                <div className="flex gap-2">
                  {product.status !== 'approved' && user?.role === 'admin' && (
                    <button
                      onClick={() => handleApprove(product.id)}
                      className="flex-1 bg-green-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-green-700 transition"
                    >
                      Approve
                    </button>
                  )}
                  <button className="flex-1 bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition">
                    Edit
                  </button>
                </div>

                <p className="text-gray-500 text-xs mt-4">
                  Created: {new Date(product.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
