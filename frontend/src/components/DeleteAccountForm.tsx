import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Warning,
  CheckCircle,
  Delete,
  ArrowBack,
} from '@mui/icons-material';
import axios from 'axios';

interface DeleteAccountFormProps {
  token: string;
  onBackToLogin: () => void;
}

export const DeleteAccountForm: React.FC<DeleteAccountFormProps> = ({ token, onBackToLogin }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [confirmed, setConfirmed] = useState(false);

  const handleDeleteAccount = async () => {
    setLoading(true);
    setError(null);

    try {
      await axios.post(`${process.env.REACT_APP_API_URL || 'https://fintech-agent-production.up.railway.app'}/auth/delete-account-with-token`, {
        token: token,
      });
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete account.');
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
          Account Deleted
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Your account has been permanently deleted. All your data has been removed from our systems.
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Thank you for using Fintech Agent. We're sorry to see you go!
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
          Deleting your account...
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper
      elevation={8}
      sx={{
        p: 4,
        maxWidth: 500,
        width: '100%',
        background: 'linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)',
        border: '2px solid #fecaca',
      }}
    >
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Warning sx={{ fontSize: 64, color: '#dc2626', mb: 2 }} />
        <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#dc2626', mb: 1 }}>
          Confirm Account Deletion
        </Typography>
        <Typography variant="body1" color="text.secondary">
          This action cannot be undone
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Alert severity="error" sx={{ mb: 3 }}>
        <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
          You are about to permanently delete your account!
        </Typography>
        <Typography variant="body2">
          • All your portfolio data will be lost<br/>
          • All your trading history will be deleted<br/>
          • Your account settings will be removed<br/>
          • This action cannot be reversed
        </Typography>
      </Alert>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Button
          variant="contained"
          color="error"
          onClick={handleDeleteAccount}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <Delete />}
          fullWidth
          sx={{
            py: 1.5,
            fontWeight: 'bold',
            backgroundColor: '#dc2626',
            '&:hover': {
              backgroundColor: '#b91c1c',
            },
          }}
        >
          {loading ? 'Deleting Account...' : 'Yes, Delete My Account Permanently'}
        </Button>

        <Button
          variant="outlined"
          onClick={onBackToLogin}
          disabled={loading}
          startIcon={<ArrowBack />}
          fullWidth
          sx={{
            py: 1.5,
            color: '#64748b',
            borderColor: '#d1d5db',
            '&:hover': {
              borderColor: '#9ca3af',
            },
          }}
        >
          Cancel - Keep My Account
        </Button>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
        This deletion link expires in 1 hour for security reasons.
      </Typography>
    </Paper>
  );
};
