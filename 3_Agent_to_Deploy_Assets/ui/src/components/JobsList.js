import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { jobsAPI } from '../api';

function JobsList() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await jobsAPI.getJobs();
      setJobs(response.data.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status) => {
    return `status status-${status.toLowerCase()}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) return <div>Loading jobs...</div>;

  return (
    <div>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <h2>Asset Deployment Jobs</h2>
        <Link to="/new" className="btn btn-primary">New Job</Link>
      </div>
      
      {jobs.length === 0 ? (
        <p>No jobs found. <Link to="/new">Create your first job</Link></p>
      ) : (
        jobs.map(job => (
          <div key={job.jobId} className="job-card">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div>
                <h3>
                  <Link to={`/jobs/${job.jobId}`} style={{textDecoration: 'none'}}>
                    {job.jobId}
                  </Link>
                </h3>
                <p>Initiated by: {job.initiatedBy}</p>
                <p>Created: {formatDate(job.createdAt)}</p>
                {job.currentStep && <p>Current Step: {job.currentStep}</p>}
              </div>
              <div>
                <div className={getStatusClass(job.status)}>
                  {job.status}
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default JobsList;