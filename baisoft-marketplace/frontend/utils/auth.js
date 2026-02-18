// frontend/utils/auth.js

/**
 * Saves the JWT token to localStorage
 * @param {string} token - The JWT token to save
 * @returns {boolean} - True if saved successfully, false otherwise
 */
export const saveToken = (token) => {
  if (typeof window === 'undefined') return false;
  try {
    localStorage.setItem('token', token);
    return true;
  } catch (error) {
    console.error('Error saving token:', error);
    return false;
  }
};

/**
 * Retrieves the JWT token from localStorage
 * @returns {string|null} - The token if found, null otherwise
 */
export const getToken = () => {
  if (typeof window === 'undefined') return null;
  try {
    return localStorage.getItem('token');
  } catch (error) {
    console.error('Error getting token:', error);
    return null;
  }
};

/**
 * Checks if the user is logged in by verifying the token
 * @returns {boolean} - True if user is logged in and token is valid, false otherwise
 */
export const isLoggedIn = () => {
  const token = getToken();
  if (!token) return false;

  try {
    // Decode the token to check expiration
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    
    // Check if token is expired
    if (payload.exp < currentTime) {
      logout(); // Auto-logout if token is expired
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Error verifying token:', error);
    return false;
  }
};

/**
 * Logs out the user by removing the token
 * @returns {boolean} - True if logged out successfully, false otherwise
 */
export const logout = () => {
  if (typeof window === 'undefined') return false;
  try {
    localStorage.removeItem('token');
    // Redirect to login page
    window.location.href = '/login';
    return true;
  } catch (error) {
    console.error('Error during logout:', error);
    return false;
  }
};

/**
 * Gets user information from the token
 * @returns {Object|null} - User info if token is valid, null otherwise
 */
export const getUserInfo = () => {
  const token = getToken();
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      id: payload.user_id,
      businessId: payload.business_id,
      role: payload.role,
      email: payload.email,
      username: payload.username
    };
  } catch (error) {
    console.error('Error getting user info:', error);
    return null;
  }
};

/**
 * Higher-order component to protect routes
 * @param {React.Component} WrappedComponent - The component to protect
 * @returns {React.Component} - Protected component
 */
export const withAuth = (WrappedComponent) => {
  const Wrapper = (props) => {
    // Client-side check
    if (typeof window !== 'undefined' && !isLoggedIn()) {
      // Using setTimeout to prevent "Cannot update during an existing state transition" warning
      setTimeout(() => {
        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      }, 0);
      return <div>Redirecting to login...</div>;
    }

    return <WrappedComponent {...props} />;
  };

  // Copy static methods if they exist
  if (WrappedComponent.getInitialProps) {
    Wrapper.getInitialProps = async (ctx) => {
      // Server-side check
      if (ctx.req) {
        const { token } = ctx.req.cookies || {};
        if (!token) {
          ctx.res.writeHead(302, { Location: '/login' });
          ctx.res.end();
          return {};
        }
      }

      // Call getInitialProps of the wrapped component if it exists
      const componentProps = WrappedComponent.getInitialProps
        ? await WrappedComponent.getInitialProps(ctx)
        : {};

      return { ...componentProps };
    };
  }

  return Wrapper;
};

// Export all functions
export default {
  saveToken,
  getToken,
  isLoggedIn,
  logout,
  getUserInfo,
  withAuth
};
