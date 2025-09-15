import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  AppBar,
  Toolbar,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Drawer,
  List,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
  Menu,
  ListItemButton,
  Container,
  Skeleton,
} from '@mui/material';
import {
  Dashboard,
  TrendingUp,
  AccountBalance,
  Assessment,
  Settings,
  Refresh,
  Add,
  Remove,
  ArrowUpward,
  ArrowDownward,
  Logout,
} from '@mui/icons-material';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './components/AuthContext';
import { AuthPage } from './components/AuthPage';
import { ResetPasswordForm } from './components/ResetPasswordForm';
import { EmailVerificationForm } from './components/EmailVerificationForm';
import { SettingsPage } from './components/SettingsPage';
import { DeleteAccountForm } from './components/DeleteAccountForm';

const API_BASE = process.env.REACT_APP_API_URL || 'https://fintech-agent-production.up.railway.app';

interface CryptoPrice {
  symbol: string;
  name: string;
  price: number;
  change_24h: number;
  market_cap: number;
  volume_24h: number;
  source: string;
}

interface Position {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  pnl: number;
  pnl_pct: number;
}

interface Portfolio {
  cash: number;
  total_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  position_count: number;
  largest_position: string;
  diversification_score: number;
  positions: Position[];
}

interface NewsItem {
  title: string;
  description: string;
  url: string;
  published_at: string;
  source: string;
  sentiment: string;
  relevant_cryptos: string[];
}

interface RebalanceSuggestion {
  action: string;
  symbol: string;
  quantity: number;
  value: number;
  reason: string;
}

type ViewType = 'dashboard' | 'portfolio' | 'trading' | 'news' | 'analytics' | 'settings';

function TradingApp() {
  const { user, logout, isAuthenticated } = useAuth();
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [cryptoPrices, setCryptoPrices] = useState<Record<string, CryptoPrice>>({});
  const [news, setNews] = useState<NewsItem[]>([]);
  const [rebalanceSuggestions, setRebalanceSuggestions] = useState<RebalanceSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tradeQuantity, setTradeQuantity] = useState('0.01');
  const [tradeSide, setTradeSide] = useState<'buy' | 'sell'>('buy');
  const [selectedCrypto, setSelectedCrypto] = useState('BTC');
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  
  const supportedCryptos = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'MATIC', 'AVAX'];

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [portfolioRes, pricesRes, newsRes, rebalanceRes] = await Promise.all([
        axios.get(`${API_BASE}/portfolio`),
        axios.get(`${API_BASE}/crypto/prices`),
        axios.get(`${API_BASE}/crypto/news?limit=8`),
        axios.get(`${API_BASE}/portfolio/rebalance`)
      ]);

      setPortfolio(portfolioRes.data);
      setCryptoPrices(pricesRes.data.prices || {});
      setNews(newsRes.data.news || []);
      setRebalanceSuggestions(rebalanceRes.data.suggestions || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const executeTrade = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/trade`, null, {
        params: {
          symbol: selectedCrypto,
          side: tradeSide,
          quantity: parseFloat(tradeQuantity)
        }
      });
      
      if (response.data.success) {
        fetchData();
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute trade');
    } finally {
      setLoading(false);
    }
  };

  const executeRebalanceTrade = async (suggestion: RebalanceSuggestion) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/trade`, null, {
        params: {
          symbol: suggestion.symbol,
          side: suggestion.action,
          quantity: suggestion.quantity
        }
      });
      
      if (response.data.success) {
        fetchData();
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute rebalance trade');
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const resetPortfolio = async () => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE}/reset`);
      fetchData();
    } catch (err: any) {
      setError(err.message || 'Failed to reset portfolio');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#4caf50';
      case 'negative': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? '#4caf50' : '#f44336';
  };

  const menuItems: Array<{text: string, icon: React.ReactNode, view: ViewType}> = [
    { text: 'Dashboard', icon: <Dashboard />, view: 'dashboard' },
    { text: 'Trading', icon: <TrendingUp />, view: 'trading' },
    { text: 'Portfolio', icon: <AccountBalance />, view: 'portfolio' },
    { text: 'Analytics', icon: <Assessment />, view: 'analytics' },
    { text: 'Settings', icon: <Settings />, view: 'settings' },
  ];

  const renderDashboard = () => (
    <Box sx={{ p: 3, bgcolor: '#0f172a', minHeight: '100vh' }}>
      {/* Key Metrics Cards */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
        gap: 3, 
        mb: 4 
      }}>
        <Card sx={{ 
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f1419 100%)', 
          color: 'white', 
          border: '1px solid #06b6d4',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 20px 40px rgba(6, 182, 212, 0.15)',
            border: '1px solid #0891b2',
          }
        }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ opacity: 0.9 }}>
              Total Portfolio Value
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1, color: '#06b6d4' }}>
              {loading && !portfolio ? (
                <Skeleton 
                  variant="text" 
                  width="60%" 
                  height={48}
                  sx={{ bgcolor: 'rgba(6, 182, 212, 0.1)' }}
                />
              ) : (
                `$${portfolio?.total_value.toLocaleString() || '0'}`
              )}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {portfolio && portfolio.total_pnl >= 0 ? <ArrowUpward fontSize="small" sx={{ color: '#10b981' }} /> : <ArrowDownward fontSize="small" sx={{ color: '#ef4444' }} />}
              <Typography variant="body2" sx={{ color: portfolio && portfolio.total_pnl >= 0 ? '#10b981' : '#ef4444' }}>
                {portfolio ? `${portfolio.total_pnl >= 0 ? '+' : ''}$${portfolio.total_pnl.toFixed(2)} (${portfolio.total_pnl_pct.toFixed(2)}%)` : '$0.00 (0.00%)'}
              </Typography>
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ 
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f1419 100%)', 
          color: 'white', 
          border: '1px solid #0891b2',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 20px 40px rgba(8, 145, 178, 0.15)',
            border: '1px solid #06b6d4',
          }
        }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ opacity: 0.9 }}>
              Available Cash
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1, color: '#0891b2' }}>
              {portfolio ? `$${portfolio.cash.toLocaleString()}` : '$0'}
            </Typography>
            <Typography variant="body2">
              Ready for investment
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ 
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f1419 100%)', 
          color: 'white', 
          border: '1px solid #0284c7',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 20px 40px rgba(2, 132, 199, 0.15)',
            border: '1px solid #0891b2',
          }
        }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ opacity: 0.9 }}>
              Diversification Score
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1, color: '#0284c7' }}>
              {portfolio ? `${portfolio.diversification_score.toFixed(0)}/100` : '0/100'}
            </Typography>
            <Typography variant="body2">
              {portfolio ? `${portfolio.position_count} active positions` : 'No positions'}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ 
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f1419 100%)', 
          color: 'white', 
          border: '1px solid #06b6d4',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 20px 40px rgba(6, 182, 212, 0.15)',
            border: '1px solid #0891b2',
          }
        }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ opacity: 0.9 }}>
              Market Status
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1, color: '#06b6d4' }}>
              LIVE
            </Typography>
            <Typography variant="body2">
              {Object.keys(cryptoPrices).length} assets tracked
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Market Overview */}
      <Card sx={{ mb: 4, bgcolor: '#1e293b', border: '1px solid #374151' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#06b6d4' }}>
              Market Overview
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={fetchData}
              disabled={loading}
              variant="outlined"
              size="small"
              sx={{
                borderColor: '#06b6d4',
                color: '#06b6d4',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  borderColor: '#0891b2',
                  backgroundColor: 'rgba(6, 182, 212, 0.1)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 25px rgba(6, 182, 212, 0.25)',
                }
              }}
            >
              Refresh
            </Button>
          </Box>
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: 2 
          }}>
            {loading && Object.keys(cryptoPrices).length === 0 ? (
              // Skeleton loading state
              Array.from({ length: 8 }).map((_, index) => (
                <Card key={`skeleton-${index}`} variant="outlined" sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Skeleton variant="text" width="40%" height={24} />
                    <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 1 }} />
                  </Box>
                  <Skeleton variant="text" width="70%" height={32} sx={{ mb: 0.5 }} />
                  <Skeleton variant="text" width="50%" height={20} />
                </Card>
              ))
            ) : (
              Object.entries(cryptoPrices).map(([symbol, data]) => (
              <Card key={symbol} variant="outlined" sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {symbol}
                  </Typography>
                  <Chip 
                    label={`${data.change_24h >= 0 ? '+' : ''}${data.change_24h.toFixed(2)}%`}
                    size="small"
                    sx={{ 
                      backgroundColor: getChangeColor(data.change_24h),
                      color: 'white',
                      fontWeight: 'bold'
                    }}
                  />
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                  ${data.price.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {data.name}
                </Typography>
              </Card>
              ))
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Recent News */}
      {news.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
              Market News
            </Typography>
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
              gap: 2 
            }}>
              {news.slice(0, 4).map((article, index) => (
                <Card key={index} variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold', flex: 1 }}>
                        {article.title}
                      </Typography>
                      <Box sx={{ 
                        width: 8, 
                        height: 8, 
                        borderRadius: '50%', 
                        backgroundColor: getSentimentColor(article.sentiment),
                        ml: 1,
                        mt: 0.5
                      }} />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {article.description}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {article.relevant_cryptos.slice(0, 3).map((crypto, i) => (
                          <Chip key={i} label={crypto} size="small" variant="outlined" />
                        ))}
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {article.source}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderTrading = () => (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
        Trading Center
      </Typography>
      
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
        {/* Manual Trading */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
              Execute Trade
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <FormControl fullWidth sx={{
                '& .MuiOutlinedInput-root': {
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover fieldset': {
                    borderColor: '#06b6d4',
                    boxShadow: '0 0 0 1px rgba(6, 182, 212, 0.1)',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#06b6d4',
                    borderWidth: '2px',
                    boxShadow: '0 0 0 3px rgba(6, 182, 212, 0.1)',
                  },
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#06b6d4',
                },
              }}>
                <InputLabel>Cryptocurrency</InputLabel>
                <Select
                  value={selectedCrypto}
                  onChange={(e) => setSelectedCrypto(e.target.value)}
                  label="Cryptocurrency"
                >
                  {supportedCryptos.map(crypto => (
                    <MenuItem key={crypto} value={crypto}>{crypto}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <TextField
                label="Quantity"
                value={tradeQuantity}
                onChange={(e) => setTradeQuantity(e.target.value)}
                type="number"
                fullWidth
                sx={{
                  '& .MuiOutlinedInput-root': {
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover fieldset': {
                      borderColor: '#06b6d4',
                      boxShadow: '0 0 0 1px rgba(6, 182, 212, 0.1)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#06b6d4',
                      borderWidth: '2px',
                      boxShadow: '0 0 0 3px rgba(6, 182, 212, 0.1)',
                    },
                  },
                  '& .MuiInputLabel-root.Mui-focused': {
                    color: '#06b6d4',
                  },
                }}
              />
              
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Button
                  variant={tradeSide === 'buy' ? 'contained' : 'outlined'}
                  color="success"
                  onClick={() => setTradeSide('buy')}
                  startIcon={<Add />}
                  fullWidth
                  sx={{
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: tradeSide === 'buy' ? '0 8px 25px rgba(16, 185, 129, 0.4)' : '0 8px 25px rgba(16, 185, 129, 0.2)',
                    }
                  }}
                >
                  BUY
                </Button>
                <Button
                  variant={tradeSide === 'sell' ? 'contained' : 'outlined'}
                  color="error"
                  onClick={() => setTradeSide('sell')}
                  startIcon={<Remove />}
                  fullWidth
                  sx={{
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: tradeSide === 'sell' ? '0 8px 25px rgba(239, 68, 68, 0.4)' : '0 8px 25px rgba(239, 68, 68, 0.2)',
                    }
                  }}
                >
                  SELL
                </Button>
              </Box>
              
              <Button
                variant="contained"
                onClick={executeTrade}
                disabled={loading}
                size="large"
                fullWidth
                sx={{
                  background: 'linear-gradient(45deg, #06b6d4 30%, #0891b2 90%)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #0891b2 30%, #0284c7 90%)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 12px 30px rgba(6, 182, 212, 0.4)',
                  },
                  '&:disabled': {
                    background: 'rgba(148, 163, 184, 0.3)',
                  }
                }}
              >
                {loading ? <CircularProgress size={24} /> : 'Execute Trade'}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Rebalancing */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
              Smart Rebalancing
            </Typography>
            {rebalanceSuggestions.length > 0 ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {rebalanceSuggestions.slice(0, 5).map((suggestion, index) => (
                  <Box key={index} sx={{ 
                    p: 2, 
                    border: '1px solid #e0e0e0', 
                    borderRadius: 1,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        {suggestion.action.toUpperCase()} {suggestion.quantity.toFixed(4)} {suggestion.symbol}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {suggestion.reason}
                      </Typography>
                    </Box>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => executeRebalanceTrade(suggestion)}
                      disabled={loading}
                    >
                      Execute
                    </Button>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Portfolio is optimally balanced
              </Typography>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );

  const renderPortfolio = () => (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
        Portfolio Management
      </Typography>
      
      {portfolio && portfolio.positions.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
              Current Positions
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Asset</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Quantity</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Avg Price</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Current Price</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Market Value</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>P&L</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>P&L %</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {portfolio.positions.map((position, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Chip label={position.symbol} variant="filled" />
                      </TableCell>
                      <TableCell align="right">{position.quantity.toFixed(6)}</TableCell>
                      <TableCell align="right">${position.avg_price.toLocaleString()}</TableCell>
                      <TableCell align="right">${position.current_price.toLocaleString()}</TableCell>
                      <TableCell align="right">${position.market_value.toLocaleString()}</TableCell>
                      <TableCell 
                        align="right" 
                        sx={{ color: position.pnl >= 0 ? '#4caf50' : '#f44336', fontWeight: 'bold' }}
                      >
                        ${position.pnl.toFixed(2)}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: position.pnl_pct >= 0 ? '#4caf50' : '#f44336', fontWeight: 'bold' }}
                      >
                        {position.pnl_pct.toFixed(2)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'trading': return renderTrading();
      case 'portfolio': return renderPortfolio();
      case 'analytics': return <Box sx={{ p: 3 }}><Typography>Analytics coming soon...</Typography></Box>;
      case 'settings': return (
        <SettingsPage onBack={() => setCurrentView('dashboard')} />
      );
      default: return renderDashboard();
    }
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: '#0f172a' }}>
      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: 260,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 260,
            boxSizing: 'border-box',
            background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f1419 100%)',
            color: 'white',
            borderRight: '1px solid rgba(6, 182, 212, 0.1)'
          },
        }}
      >
        <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            component="img"
            src="/logo.png"
            alt="Fintech Agent Logo"
            sx={{
              width: 40,
              height: 40,
              borderRadius: '8px',
            }}
          />
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'white' }}>
              Fintech Agent
            </Typography>
            <Typography variant="body2" sx={{ color: '#94a3b8' }}>
              Professional Platform
            </Typography>
          </Box>
        </Box>
        <Divider sx={{ bgcolor: '#06b6d4' }} />
        <List sx={{ px: 2, py: 1 }}>
          {menuItems.map((item) => (
            <ListItemButton
              key={item.view}
              onClick={() => setCurrentView(item.view)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                position: 'relative',
                overflow: 'hidden',
                bgcolor: currentView === item.view ? '#06b6d4' : 'transparent',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                transform: currentView === item.view ? 'translateX(8px)' : 'translateX(0)',
                '&:hover': {
                  bgcolor: currentView === item.view ? '#06b6d4' : '#1e293b',
                  transform: 'translateX(8px)',
                },
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: currentView === item.view ? '4px' : '0px',
                  backgroundColor: '#0891b2',
                  transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                },
              }}
            >
              <ListItemIcon sx={{ 
                color: 'inherit', 
                minWidth: 36,
                transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                transform: currentView === item.view ? 'scale(1.1)' : 'scale(1)',
              }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top Bar */}
        <AppBar 
          position="static" 
          elevation={0}
          sx={{ 
            background: 'linear-gradient(90deg, #0f172a 0%, #1e293b 50%, #334155 100%)', 
            borderBottom: '1px solid #06b6d4',
            color: 'white'
          }}
        >
          <Toolbar>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
              <Box
                component="img"
                src="/logo.png"
                alt="Logo"
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '6px',
                }}
              />
              <Typography variant="h6" sx={{ fontWeight: 'bold', textTransform: 'capitalize', color: '#06b6d4' }}>
                {currentView}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip 
                label="LIVE" 
                color="success" 
                size="small"
                sx={{ fontWeight: 'bold' }}
              />
              <IconButton
                onClick={(e) => setUserMenuAnchor(e.currentTarget)}
                sx={{ p: 0 }}
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: '#06b6d4' }}>
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </Avatar>
              </IconButton>
              <Menu
                anchorEl={userMenuAnchor}
                open={Boolean(userMenuAnchor)}
                onClose={() => setUserMenuAnchor(null)}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              >
                <Box sx={{ px: 2, py: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                    {user?.full_name || user?.username}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user?.email}
                  </Typography>
                </Box>
                <Divider />
                <ListItemButton onClick={() => { setCurrentView('settings'); setUserMenuAnchor(null); }}>
                  <ListItemIcon>
                    <Settings fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Settings" />
                </ListItemButton>
                <ListItemButton onClick={logout}>
                  <ListItemIcon>
                    <Logout fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Sign Out" />
                </ListItemButton>
              </Menu>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Content Area */}
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          {error && (
            <Alert 
              severity="error" 
              sx={{ m: 3, mb: 0 }} 
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          )}
          {renderCurrentView()}
        </Box>
      </Box>
    </Box>
  );
}

// Reset Password Page Component
const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  if (!token) {
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
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: '80vh',
            }}
          >
            <Alert severity="error">
              Invalid reset link. Please request a new password reset.
            </Alert>
          </Box>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #374151 100%)',
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
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '80vh',
          }}
        >
          <ResetPasswordForm 
            token={token} 
            onBackToLogin={() => navigate('/')} 
          />
        </Box>
      </Container>
    </Box>
  );
};

// Email Verification Page Component
const EmailVerificationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #374151 100%)',
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
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '80vh',
          }}
        >
          <EmailVerificationForm 
            token={token || undefined} 
            onBackToLogin={() => navigate('/')} 
          />
        </Box>
      </Container>
    </Box>
  );
};

// Delete Account Confirmation Page Component
const DeleteAccountPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  if (!token) {
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
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: '80vh',
            }}
          >
            <Alert severity="error">
              Invalid deletion link. Please request a new account deletion from settings.
            </Alert>
          </Box>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #374151 100%)',
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
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '80vh',
          }}
        >
          <DeleteAccountForm 
            token={token} 
            onBackToLogin={() => navigate('/')} 
          />
        </Box>
      </Container>
    </Box>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/verify-email" element={<EmailVerificationPage />} />
          <Route path="/delete-account" element={<DeleteAccountPage />} />
          <Route path="/*" element={<TradingApp />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;