import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '';

const getSummaryReport = async () => {
  const response = await axios.get(`${API_BASE}/v1/analysis/summary`);
  return response.data;
};

const getWeightTable = async () => {
  const response = await axios.get(`${API_BASE}/v1/analysis/weights`);
  return response.data;
};

export default { getSummaryReport, getWeightTable };
