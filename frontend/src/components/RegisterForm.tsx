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
  LinearProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email,
  Lock,
  Person,
  AccountCircle,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';
import { useAuth } from './AuthContext';

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { register, loading, error, clearError } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);

  const getPasswordStrength = (password: string) => {
    let score = 0;
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      numbers: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    Object.values(checks).forEach(check => check && score++);
    return { score, checks };
  };

  const passwordStrength = getPasswordStrength(formData.password);
  const passwordsMatch = formData.password === formData.confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!passwordsMatch) {
      return;
    }

    if (passwordStrength.score < 5) {
      return;
    }

    try {
      await register(
        formData.email,
        formData.username,
        formData.password,
        formData.fullName || undefined
      );
      setRegistrationSuccess(true);
    } catch (error) {
      // Error is handled by context
    }
  };

  const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  if (registrationSuccess) {
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
          Account Created!
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          We've sent a verification email to <strong>{formData.email}</strong>. 
          Please check your inbox and click the verification link to activate your account.
        </Typography>
        <Button
          variant="outlined"
          onClick={onSwitchToLogin}
          fullWidth
        >
          Back to Sign In
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
        animation: 'slideInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
        '@keyframes slideInUp': {
          '0%': {
            transform: 'translateY(30px)',
            opacity: 0,
          },
          '100%': {
            transform: 'translateY(0)',
            opacity: 1,
          },
        },
      }}
    >
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#1e293b', mb: 1 }}>
          Create Account
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Join the trading platform
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={clearError}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            label="Full Name (Optional)"
            value={formData.fullName}
            onChange={handleInputChange('fullName')}
            fullWidth
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Person color="action" />
                </InputAdornment>
              ),
            }}
          />

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
            label="Username"
            value={formData.username}
            onChange={handleInputChange('username')}
            required
            fullWidth
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <AccountCircle color="action" />
                </InputAdornment>
              ),
            }}
          />

          <Box>
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
            
            {formData.password && (
              <Box sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Password Strength
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(passwordStrength.score / 5) * 100}
                    sx={{ 
                      ml: 1, 
                      flex: 1,
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: passwordStrength.score < 3 ? '#f44336' : 
                                       passwordStrength.score < 5 ? '#ff9800' : '#4caf50'
                      }
                    }}
                  />
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {Object.entries(passwordStrength.checks).map(([key, passed]) => (
                    <Box key={key} sx={{ display: 'flex', alignItems: 'center', mr: 1 }}>
                      {passed ? (
                        <CheckCircle sx={{ fontSize: 14, color: '#4caf50', mr: 0.5 }} />
                      ) : (
                        <Cancel sx={{ fontSize: 14, color: '#f44336', mr: 0.5 }} />
                      )}
                      <Typography variant="caption" color={passed ? '#4caf50' : '#f44336'}>
                        {key === 'length' ? '8+ chars' : 
                         key === 'uppercase' ? 'A-Z' :
                         key === 'lowercase' ? 'a-z' :
                         key === 'numbers' ? '0-9' : 'Special'}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
          </Box>

          <TextField
            label="Confirm Password"
            type={showConfirmPassword ? 'text' : 'password'}
            value={formData.confirmPassword}
            onChange={handleInputChange('confirmPassword')}
            required
            fullWidth
            error={formData.confirmPassword.length > 0 && !passwordsMatch}
            helperText={
              formData.confirmPassword.length > 0 && !passwordsMatch 
                ? "Passwords don't match" 
                : ""
            }
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Lock color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    edge="end"
                  >
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading || passwordStrength.score < 5 || !passwordsMatch}
            fullWidth
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              py: 1.5,
              fontWeight: 'bold',
              '&:hover': {
                background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
              },
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Create Account'}
          </Button>
        </Box>
      </form>

      <Divider sx={{ my: 3 }}>
        <Typography variant="body2" color="text.secondary">
          or
        </Typography>
      </Divider>

      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Already have an account?{' '}
          <Link
            component="button"
            variant="body2"
            onClick={onSwitchToLogin}
            sx={{ color: '#3b82f6', fontWeight: 'bold', textDecoration: 'none' }}
          >
            Sign In
          </Link>
        </Typography>
      </Box>
    </Paper>
  );
};
