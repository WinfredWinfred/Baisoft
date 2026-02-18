import { useRouter } from 'next/router';
import Navbar from '../components/Navbar';
import DashboardLayout from '../components/DashboardLayout';
import '../styles/globals.css';

function MyApp({ Component, pageProps }) {
  const router = useRouter();
  const isDashboard = router.pathname.startsWith('/dashboard');
  
  const content = (
    <>
      <Navbar />
      <main>
        <Component {...pageProps} />
      </main>
    </>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {isDashboard ? (
        <DashboardLayout>
          {content}
        </DashboardLayout>
      ) : (
        content
      )}
    </div>
  );
}

export default MyApp;
