import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
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
} from '@mui/material';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

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

function App() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [cryptoPrices, setCryptoPrices] = useState<Record<string, CryptoPrice>>({});
  const [news, setNews] = useState<NewsItem[]>([]);
  const [rebalanceSuggestions, setRebalanceSuggestions] = useState<RebalanceSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tradeQuantity, setTradeQuantity] = useState('0.01');
  const [tradeSide, setTradeSide] = useState<'buy' | 'sell'>('buy');
  const [selectedCrypto, setSelectedCrypto] = useState('BTC');
  
  const supportedCryptos = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'MATIC', 'AVAX'];

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all data in parallel
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
        alert(`Trade executed: ${response.data.message}`);
        fetchData(); // Refresh data
      } else {
        alert(`Trade failed: ${response.data.message}`);
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
        alert(`Rebalance trade executed: ${response.data.message}`);
        fetchData();
      } else {
        alert(`Rebalance trade failed: ${response.data.message}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute rebalance trade');
    } finally {
      setLoading(false);
    }
  };

  const resetPortfolio = async () => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE}/reset`);
      alert('Portfolio reset to $10,000');
      fetchData();
    } catch (err: any) {
      setError(err.message || 'Failed to reset portfolio');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'success';
      case 'negative': return 'error';
      default: return 'default';
    }
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? 'success.main' : 'error.main';
  };

  return (
    <Box sx={{ flexGrow: 1, bgcolor: '#f5f5f5', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ bgcolor: '#1976d2' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🚀 Enhanced Multi-Crypto Advisory System v2.0
          </Typography>
          <Chip label="MULTI-CRYPTO MODE" color="warning" />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, pb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Crypto Prices Grid */}
        <Paper sx={{ p: 2, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            💰 Live Cryptocurrency Prices
          </Typography>
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: 2 
          }}>
            {Object.entries(cryptoPrices).map(([symbol, data]) => (
              <Card variant="outlined" key={symbol}>
                <CardContent>
                  <Typography variant="h6" color="primary">
                    {symbol}
                  </Typography>
                  <Typography variant="h5">
                    ${data.price.toLocaleString()}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ color: getChangeColor(data.change_24h) }}
                  >
                    {data.change_24h >= 0 ? '+' : ''}{data.change_24h.toFixed(2)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {data.name}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        </Paper>

        {/* Portfolio Overview */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mb: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💼 Portfolio Value
              </Typography>
              {portfolio ? (
                <>
                  <Typography variant="h4" color="primary">
                    ${portfolio.total_value.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color={portfolio.total_pnl >= 0 ? 'success.main' : 'error.main'}>
                    P&L: ${portfolio.total_pnl.toFixed(2)} ({portfolio.total_pnl_pct.toFixed(2)}%)
                  </Typography>
                </>
              ) : (
                <CircularProgress size={24} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💵 Available Cash
              </Typography>
              {portfolio ? (
                <Typography variant="h4" color="primary">
                  ${portfolio.cash.toLocaleString()}
                </Typography>
              ) : (
                <CircularProgress size={24} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Diversification
              </Typography>
              {portfolio ? (
                <>
                  <Typography variant="h4" color="primary">
                    {portfolio.diversification_score.toFixed(1)}/100
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {portfolio.position_count} positions
                  </Typography>
                </>
              ) : (
                <CircularProgress size={24} />
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Current Positions */}
        {portfolio && portfolio.positions.length > 0 && (
          <Paper sx={{ p: 2, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              📈 Current Positions
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Avg Price</TableCell>
                    <TableCell align="right">Current Price</TableCell>
                    <TableCell align="right">Market Value</TableCell>
                    <TableCell align="right">P&L</TableCell>
                    <TableCell align="right">P&L %</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {portfolio.positions.map((position, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Chip label={position.symbol} variant="outlined" />
                      </TableCell>
                      <TableCell align="right">{position.quantity.toFixed(6)}</TableCell>
                      <TableCell align="right">${position.avg_price.toLocaleString()}</TableCell>
                      <TableCell align="right">${position.current_price.toLocaleString()}</TableCell>
                      <TableCell align="right">${position.market_value.toLocaleString()}</TableCell>
                      <TableCell 
                        align="right" 
                        sx={{ color: position.pnl >= 0 ? 'success.main' : 'error.main' }}
                      >
                        ${position.pnl.toFixed(2)}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: position.pnl_pct >= 0 ? 'success.main' : 'error.main' }}
                      >
                        {position.pnl_pct.toFixed(2)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        )}

        {/* Trading and Rebalancing */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 3, mb: 4 }}>
          {/* Manual Trading */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              ⚡ Manual Trading
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControl size="small">
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
                size="small"
              />
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant={tradeSide === 'buy' ? 'contained' : 'outlined'}
                  color="success"
                  onClick={() => setTradeSide('buy')}
                  size="small"
                >
                  BUY
                </Button>
                <Button
                  variant={tradeSide === 'sell' ? 'contained' : 'outlined'}
                  color="error"
                  onClick={() => setTradeSide('sell')}
                  size="small"
                >
                  SELL
                </Button>
              </Box>
              <Button
                variant="contained"
                onClick={executeTrade}
                disabled={loading}
                fullWidth
              >
                Execute Trade
              </Button>
            </Box>
          </Paper>

          {/* Rebalancing Suggestions */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              🔄 Rebalancing Suggestions
            </Typography>
            {rebalanceSuggestions.length > 0 ? (
              <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                {rebalanceSuggestions.slice(0, 5).map((suggestion, index) => (
                  <Box key={index} sx={{ mb: 2, p: 1, border: '1px solid #ddd', borderRadius: 1 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <Chip 
                        label={suggestion.action.toUpperCase()} 
                        color={suggestion.action === 'buy' ? 'success' : 'error'}
                        size="small"
                      /> {suggestion.quantity.toFixed(4)} {suggestion.symbol}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {suggestion.reason}
                    </Typography>
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
                Portfolio is well balanced
              </Typography>
            )}
          </Paper>
        </Box>

        {/* System Controls */}
        <Paper sx={{ p: 2, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            🔧 System Controls
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              onClick={fetchData}
              disabled={loading}
            >
              Refresh Data
            </Button>
            <Button
              variant="outlined"
              color="warning"
              onClick={resetPortfolio}
              disabled={loading}
            >
              Reset Portfolio
            </Button>
          </Box>
        </Paper>

        {/* Multi-Crypto News */}
        {news.length > 0 && (
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              📰 Multi-Crypto News Feed
            </Typography>
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
              gap: 2 
            }}>
              {news.map((article, index) => (
                <Card variant="outlined" key={index}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', flex: 1 }}>
                        {article.title}
                      </Typography>
                      <Chip 
                        label={article.sentiment} 
                        size="small" 
                        color={getSentimentColor(article.sentiment) as any}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {article.description}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                      {article.relevant_cryptos.map((crypto, i) => (
                        <Chip key={i} label={crypto} size="small" variant="outlined" />
                      ))}
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {article.source} • {new Date(article.published_at).toLocaleDateString()}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Paper>
        )}

        {loading && (
          <Box display="flex" justifyContent="center" mt={2}>
            <CircularProgress />
          </Box>
        )}
      </Container>
    </Box>
  );
}

export default App;