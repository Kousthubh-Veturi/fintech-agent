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
  InputAdornment,
} from '@mui/material';
import {
  Lock,
  Visibility,
  VisibilityOff,
  CheckCircle,
  ArrowBack,
} from '@mui/icons-material';
import axios from 'axios';

interface ResetPasswordFormProps {
  token: string;
  onBackToLogin: () => void;
}

export const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({ 
  token,
  onBackToLogin 
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const validatePassword = (password: string) => {
    const minLength = password.length >= 8;
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    return minLength && hasUppercase && hasLowercase && hasNumber && hasSpecialChar;
  };

  const getPasswordStrength = (password: string) => {
    if (password.length === 0) return '';
    if (password.length < 8) return 'Too short';
    if (!validatePassword(password)) return 'Weak';
    return 'Strong';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!validatePassword(newPassword)) {
      setError('Password must be at least 8 characters with uppercase, lowercase, number, and special character');
      return;
    }

    setLoading(true);

    try {
      await axios.post('http://localhost:8000/auth/reset-password', {
        token,
        new_password: newPassword
      });
      setSuccess(true);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Paper
        elevation={8}
        sx={{
          p: 4,
          maxWidth: 400,
          width: '100%',
          background: 'linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)',
          textAlign: 'center'
        }}
      >
        <CheckCircle sx={{ fontSize: 64, color: '#10b981', mb: 2 }} />
        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1e293b', mb: 2 }}>
          Password Reset Successful
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Your password has been successfully reset. You can now sign in with your new password.
        </Typography>
        <Button
          variant="contained"
          onClick={onBackToLogin}
          startIcon={<ArrowBack />}
          fullWidth
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
            }
          }}
        >
          Sign In
        </Button>
      </Paper>
    );
  }

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
        <Lock sx={{ fontSize: 48, color: '#667eea', mb: 1 }} />
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#1e293b' }}>
          Reset Password
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Enter your new password below
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          type={showPassword ? 'text' : 'password'}
          label="New Password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          sx={{ mb: 2 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Lock color="action" />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <Button
                  onClick={() => setShowPassword(!showPassword)}
                  sx={{ minWidth: 'auto', p: 1 }}
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </Button>
              </InputAdornment>
            ),
          }}
          helperText={
            newPassword ? `Password strength: ${getPasswordStrength(newPassword)}` : 
            'Must contain: 8+ chars, uppercase, lowercase, number, special character'
          }
        />

        <TextField
          fullWidth
          type={showConfirmPassword ? 'text' : 'password'}
          label="Confirm New Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          sx={{ mb: 3 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Lock color="action" />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <Button
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  sx={{ minWidth: 'auto', p: 1 }}
                >
                  {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                </Button>
              </InputAdornment>
            ),
          }}
          error={confirmPassword !== '' && newPassword !== confirmPassword}
          helperText={
            confirmPassword !== '' && newPassword !== confirmPassword 
              ? 'Passwords do not match' 
              : ''
          }
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          disabled={loading || !newPassword || !confirmPassword}
          sx={{
            py: 1.5,
            mb: 2,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
            },
            '&:disabled': {
              background: '#e2e8f0',
              color: '#94a3b8'
            }
          }}
        >
          {loading ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            'Reset Password'
          )}
        </Button>

        <Box sx={{ textAlign: 'center' }}>
          <Link
            component="button"
            type="button"
            variant="body2"
            onClick={onBackToLogin}
            sx={{ color: '#667eea', textDecoration: 'none' }}
          >
            Back to Sign In
          </Link>
        </Box>
      </Box>
    </Paper>
  );
};
