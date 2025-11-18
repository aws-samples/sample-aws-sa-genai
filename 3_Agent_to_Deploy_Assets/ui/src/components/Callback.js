import React, { useEffect } from 'react';

const Callback = () => {
  useEffect(() => {
    // Parse tokens from URL hash (implicit flow)
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    
    const idToken = params.get('id_token');
    const accessToken = params.get('access_token');
    const error = params.get('error');

    if (error) {
      console.error('Authentication error:', error);
      window.location.href = '/';
    } else if (idToken && accessToken) {
      // Store tokens in localStorage
      localStorage.setItem('id_token', idToken);
      localStorage.setItem('access_token', accessToken);
      
      // Redirect to main app
      window.location.href = '/';
    } else {
      console.error('No tokens found in callback');
      window.location.href = '/';
    }
  }, []);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh' 
    }}>
      <div>Processing authentication...</div>
    </div>
  );
};

export default Callback;