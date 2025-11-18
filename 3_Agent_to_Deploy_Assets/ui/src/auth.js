// Configuration
const authConfig = {
  ClientId: process.env.REACT_APP_CLIENT_ID || '6gepfa9rjuqcn2ql0k3na71417',
  AppWebDomain: process.env.REACT_APP_COGNITO_DOMAIN || 'biops-038198578763.auth.us-east-1.amazoncognito.com',
  UserPoolId: process.env.REACT_APP_USER_POOL_ID || 'us-east-1_p7YlBR2h9',
  RedirectUri: process.env.NODE_ENV === 'production' 
    ? `${window.location.origin}/callback`
    : 'http://localhost:3000/callback'
};

class AuthService {
  signIn() {
    const redirectUri = process.env.NODE_ENV === 'production' 
      ? `${window.location.origin}/callback`
      : 'http://localhost:3000/callback';
    
    const authUrl = `https://${authConfig.AppWebDomain}/oauth2/authorize?` +
      `client_id=${authConfig.ClientId}&` +
      `response_type=token&` +
      `scope=openid+email+profile&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}`;
    
    window.location.href = authUrl;
  }

  signOut() {
    localStorage.removeItem('id_token');
    localStorage.removeItem('access_token');
    
    const logoutUrl = `https://${authConfig.AppWebDomain}/logout?` +
      `client_id=${authConfig.ClientId}&` +
      `logout_uri=${encodeURIComponent(process.env.NODE_ENV === 'production' ? window.location.origin : 'http://localhost:3000/')}`;
    
    window.location.href = logoutUrl;
  }

  getCurrentUser() {
    return new Promise((resolve, reject) => {
      const idToken = localStorage.getItem('id_token');
      if (idToken) {
        try {
          const payload = JSON.parse(atob(idToken.split('.')[1]));
          resolve({
            username: payload['cognito:username'],
            email: payload.email,
            accessToken: localStorage.getItem('access_token')
          });
        } catch (error) {
          reject('Invalid token');
        }
      } else {
        reject('No valid session');
      }
    });
  }

  getAuthHeaders() {
    const idToken = localStorage.getItem('id_token');
    if (idToken) {
      return {
        'Authorization': `Bearer ${idToken}`,
        'Content-Type': 'application/json'
      };
    }
    return { 'Content-Type': 'application/json' };
  }

  isAuthenticated() {
    const idToken = localStorage.getItem('id_token');
    if (!idToken) return false;
    
    try {
      const payload = JSON.parse(atob(idToken.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch (error) {
      return false;
    }
  }
}

export default new AuthService();