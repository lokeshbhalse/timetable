// frontend/src/components/Auth/GoogleLoginButton.tsx
import React from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import authService from '@/services/auth.service';

interface GoogleLoginButtonProps {
  onSuccess: (user: any) => void;
  onError?: () => void;
}

const GoogleLoginButton: React.FC<GoogleLoginButtonProps> = ({ onSuccess, onError }) => {
  const handleSuccess = async (credentialResponse: any) => {
    try {
      // Decode the JWT to get user info
      const response = await fetch('https://www.googleapis.com/oauth2/v3/tokeninfo?id_token=' + credentialResponse.credential);
      const userInfo = await response.json();
      
      const result = await authService.googleLogin({
        email: userInfo.email,
        name: userInfo.name,
        sub: userInfo.sub,
        picture: userInfo.picture
      });
      
      if (result.success) {
        onSuccess(result.user);
      }
    } catch (error) {
      console.error('Google login error:', error);
      if (onError) onError();
    }
  };

  return (
    <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => {
          console.error('Google Login Failed');
          if (onError) onError();
        }}
        useOneTap
      />
    </GoogleOAuthProvider>
  );
};

export default GoogleLoginButton;