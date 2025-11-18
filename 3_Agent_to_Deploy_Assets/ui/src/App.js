import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import JobForm from './components/JobForm';
import JobsList from './components/JobsList';
import JobDetail from './components/JobDetail';

function App() {
  const location = useLocation();

  return (
    <div>
      <div className="header">
        <div className="container">
          <h1>BIOPS Asset Deployment</h1>
          <nav>
            <Link to="/" style={{color: 'white', marginRight: '1rem'}}>Jobs</Link>
            <Link to="/new" style={{color: 'white'}}>New Job</Link>
          </nav>
        </div>
      </div>
      
      <div className="container">
        <Routes>
          <Route path="/" element={<JobsList />} />
          <Route path="/new" element={<JobForm />} />
          <Route path="/jobs/:jobId" element={<JobDetail />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;