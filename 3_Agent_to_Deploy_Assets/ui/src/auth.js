import { CognitoAuth } from 'amazon-cognito-auth-js';

// Configuration - update these values after deployment
const authConfig = {
  ClientId: 'YOUR_USER_POOL_CLIENT_ID', // From CDK output
  AppWebDomain: 'biops-YOUR_ACCOUNT_ID.auth.us-east-1.amazoncognito.com', // From CDK output
  TokenScopesArray: ['openid', 'email', 'profile'],
  RedirectUriSignIn: 'http://localhost:3000/callback',
  RedirectUriSignOut: 'http://localhost:3000/',
  UserPoolId: 'YOUR_USER_POOL_ID', // From CDK output
  AdvancedSecurityDataCollectionFlag: false
};

class AuthService {
  constructor() {
    this.auth = new CognitoAuth(authConfig);
    this.auth.userhandler = {
      onSuccess: (result) => {
        console.log('Sign in success', result);
        this.onAuthSuccess(result);
      },
      onFailure: (err) => {
        console.log('Sign in failure', err);
        this.onAuthFailure(err);
      }
    };
  }

  signIn() {
    this.auth.getSession();
  }

  signOut() {
    this.auth.signOut();
  }

  getCurrentUser() {
    return new Promise((resolve, reject) => {
      const session = this.auth.getCachedSession();
      if (session && session.isValid()) {
        resolve({
          username: session.getIdToken().payload['cognito:username'],
          email: session.getIdToken().payload.email,
          accessToken: session.getAccessToken().getJwtToken()
        });
      } else {
        reject('No valid session');
      }
    });
  }

  getAuthHeaders() {
    const session = this.auth.getCachedSession();
    if (session && session.isValid()) {
      return {
        'Authorization': `Bearer ${session.getIdToken().getJwtToken()}`,
        'Content-Type': 'application/json'
      };
    }
    return { 'Content-Type': 'application/json' };
  }

  isAuthenticated() {
    const session = this.auth.getCachedSession();
    return session && session.isValid();
  }

  onAuthSuccess(result) {
    // Handle successful authentication
    window.location.href = '/';
  }

  onAuthFailure(err) {
    // Handle authentication failure
    console.error('Authentication failed:', err);
  }
}

export default new AuthService();