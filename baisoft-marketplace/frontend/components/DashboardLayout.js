import { getUserInfo } from '../utils/auth';

export default function DashboardLayout({ children }) {
  const user = getUserInfo();
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="text-sm text-gray-500">
              Logged in as: <span className="font-medium text-indigo-600 capitalize">{user?.role || 'User'}</span>
              {user?.business_name && (
                <span className="ml-4">
                  Business: <span className="font-medium">{user.business_name}</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      {children}
    </div>
  );
}
