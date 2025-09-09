import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  CheckCircle,
  Email,
  ArrowBack,
  Refresh,
} from '@mui/icons-material';
import axios from 'axios';

interface EmailVerificationFormProps {
  token?: string;
  onBackToLogin: () => void;
}

export const EmailVerificationForm: React.FC<EmailVerificationFormProps> = ({ token, onBackToLogin }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [email, setEmail] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Auto-verify if token is provided
  useEffect(() => {
    if (token) {
      verifyEmail(token);
    }
  }, [token]);

  const verifyEmail = async (verificationToken: string) => {
    setLoading(true);
    setError(null);

    try {
      await axios.post(`${process.env.REACT_APP_API_URL || 'https://fintech-agent-production.up.railway.app'}/auth/verify-email`, {
        token: verificationToken,
      });
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to verify email.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    setResendLoading(true);
    setError(null);
    setResendSuccess(false);

    try {
      await axios.post(`${process.env.REACT_APP_API_URL || 'https://fintech-agent-production.up.railway.app'}/auth/resend-verification`, {
        email: email,
      });
      setResendSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resend verification email.');
    } finally {
      setResendLoading(false);
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
          Email Verified!
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Your email has been successfully verified. You can now log in to your account.
        </Typography>
        <Button
          variant="contained"
          onClick={onBackToLogin}
          fullWidth
          sx={{
            mt: 2,
            background: 'linear-gradient(45deg, #3b82f6 30%, #2563eb 90%)',
            '&:hover': {
              background: 'linear-gradient(45deg, #2563eb 30%, #1d4ed8 90%)',
            },
          }}
        >
          Go to Login
        </Button>
      </Paper>
    );
  }

  if (loading) {
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
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="h6" sx={{ color: '#1e293b' }}>
          Verifying your email...
        </Typography>
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
      <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1e293b', mb: 3, textAlign: 'center' }}>
        Email Verification
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {resendSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Verification email sent! Please check your inbox.
        </Alert>
      )}

      {token ? (
        <Box textAlign="center">
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            There was an issue verifying your email. Please try again or request a new verification email.
          </Typography>
          <Button
            variant="outlined"
            onClick={() => verifyEmail(token)}
            disabled={loading}
            sx={{ mb: 2, mr: 1 }}
          >
            Retry Verification
          </Button>
        </Box>
      ) : (
        <Box>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Enter your email address to receive a new verification link.
          </Typography>
          <form onSubmit={handleResendVerification}>
            <TextField
              label="Email Address"
              type="email"
              fullWidth
              margin="normal"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email color="action" />
                  </InputAdornment>
                ),
              }}
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              sx={{
                mt: 3,
                py: 1.5,
                background: 'linear-gradient(45deg, #3b82f6 30%, #2563eb 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #2563eb 30%, #1d4ed8 90%)',
                },
              }}
              disabled={resendLoading}
              startIcon={resendLoading ? <CircularProgress size={20} color="inherit" /> : <Refresh />}
            >
              {resendLoading ? 'Sending...' : 'Resend Verification Email'}
            </Button>
          </form>
        </Box>
      )}

      <Button
        variant="text"
        onClick={onBackToLogin}
        fullWidth
        sx={{ mt: 2 }}
        startIcon={<ArrowBack />}
      >
        Back to Login
      </Button>
    </Paper>
  );
};
