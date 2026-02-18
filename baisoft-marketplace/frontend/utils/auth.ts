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

// Token payload type
type TokenData = {
  user_id?: number;
  business_id?: number;
  role?: string;
  exp: number;
  [key: string]: any;
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

// Higher-order component type for withAuth
type GetInitialProps = (ctx: any) => Promise<any>;

type WithAuthComponent = {
  getInitialProps?: GetInitialProps;
} & React.ComponentType<any>;

// Higher-order component for protecting routes
export const withAuth = (WrappedComponent: WithAuthComponent) => {
  const Wrapper: WithAuthComponent = (props) => {
    // This will be handled by getServerSideProps
    return <WrappedComponent {...props} />;
  };

  Wrapper.getInitialProps = async (ctx: any) => {
    // On server, check the token in cookies
    if (ctx.req) {
      // Server-side check would go here
      // For now, we'll just pass through and let client-side handle it
    }

    // If no token or invalid token, redirect to login
    const isAuthenticated = isLoggedIn();
    if (!isAuthenticated && ctx.res) {
      ctx.res.writeHead(302, { Location: '/login' });
      ctx.res.end();
      return {};
    }

    // If the wrapped component has getInitialProps, call it
    let componentProps = {};
    if (WrappedComponent.getInitialProps) {
      componentProps = await WrappedComponent.getInitialProps(ctx);
    }

    return { ...componentProps };
  };

  return Wrapper;
};

// Redirect to login if not authenticated
export const requireAuth = (context: any) => {
  const isServer = typeof window === 'undefined';
  
  if (isServer) {
    // Server-side check would go here
    const { res } = context;
    res.writeHead(302, { Location: '/login' });
    res.end();
    return { props: {} };
  } else {
    // Client-side check
    if (!isLoggedIn()) {
      window.location.href = '/login';
      return { props: {} };
    }
    return { props: {} };
  }
};
