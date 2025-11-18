import React from 'react';
import AuthService from '../auth';

const Login = () => {
  const handleLogin = () => {
    AuthService.signIn();
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh',
      flexDirection: 'column'
    }}>
      <h1>BIOPS Asset Management</h1>
      <p>Please sign in to continue</p>
      <button 
        onClick={handleLogin}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Sign In with Cognito
      </button>
    </div>
  );
};

export default Login;