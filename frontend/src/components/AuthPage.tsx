import React, { useState } from 'react';
import { Box, Container, Typography } from '@mui/material';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { ForgotPasswordForm } from './ForgotPasswordForm';

type AuthView = 'login' | 'register' | 'forgot-password';

export const AuthPage: React.FC = () => {
  const [currentView, setCurrentView] = useState<AuthView>('login');

  const renderCurrentView = () => {
    switch (currentView) {
      case 'register':
        return <RegisterForm onSwitchToLogin={() => setCurrentView('login')} />;
      case 'forgot-password':
        return <ForgotPasswordForm onSwitchToLogin={() => setCurrentView('login')} />;
      default:
        return (
          <LoginForm
            onSwitchToRegister={() => setCurrentView('register')}
            onSwitchToForgotPassword={() => setCurrentView('forgot-password')}
          />
        );
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #06b6d4 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '80vh',
            gap: 4
          }}
        >
          {/* Logo and Brand */}
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Box
              component="img"
              src="/logo.png"
              alt="Fintech Agent Logo"
              sx={{
                width: 80,
                height: 80,
                borderRadius: '16px',
                mb: 2,
                boxShadow: '0 8px 32px rgba(6, 182, 212, 0.3)',
                animation: 'logoFloat 3s ease-in-out infinite',
                '@keyframes logoFloat': {
                  '0%, 100%': {
                    transform: 'translateY(0px)',
                  },
                  '50%': {
                    transform: 'translateY(-10px)',
                  },
                },
              }}
            />
            <Typography
              variant="h4"
              sx={{
                fontWeight: 'bold',
                color: 'white',
                mb: 1,
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              }}
            >
              Fintech Agent
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: '#06b6d4',
                fontWeight: 500,
                textShadow: '0 1px 2px rgba(0,0,0,0.2)',
              }}
            >
              Professional Trading Platform
            </Typography>
          </Box>
          
          {renderCurrentView()}
        </Box>
      </Container>
    </Box>
  );
};
