import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  InputAdornment,
} from '@mui/material';
import {
  ArrowBack,
  Delete,
  Lock,
  Email,
  Warning,
} from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from './AuthContext';

interface SettingsPageProps {
  onBack: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onBack }) => {
  const { user, logout } = useAuth();
  const [deleteMethod, setDeleteMethod] = useState<'password' | 'email' | null>(null);
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState(false);

  const handleDeleteWithPassword = async () => {
    setLoading(true);
    setError(null);

    try {
      await axios.post(`${process.env.REACT_APP_API_URL || 'https://fintech-agent-production.up.railway.app'}/auth/delete-account-with-password`, {
        password: password,
      });
      
      setSuccess('Account deleted successfully. You will be logged out.');
      setTimeout(() => {
        logout();
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete account.');
    } finally {
      setLoading(false);
      setConfirmDialog(false);
      setPassword('');
    }
  };

  const handleDeleteWithEmail = async () => {
    setLoading(true);
    setError(null);

    try {
      await axios.post(`${process.env.REACT_APP_API_URL || 'https://fintech-agent-production.up.railway.app'}/auth/request-account-deletion`);
      
      setSuccess('Account deletion confirmation email sent! Check your inbox and click the link to confirm deletion.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send deletion email.');
    } finally {
      setLoading(false);
      setConfirmDialog(false);
    }
  };

  const openConfirmDialog = (method: 'password' | 'email') => {
    setDeleteMethod(method);
    setConfirmDialog(true);
    setError(null);
    setSuccess(null);
  };

  const closeConfirmDialog = () => {
    setConfirmDialog(false);
    setDeleteMethod(null);
    setPassword('');
    setError(null);
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#1e293b' }}>
          Account Settings
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

      {/* Account Info */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
          Account Information
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Typography><strong>Email:</strong> {user?.email}</Typography>
          <Typography><strong>Username:</strong> {user?.username}</Typography>
          <Typography><strong>Full Name:</strong> {user?.full_name || 'Not set'}</Typography>
          <Typography>
            <strong>Email Verified:</strong> 
            <Box component="span" sx={{ 
              color: user?.is_verified ? '#10b981' : '#ef4444',
              fontWeight: 'bold',
              ml: 1
            }}>
              {user?.is_verified ? '✅ Verified' : '❌ Not Verified'}
            </Box>
          </Typography>
          <Typography>
            <strong>2FA Enabled:</strong> 
            <Box component="span" sx={{ 
              color: user?.is_2fa_enabled ? '#10b981' : '#64748b',
              fontWeight: 'bold',
              ml: 1
            }}>
              {user?.is_2fa_enabled ? '🔒 Enabled' : '🔓 Disabled'}
            </Box>
          </Typography>
        </Box>
      </Paper>

      {/* Danger Zone */}
      <Paper 
        elevation={2} 
        sx={{ 
          p: 3, 
          border: '2px solid #fecaca',
          backgroundColor: '#fef2f2'
        }}
      >
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 'bold', 
            mb: 2, 
            color: '#dc2626',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <Warning sx={{ mr: 1 }} />
          Danger Zone
        </Typography>
        
        <Typography variant="body1" sx={{ mb: 3, color: '#7f1d1d' }}>
          Once you delete your account, there is no going back. This will permanently delete your account, 
          portfolio data, and all associated information.
        </Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Card variant="outlined" sx={{ backgroundColor: 'white' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                <Lock sx={{ mr: 1, color: '#dc2626' }} />
                Delete with Password
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Verify your identity with your current password to delete your account immediately.
              </Typography>
              <Button
                variant="outlined"
                color="error"
                onClick={() => openConfirmDialog('password')}
                disabled={loading}
                startIcon={<Delete />}
              >
                Delete Account with Password
              </Button>
            </CardContent>
          </Card>

          <Card variant="outlined" sx={{ backgroundColor: 'white' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                <Email sx={{ mr: 1, color: '#dc2626' }} />
                Delete with Email Verification
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                We'll send a confirmation link to your email address. Click the link to delete your account.
              </Typography>
              <Button
                variant="outlined"
                color="error"
                onClick={() => openConfirmDialog('email')}
                disabled={loading}
                startIcon={<Delete />}
              >
                Delete Account via Email
              </Button>
            </CardContent>
          </Card>
        </Box>
      </Paper>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog} onClose={closeConfirmDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: '#dc2626' }}>
          <Warning sx={{ mr: 1 }} />
          Confirm Account Deletion
        </DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <strong>This action cannot be undone!</strong> All your data will be permanently deleted.
          </Alert>
          
          {deleteMethod === 'password' ? (
            <Box>
              <Typography sx={{ mb: 2 }}>
                Enter your password to confirm account deletion:
              </Typography>
              <TextField
                label="Current Password"
                type="password"
                fullWidth
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
          ) : (
            <Typography>
              We'll send a confirmation email to <strong>{user?.email}</strong>. 
              Click the link in the email to permanently delete your account.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeConfirmDialog} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={deleteMethod === 'password' ? handleDeleteWithPassword : handleDeleteWithEmail}
            color="error"
            variant="contained"
            disabled={loading || (deleteMethod === 'password' && !password)}
            startIcon={loading ? <CircularProgress size={20} /> : <Delete />}
          >
            {loading ? 'Processing...' : 'Delete Account'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
