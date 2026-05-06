import React, { useState, useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';

import LandingPage from './pages/LandingPage';
import MainTool from './pages/MainTool';
import ResultsPage from './pages/ResultsPage';
import ProAnalysisPage from './pages/ProAnalysisPage';
import MLOpsDashboard from './pages/MLOpsDashboard';
import './App.css';

function App() {
    const location = useLocation();
    const [language, setLanguage] = useState('en'); // Default language

    return (
        <div className="App">
            <Routes>
                <Route path="/" element={<LandingPage language={language} setLanguage={setLanguage} />} />
                <Route path="/app" element={<MainTool language={language} setLanguage={setLanguage} />} />
                <Route path="/results" element={<ResultsPage language={language} setLanguage={setLanguage} />} />
                <Route path="/pro-analysis" element={<ProAnalysisPage language={language} setLanguage={setLanguage} />} />
                <Route path="/mlops" element={<MLOpsDashboard language={language} />} />
            </Routes>
        </div>
    );
}

export default App;
