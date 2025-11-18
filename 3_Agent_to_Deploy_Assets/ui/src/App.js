import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import JobForm from './components/JobForm';
import JobsList from './components/JobsList';
import JobDetail from './components/JobDetail';
import Login from './components/Login';
import Callback from './components/Callback';
import AuthService from './auth';

function App() {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      if (AuthService.isAuthenticated()) {
        const currentUser = await AuthService.getCurrentUser();
        setUser(currentUser);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.log('Not authenticated');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    AuthService.signOut();
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  // Handle OAuth callback
  if (location.pathname === '/callback') {
    return <Callback />;
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div>
      <div className="header">
        <div className="container">
          <h1>BIOPS Asset Deployment</h1>
          <nav style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <Link to="/" style={{color: 'white', marginRight: '1rem'}}>Jobs</Link>
              <Link to="/new" style={{color: 'white'}}>New Job</Link>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ color: 'white', marginRight: '1rem' }}>Welcome, {user?.email}</span>
              <button 
                onClick={handleLogout}
                style={{
                  padding: '5px 10px',
                  backgroundColor: 'transparent',
                  color: 'white',
                  border: '1px solid white',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Logout
              </button>
            </div>
          </nav>
        </div>
      </div>
      
      <div className="container">
        <Routes>
          <Route path="/" element={<JobsList />} />
          <Route path="/new" element={<JobForm />} />
          <Route path="/jobs/:jobId" element={<JobDetail />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;