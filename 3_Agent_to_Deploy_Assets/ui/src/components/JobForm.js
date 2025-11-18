import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { jobsAPI } from '../api';

function JobForm() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    source_account_id: '',
    source_role_name: 'QuickSightRole',
    source_asset_id: '',
    target_account_id: '',
    target_role_name: 'QuickSightRole',
    target_admin_user: '',
    bucket_name: 'biops-version-control-demo-2025',
    dashboard_name: 'BIOpsDemo',
    aws_region: 'us-east-1',
    initiated_by: 'ui-user'
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const { initiated_by, ...config } = formData;
      await jobsAPI.createJob(config, initiated_by);
      navigate('/');
    } catch (error) {
      alert('Failed to start job: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Start New Asset Deployment Job</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Source Account ID:</label>
          <input
            type="text"
            name="source_account_id"
            value={formData.source_account_id}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label>Source Asset ID:</label>
          <input
            type="text"
            name="source_asset_id"
            value={formData.source_asset_id}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label>Target Account ID:</label>
          <input
            type="text"
            name="target_account_id"
            value={formData.target_account_id}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label>Target Admin User:</label>
          <input
            type="text"
            name="target_admin_user"
            value={formData.target_admin_user}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label>Initiated By:</label>
          <input
            type="text"
            name="initiated_by"
            value={formData.initiated_by}
            onChange={handleChange}
            required
          />
        </div>
        
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Starting Job...' : 'Start Job'}
        </button>
      </form>
    </div>
  );
}

export default JobForm;