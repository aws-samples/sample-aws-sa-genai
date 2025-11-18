import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { jobsAPI } from '../api';

function JobDetail() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJob();
    const interval = setInterval(fetchJob, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [jobId]);

  const fetchJob = async () => {
    try {
      const response = await jobsAPI.getJob(jobId);
      setJob(response.data);
    } catch (error) {
      console.error('Failed to fetch job:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status) => {
    return `status status-${status.toLowerCase()}`;
  };

  const getStepClass = (status) => {
    if (!status) return 'step';
    return `step step-${status.toLowerCase()}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const calculateDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return 'N/A';
    const start = new Date(startTime);
    const end = new Date(endTime);
    const duration = Math.round((end - start) / 1000);
    return `${duration}s`;
  };

  if (loading) return <div>Loading job details...</div>;
  if (!job) return <div>Job not found</div>;

  return (
    <div>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <h2>Job Details: {job.jobId}</h2>
        <Link to="/" className="btn btn-secondary">Back to Jobs</Link>
      </div>
      
      <div className="job-card">
        <div className={getStatusClass(job.status)}>
          Status: {job.status}
        </div>
        
        <p><strong>Initiated by:</strong> {job.initiatedBy}</p>
        <p><strong>Created:</strong> {formatDate(job.createdAt)}</p>
        <p><strong>Updated:</strong> {formatDate(job.updatedAt)}</p>
        {job.currentStep && <p><strong>Current Step:</strong> {job.currentStep}</p>}
        
        {job.payload && (
          <div>
            <h3>Configuration</h3>
            <pre style={{background: '#f5f5f5', padding: '1rem', borderRadius: '4px', overflow: 'auto'}}>
              {JSON.stringify(job.payload, null, 2)}
            </pre>
          </div>
        )}
        
        <h3>Steps</h3>
        {job.steps && job.steps.length > 0 ? (
          job.steps.map((step, index) => (
            <div key={index} className={getStepClass(step.status)}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div>
                  <strong>{step.name}</strong>
                  <span style={{marginLeft: '1rem', fontSize: '0.9em'}}>
                    {step.status || 'PENDING'}
                  </span>
                </div>
                <div style={{fontSize: '0.8em', color: '#666'}}>
                  {calculateDuration(step.startedAt, step.endedAt)}
                </div>
              </div>
              
              {step.startedAt && (
                <div style={{fontSize: '0.8em', color: '#666', marginTop: '0.25rem'}}>
                  Started: {formatDate(step.startedAt)}
                  {step.endedAt && ` | Ended: ${formatDate(step.endedAt)}`}
                </div>
              )}
              
              {step.outputS3Key && (
                <div style={{fontSize: '0.8em', marginTop: '0.25rem'}}>
                  Output: {step.outputS3Key}
                </div>
              )}
              
              {step.errorMessage && (
                <div style={{color: '#dc3545', fontSize: '0.8em', marginTop: '0.25rem'}}>
                  Error: {step.errorMessage}
                </div>
              )}
            </div>
          ))
        ) : (
          <p>No steps recorded yet.</p>
        )}
        
        {job.results && (
          <div>
            <h3>Results</h3>
            <pre style={{background: '#f5f5f5', padding: '1rem', borderRadius: '4px', overflow: 'auto'}}>
              {JSON.stringify(job.results, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default JobDetail;