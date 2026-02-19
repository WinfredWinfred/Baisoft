import { NextPage, NextPageContext } from 'next';
import { useRouter } from 'next/router';
import { ComponentType, useEffect } from 'react';

// Token payload type
type TokenData = {
  user_id?: number;
  business_id?: number;
  role?: string;
  exp: number;
  [key: string]: any;
};

// Type for components with getInitialProps
type WithInitialProps<IP = any> = {
  getInitialProps?: (ctx: NextPageContext) => Promise<IP>;
};

// Type for the wrapped component props
type WithAuthProps = {
  [key: string]: any;
};

// Type for the wrapped component
type WrappedComponentType<P = {}, IP = {}> = ComponentType<P> & {
  getInitialProps?: (ctx: NextPageContext) => Promise<IP>;
};

// Save JWT token to localStorage
export const saveToken = (token: string): boolean => {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem('token', token);
      return true;
    } catch (error) {
      console.error('Error saving token:', error);
      return false;
    }
  }
  return false;
};

// Retrieve JWT token from localStorage
export const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    try {
      return localStorage.getItem('token');
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  }
  return null;
};

// Get token data (payload) without verification
export const getTokenData = (): TokenData | null => {
  const token = getToken();
  if (!token) return null;

  try {
    // Split the token into parts
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    // Decode the payload (middle part)
    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
};

// Check if user is authenticated
export const isLoggedIn = (): boolean => {
  const token = getToken();
  if (!token) return false;

  const tokenData = getTokenData();
  if (!tokenData) return false;

  // Check if token is expired
  const currentTime = Math.floor(Date.now() / 1000);
  return tokenData.exp > currentTime;
};

// Get user role from token
export const getUserRole = (): string | null => {
  const tokenData = getTokenData();
  return tokenData?.role || null;
};

// Get user ID from token
export const getUserId = (): number | null => {
  const tokenData = getTokenData();
  return tokenData?.user_id || null;
};

// Get user's business ID from token
export const getUserBusinessId = (): number | null => {
  const tokenData = getTokenData();
  return tokenData?.business_id || null;
};

// Get full user info from token
export const getUserInfo = (): TokenData | null => {
  return getTokenData();
};

// Logout user by removing token
export const logout = (): boolean => {
  if (typeof window !== 'undefined') {
    try {
      localStorage.removeItem('token');
      // Optional: Clear any other auth-related data
      // localStorage.removeItem('user');
      window.location.href = '/login';
      return true;
    } catch (error) {
      console.error('Error during logout:', error);
      return false;
    }
  }
  return false;
};

// Higher-order component for protecting routes
export const withAuth = <P extends object = {}, IP = {}>(
  WrappedComponent: WrappedComponentType<P, IP>
): NextPage<P & WithAuthProps, IP> & WithInitialProps<IP> => {
  const Wrapper: NextPage<P & WithAuthProps, IP> & WithInitialProps<IP> = (props) => {
    const router = useRouter();
    
    // Client-side check
    useEffect(() => {
      const isAuthenticated = isLoggedIn();
      if (!isAuthenticated) {
        router.push('/login');
      }
    }, [router]);

    return <WrappedComponent {...props} />;
  };

  Wrapper.getInitialProps = async (ctx: NextPageContext): Promise<IP> => {
    // On server, check the token in cookies
    if (ctx.req) {
      // Server-side check would go here
      // For now, we'll just pass through and let client-side handle it
    }

    // If no token or invalid token, redirect to login
    const isAuthenticated = isLoggedIn();
    if (!isAuthenticated) {
      if (ctx.res) {
        // Server-side redirect
        ctx.res.writeHead(302, { Location: '/login' });
        ctx.res.end();
      } else {
        // Client-side redirect
        window.location.href = '/login';
      }
      return {} as unknown as IP;
    }

    // Call getInitialProps of the wrapped component if it exists
    let componentProps = {} as IP;
    if (WrappedComponent.getInitialProps) {
      componentProps = await WrappedComponent.getInitialProps(ctx);
    }

    return componentProps;
  };

  return Wrapper;
};

// Redirect to login if not authenticated
export const requireAuth = (context: NextPageContext) => {
  const isServer = typeof window === 'undefined';
  
  if (isServer && context.res) {
    // Server-side redirect
    context.res.writeHead(302, { Location: '/login' });
    context.res.end();
  } else if (!isServer && !isLoggedIn()) {
    // Client-side redirect
    window.location.href = '/login';
  }
  
  return { props: {} };
};

// Export all auth functions
export default {
  saveToken,
  getToken,
  isLoggedIn,
  getUserRole,
  getUserId,
  getUserBusinessId,
  getUserInfo,
  logout,
  withAuth,
  requireAuth
};
