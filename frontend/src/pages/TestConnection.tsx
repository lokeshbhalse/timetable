// frontend/src/pages/TestConnection.tsx
import React, { useState, useEffect } from 'react';

const TestConnection = () => {
  const [status, setStatus] = useState<string>('Testing...');
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Test backend connection
  const testBackend = async () => {
    setStatus('Testing connection to http://localhost:8000...');
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/health');
      const data = await response.json();
      setStatus(`✅ Connected! Backend says: ${data.message}`);
      return true;
    } catch (err: any) {
      setStatus(`❌ Connection failed: ${err.message}`);
      setError(`Cannot connect to backend at http://localhost:8000. Make sure to run: python app.py`);
      return false;
    }
  };

  // Fetch courses from backend
  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/courses');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setCourses(data.courses || []);
      alert(`✅ Found ${data.courses?.length || 0} courses in database`);
    } catch (err: any) {
      setError(`Failed to fetch courses: ${err.message}`);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Generate timetable
  const generateTimetable = async () => {
    setLoading(true);
    setError(null);
    
    const sampleCourses = [
      {
        course_name: "Mathematics",
        no_of_students: 60,
        semester: "1",
        department: "CSE",
        lab: "n",
        preference: 0
      },
      {
        course_name: "Physics",
        no_of_students: 60,
        semester: "1",
        department: "CSE",
        lab: "n",
        preference: 0
      }
    ];
    
    try {
      const response = await fetch('http://localhost:8000/api/timetable/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branch: 'CSE', year: 1, section: 'A', semester: 1 })
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      console.log('Generation result:', data);
      alert(`✅ Timetable generated! Created ${Object.keys(data.timetables || {}).length} timetables`);
    } catch (err: any) {
      setError(`Generation failed: ${err.message}`);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testBackend();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🔌 Backend Connection Test</h1>
      
      {/* Status Card */}
      <div style={{ 
        margin: '20px 0', 
        padding: '15px', 
        background: status.includes('✅') ? '#d4edda' : '#f8d7da',
        border: `1px solid ${status.includes('✅') ? '#c3e6cb' : '#f5c6cb'}`,
        borderRadius: '5px'
      }}>
        <strong>Status:</strong> {status}
      </div>

      {/* Error Display */}
      {error && (
        <div style={{ 
          margin: '20px 0', 
          padding: '15px', 
          background: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '5px',
          color: '#721c24'
        }}>
          <strong>❌ Error:</strong><br />
          {error}
        </div>
      )}

      {/* Buttons */}
      <div style={{ display: 'flex', gap: '10px', margin: '20px 0', flexWrap: 'wrap' }}>
        <button 
          onClick={testBackend}
          style={buttonStyle.primary}
        >
          🔄 Test Connection
        </button>
        
        <button 
          onClick={fetchCourses}
          disabled={loading}
          style={buttonStyle.success}
        >
          {loading ? 'Loading...' : '📚 Fetch Courses'}
        </button>
        
        <button 
          onClick={generateTimetable}
          disabled={loading}
          style={buttonStyle.warning}
        >
          {loading ? 'Generating...' : '🎲 Generate Timetable'}
        </button>
      </div>

      {/* Courses Display */}
      {courses.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h2>📋 Courses ({courses.length})</h2>
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '10px', 
            borderRadius: '5px', 
            overflow: 'auto',
            maxHeight: '300px',
            fontSize: '12px'
          }}>
            {JSON.stringify(courses.slice(0, 10), null, 2)}
          </pre>
        </div>
      )}

      {/* Instructions */}
      <div style={{ 
        marginTop: '30px', 
        padding: '15px', 
        background: '#e7f3ff',
        borderRadius: '5px',
        fontSize: '14px'
      }}>
        <h3>📝 Troubleshooting:</h3>
        <ol>
          <li>Make sure backend is running: <code>python main.py</code> in a separate terminal</li>
          <li>Backend should show: <code>Uvicorn running on http://127.0.0.1:8000</code></li>
          <li>Test backend directly: <a href="http://localhost:8000/api/health" target="_blank">http://localhost:8000/api/health</a></li>
          <li>Check if port 8000 is not blocked by firewall</li>
          <li>If using Windows, try: <code>netsh advfirewall firewall add rule name="Open Port 8000" dir=in action=allow protocol=TCP localport=8000</code></li>
        </ol>
      </div>
    </div>
  );
};

// Button styles
const buttonStyle = {
  primary: {
    padding: '10px 20px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  success: {
    padding: '10px 20px',
    background: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  warning: {
    padding: '10px 20px',
    background: '#ffc107',
    color: '#333',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px'
  }
};

export default TestConnection;