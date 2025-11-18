import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const jobsAPI = {
  createJob: (config, initiatedBy) => 
    api.post('/jobs', { config, initiated_by: initiatedBy }),
  
  getJobs: () => 
    api.get('/jobs'),
  
  getJob: (jobId) => 
    api.get(`/jobs/${jobId}`),
  
  startExport: (payload) => 
    api.post('/export', payload),
  
  checkExportStatus: (exportJobId, payload) => 
    api.get(`/export/${exportJobId}`, { data: payload }),
  
  uploadAssets: (payload) => 
    api.post('/upload', payload),
  
  importAssets: (payload) => 
    api.post('/import', payload),
};

export default api;