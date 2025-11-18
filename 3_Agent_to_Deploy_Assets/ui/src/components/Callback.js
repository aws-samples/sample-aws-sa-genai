import React, { useEffect } from 'react';
import AuthService from '../auth';

const Callback = () => {
  useEffect(() => {
    // Parse the callback URL and handle the authentication result
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');

    if (error) {
      console.error('Authentication error:', error);
      window.location.href = '/';
    } else if (code) {
      // Let Cognito Auth handle the callback
      AuthService.auth.parseCognitoWebResponse(window.location.href);
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