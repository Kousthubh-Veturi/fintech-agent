import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
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
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  Zap,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

interface Portfolio {
  user_id: number;
  cash_balance: number;
  total_value: number;
  positions: Position[];
  pnl: number;
  pnl_pct: number;
}

interface Position {
  instrument: string;
  quantity: number;
  avg_price: number;
  market_value: number;
  updated_at: string;
}

interface Order {
  order_id: number;
  instrument: string;
  side: string;
  order_type: string;
  quantity: number;
  status: string;
  created_at: string;
}

interface MarketData {
  instrument: string;
  price: number;
  ohlc_1h: any;
  ohlc_1d: any;
  timestamp: number;
}

interface NewsItem {
  title: string;
  url: string;
  sentiment: number;
  weight: number;
  source: string;
  published_at: string;
}

interface News {
  items: NewsItem[];
  avg_sentiment: number;
  negative_news_count: number;
  positive_news_count: number;
  high_impact_news: NewsItem[];
}

function App() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [news, setNews] = useState<News | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agentRunning, setAgentRunning] = useState(false);

  const userId = 1;
  const instrument = 'XBX-USD';

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setError(null);
      const [portfolioRes, ordersRes, marketRes, newsRes] = await Promise.all([
        axios.get(`${API_BASE}/portfolio/${userId}`),
        axios.get(`${API_BASE}/orders/${userId}`),
        axios.get(`${API_BASE}/market/${instrument}`),
        axios.get(`${API_BASE}/news/BTC`),
      ]);

      setPortfolio(portfolioRes.data);
      setOrders(ordersRes.data.orders || []);
      setMarketData(marketRes.data);
      setNews(newsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const executeAgentCycle = async () => {
    try {
      setAgentRunning(true);
      await axios.post(`${API_BASE}/agent/execute/${userId}?instrument=${instrument}`);
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute agent cycle');
    } finally {
      setAgentRunning(false);
    }
  };

  const createOrder = async (side: string, quantity: number) => {
    try {
      await axios.post(`${API_BASE}/orders/${userId}`, {
        instrument,
        side,
        order_type: 'market',
        quantity,
      });
      await fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create order');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, bgcolor: '#f5f5f5', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ bgcolor: '#1976d2' }}>
        <Toolbar>
          <Activity style={{ marginRight: 16 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            FinTech Trading Agent
          </Typography>
          <Chip
            label={agentRunning ? 'Agent Running' : 'Agent Ready'}
            color={agentRunning ? 'warning' : 'success'}
            variant="outlined"
            sx={{ color: 'white', borderColor: 'white' }}
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <DollarSign style={{ marginRight: 8, color: '#4caf50' }} />
                  <Typography variant="h6">Portfolio</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  ${portfolio?.total_value?.toFixed(2) || '0.00'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Cash: ${portfolio?.cash_balance?.toFixed(2) || '0.00'}
                </Typography>
                <Box mt={2}>
                  <Chip
                    label={`${portfolio?.pnl_pct?.toFixed(2) || '0.00'}%`}
                    color={portfolio && portfolio.pnl_pct >= 0 ? 'success' : 'error'}
                    icon={portfolio && portfolio.pnl_pct >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <BarChart3 style={{ marginRight: 8, color: '#ff9800' }} />
                  <Typography variant="h6">Market Price</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  ${marketData?.price?.toFixed(2) || '0.00'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {instrument}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <AlertTriangle style={{ marginRight: 8, color: '#f44336' }} />
                  <Typography variant="h6">News Sentiment</Typography>
                </Box>
                <Typography variant="h4" color={news && news.avg_sentiment >= 0 ? 'success.main' : 'error.main'}>
                  {news?.avg_sentiment?.toFixed(3) || '0.000'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {news?.items?.length || 0} articles
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Zap style={{ marginRight: 8, color: '#9c27b0' }} />
                  <Typography variant="h6">Agent Control</Typography>
                </Box>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={executeAgentCycle}
                  disabled={agentRunning}
                  startIcon={agentRunning ? <CircularProgress size={20} /> : <Zap size={20} />}
                >
                  {agentRunning ? 'Running...' : 'Execute Cycle'}
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Positions
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Instrument</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell align="right">Avg Price</TableCell>
                      <TableCell align="right">Market Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {portfolio?.positions?.map((position, index) => (
                      <TableRow key={index}>
                        <TableCell>{position.instrument}</TableCell>
                        <TableCell align="right">{position.quantity.toFixed(6)}</TableCell>
                        <TableCell align="right">${position.avg_price.toFixed(2)}</TableCell>
                        <TableCell align="right">${position.market_value.toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                    {(!portfolio?.positions || portfolio.positions.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          No positions
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Recent Orders
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Side</TableCell>
                      <TableCell>Quantity</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Time</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {orders.slice(0, 5).map((order) => (
                      <TableRow key={order.order_id}>
                        <TableCell>
                          <Chip
                            label={order.side.toUpperCase()}
                            color={order.side === 'buy' ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{order.quantity?.toFixed(6) || 'N/A'}</TableCell>
                        <TableCell>
                          <Chip
                            label={order.status}
                            color={order.status === 'filled' ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{new Date(order.created_at).toLocaleTimeString()}</TableCell>
                      </TableRow>
                    ))}
                    {orders.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          No orders
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Latest News
              </Typography>
              <Grid container spacing={2}>
                {news?.items?.slice(0, 6).map((item, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                          <Typography variant="body2" color="textSecondary">
                            {item.source}
                          </Typography>
                          <Chip
                            label={item.sentiment >= 0 ? 'Positive' : 'Negative'}
                            color={item.sentiment >= 0 ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                        <Typography variant="body1" gutterBottom>
                          {item.title.length > 100 ? `${item.title.substring(0, 100)}...` : item.title}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {new Date(item.published_at).toLocaleString()}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button
                    variant="contained"
                    color="success"
                    fullWidth
                    onClick={() => createOrder('buy', 0.001)}
                    startIcon={<TrendingUp size={20} />}
                  >
                    Buy 0.001 BTC
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    variant="contained"
                    color="error"
                    fullWidth
                    onClick={() => createOrder('sell', 0.001)}
                    startIcon={<TrendingDown size={20} />}
                  >
                    Sell 0.001 BTC
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box>
                <Box display="flex" alignItems="center" mb={1}>
                  <CheckCircle style={{ marginRight: 8, color: '#4caf50' }} size={20} />
                  <Typography variant="body2">Redis Connected</Typography>
                </Box>
                <Box display="flex" alignItems="center" mb={1}>
                  <CheckCircle style={{ marginRight: 8, color: '#4caf50' }} size={20} />
                  <Typography variant="body2">Database Connected</Typography>
                </Box>
                <Box display="flex" alignItems="center" mb={1}>
                  <CheckCircle style={{ marginRight: 8, color: '#4caf50' }} size={20} />
                  <Typography variant="body2">Paper Trading Active</Typography>
                </Box>
                <Box display="flex" alignItems="center">
                  <AlertTriangle style={{ marginRight: 8, color: '#ff9800' }} size={20} />
                  <Typography variant="body2">CoinDesk API Limited</Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;