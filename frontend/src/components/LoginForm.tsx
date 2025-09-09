import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Link,
  Divider,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email,
  Lock,
  Security,
} from '@mui/icons-material';
import { useAuth } from './AuthContext';

interface LoginFormProps {
  onSwitchToRegister: () => void;
  onSwitchToForgotPassword: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ 
  onSwitchToRegister, 
  onSwitchToForgotPassword 
}) => {
  const { login, loading, error, clearError } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    totpCode: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [needs2FA, setNeeds2FA] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await login(formData.email, formData.password, formData.totpCode || undefined);
    } catch (error: any) {
      if (error.message.includes('2FA code required')) {
        setNeeds2FA(true);
      }
    }
  };

  const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  return (
    <Paper
      elevation={8}
      sx={{
        p: 4,
        maxWidth: 400,
        width: '100%',
        background: 'linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)',
      }}
    >
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#1e293b', mb: 1 }}>
          Welcome Back
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Sign in to your account
        </Typography>
      </Box>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={clearError}
          action={
            error.includes('verify your email') ? (
              <Button 
                color="inherit" 
                size="small"
                onClick={() => window.open('/verify-email', '_blank')}
              >
                Verify Email
              </Button>
            ) : null
          }
        >
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            label="Email"
            type="email"
            value={formData.email}
            onChange={handleInputChange('email')}
            required
            fullWidth
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Email color="action" />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={formData.password}
            onChange={handleInputChange('password')}
            required
            fullWidth
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Lock color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {needs2FA && (
            <TextField
              label="2FA Code"
              value={formData.totpCode}
              onChange={handleInputChange('totpCode')}
              placeholder="Enter 6-digit code"
              fullWidth
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Security color="action" />
                  </InputAdornment>
                ),
              }}
            />
          )}

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading}
            fullWidth
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              py: 1.5,
              fontWeight: 'bold',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
              },
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
          </Button>
        </Box>
      </form>

      <Box sx={{ textAlign: 'center', mt: 3 }}>
        <Link
          component="button"
          variant="body2"
          onClick={onSwitchToForgotPassword}
          sx={{ color: '#3b82f6', textDecoration: 'none' }}
        >
          Forgot your password?
        </Link>
      </Box>

      <Divider sx={{ my: 3 }}>
        <Typography variant="body2" color="text.secondary">
          or
        </Typography>
      </Divider>

      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Don't have an account?{' '}
          <Link
            component="button"
            variant="body2"
            onClick={onSwitchToRegister}
            sx={{ color: '#3b82f6', fontWeight: 'bold', textDecoration: 'none' }}
          >
            Create Account
          </Link>
        </Typography>
      </Box>
    </Paper>
  );
};
