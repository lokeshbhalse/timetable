// frontend/src/pages/TestAPI.tsx
import React, { useEffect, useState } from 'react';
import api from '@/services/api';

export const TestAPI = () => {
  const [status, setStatus] = useState<string>('Testing...');
  const [courses, setCourses] = useState<any[]>([]);

  useEffect(() => {
    testConnection();
  }, []);

  const testConnection = async () => {
    try {
      // Test health
      const healthRes = await api.get('/health');
      setStatus(`Connected! Server says: ${healthRes.data.status}`);
      
      // Get courses
      const coursesRes = await api.get('/courses');
      setCourses(coursesRes.data.courses || []);
    } catch (error) {
      setStatus('Failed to connect to backend');
      console.error(error);
    }
  };

  const testGenerate = async () => {
    try {
      const response = await api.post('/timetable/generate', {
        branch: 'CSE',
        year: 1,
        section: 'A',
        semester: 1
      });
      alert('Generation successful! Check console for response');
      console.log(response.data);
    } catch (error) {
      alert('Generation failed');
      console.error(error);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Test Page</h1>
      <div className="mb-4">
        <p className="text-green-600 font-semibold">Status: {status}</p>
      </div>
      
      <button 
        onClick={testGenerate}
        className="bg-blue-500 text-white px-4 py-2 rounded mr-2"
      >
        Test Generate Timetable
      </button>
      
      <h2 className="text-xl font-bold mt-6 mb-2">Courses ({courses.length})</h2>
      <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96">
        {JSON.stringify(courses, null, 2)}
      </pre>
    </div>
  );
};

export default TestAPI;