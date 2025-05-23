import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  TableContainer,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { useTheme } from '@mui/material/styles';
import AnalysisService from '../services/AnalysisService';

const AnalysisPage = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [weights, setWeights] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await AnalysisService.getSummaryReport();
        setData(result);
      } catch (err) {
        console.error('Error fetching summary report:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();

    // Fetch weight table
    AnalysisService.getWeightTable()
      .then(w => setWeights(w))
      .catch(err => console.error('Error fetching weight table:', err));
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography color="error">Error: {error}</Typography>
      </Box>
    );
  }

  if (!data.length) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography>No analysis data available.</Typography>
      </Box>
    );
  }

  // Dynamically derive metrics and market types from data
  const metrics = Object.keys(data[0]).filter(key => key !== 'strategy' && key !== 'market_type');
  const marketTypes = [...new Set(data.map(item => item.market_type))];
  const strategies = [...new Set(data.map(item => item.strategy))];

  // Build rows for DataGrid
  const rows = strategies.map((strategy, idx) => {
    const row = { id: idx, strategy };
    metrics.forEach(metric => {
      marketTypes.forEach(mt => {
        const rec = data.find(r => r.strategy === strategy && r.market_type === mt);
        row[`${metric}_${mt}`] = rec ? rec[metric] : null;
      });
    });
    return row;
  });

  // Build DataGrid columns
  const columns = [
    { field: 'strategy', headerName: 'Strategy', width: 200 }
  ];
  metrics.forEach(metric => {
    marketTypes.forEach(mt => {
      columns.push({
        field: `${metric}_${mt}`,
        headerName: `${mt} ${metric.replace('_', ' ')}`,
        width: 150,
        valueFormatter: params => typeof params.value === 'number' ? params.value.toFixed(metric === 'win_rate' ? 4 : 2) : params.value
      });
    });
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Strategy Comparative Analysis</Typography>
      <DataGrid
        rows={rows}
        columns={columns}
        autoHeight
        pageSize={10}
        rowsPerPageOptions={[5, 10]}
      />
      {/* Weight Table Section */}
      {weights && (
        <Box sx={{ mt: 5 }}>
          <Typography variant="h5" gutterBottom>Ensemble Weights by Market</Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Market Type</TableCell>
                  {Object.keys(weights).length > 0 && Object.keys(weights[Object.keys(weights)[0]]).map(strat => (
                    <TableCell key={strat} align="right">{strat}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(weights).map(([market, wts]) => (
                  <TableRow key={market}>
                    <TableCell>{market}</TableCell>
                    {Object.values(wts).map((val, idx) => (
                      <TableCell key={idx} align="right">{(val*100).toFixed(2)}%</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
    </Box>
  );
};

export default AnalysisPage;
