import { NextPage, NextPageContext } from 'next';
import { useRouter } from 'next/router';
import { ComponentType, useEffect } from 'react';

type TokenData = {
  user_id?: number;
  business_id?: number;
  role?: string;
  exp: number;
  [key: string]: any;
};

type WithInitialProps<IP = any> = {
  getInitialProps?: (ctx: NextPageContext) => Promise<IP>;
};

type WithAuthProps = {
  [key: string]: any;
};

type WrappedComponentType<P = {}, IP = {}> = ComponentType<P> & {
  getInitialProps?: (ctx: NextPageContext) => Promise<IP>;
};

/**
 * Save JWT token to browser localStorage
 */
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

/**
 * Retrieve JWT token from localStorage
 */
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

/**
 * Decode JWT token payload without verification
 * Returns the decoded payload or null if invalid
 */
export const getTokenData = (): TokenData | null => {
  const token = getToken();
  if (!token) return null;

  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    
    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
};

/**
 * Check if user is authenticated with valid token
 */
export const isLoggedIn = (): boolean => {
  const token = getToken();
  if (!token) return false;

  const tokenData = getTokenData();
  if (!tokenData) return false;

  const currentTime = Math.floor(Date.now() / 1000);
  return tokenData.exp > currentTime;
};

/**
 * Get user role from token
 */
export const getUserRole = (): string | null => {
  const tokenData = getTokenData();
  return tokenData?.role || null;
};

/**
 * Get user ID from token
 */
export const getUserId = (): number | null => {
  const tokenData = getTokenData();
  return tokenData?.user_id || null;
};

/**
 * Get user's business ID from token
 */
export const getUserBusinessId = (): number | null => {
  const tokenData = getTokenData();
  return tokenData?.business_id || null;
};

/**
 * Get full user info from token
 */
export const getUserInfo = (): TokenData | null => {
  return getTokenData();
};

/**
 * Logout user by removing token and redirecting to login
 */
export const logout = (): boolean => {
  if (typeof window !== 'undefined') {
    try {
      localStorage.removeItem('token');
      window.location.href = '/login';
      return true;
    } catch (error) {
      console.error('Error during logout:', error);
      return false;
    }
  }
  return false;
};

/**
 * Higher-order component for protecting routes
 * Redirects to login if user is not authenticated
 */
export const withAuth = <P extends object = {}, IP = {}>(
  WrappedComponent: WrappedComponentType<P, IP>
): NextPage<P & WithAuthProps, IP> & WithInitialProps<IP> => {
  const Wrapper: NextPage<P & WithAuthProps, IP> & WithInitialProps<IP> = (props) => {
    const router = useRouter();
    
    useEffect(() => {
      const isAuthenticated = isLoggedIn();
      if (!isAuthenticated) {
        router.push('/login');
      }
    }, [router]);

    return <WrappedComponent {...props} />;
  };

  Wrapper.getInitialProps = async (ctx: NextPageContext): Promise<IP> => {
    const isAuthenticated = isLoggedIn();
    if (!isAuthenticated) {
      if (ctx.res) {
        ctx.res.writeHead(302, { Location: '/login' });
        ctx.res.end();
      } else {
        window.location.href = '/login';
      }
      return {} as unknown as IP;
    }

    let componentProps = {} as IP;
    if (WrappedComponent.getInitialProps) {
      componentProps = await WrappedComponent.getInitialProps(ctx);
    }

    return componentProps;
  };

  return Wrapper;
};

export default {
  saveToken,
  getToken,
  isLoggedIn,
  getUserRole,
  getUserId,
  getUserBusinessId,
  getUserInfo,
  logout,
  withAuth
};
