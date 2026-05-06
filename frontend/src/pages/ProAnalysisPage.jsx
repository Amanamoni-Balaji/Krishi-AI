import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    TrendingUp, Sprout, Bug, Calendar, ArrowLeft,
    Droplets, CheckCircle, AlertTriangle, Clock
} from 'lucide-react';
import axios from 'axios';
import { translations } from '../utils/translations';
import '../App.css';

const API_URL = 'http://127.0.0.1:5000';

const ProAnalysisPage = ({ language }) => {
    const location = useLocation();
    const navigate  = useNavigate();
    const { prediction, erosionRisk, longForecast, aiAdvice, recommendation, formData } =
        location.state || {};
    const t = translations[language] || translations['en'];

    const [proData, setProData]   = useState(null);
    const [loading, setLoading]   = useState(true);
    const [error, setError]       = useState('');

    useEffect(() => {
        if (!location.state) { navigate('/app'); return; }
        window.scrollTo(0, 0);

        // Call the real /pro-analysis endpoint
        axios.post(`${API_URL}/pro-analysis`, {
            district:     formData?.district    || '',
            season:       formData?.season      || 'Kharif',
            crop:         formData?.crop        || '',
            area:         formData?.areaInHa    || 1,
            rainfall:     formData?.rainfallUsed || 0,
            sowing_date:  formData?.sowing_date || '',
            weather_data: longForecast          || [],
        })
            .then(res => { setProData(res.data); setLoading(false); })
            .catch(err => {
                setError('Failed to load Pro analysis data. Check backend is running.');
                setLoading(false);
            });
    }, []);

    if (!location.state) return null;

    const formatINR = (n) =>
        n >= 100000
            ? `₹${(n / 100000).toFixed(1)}L`
            : `₹${Number(n).toLocaleString('en-IN')}`;

    return (
        <div className="app-container editorial-theme">
            <div className="grid-lines fixed">
                <div className="line" /><div className="line" />
                <div className="line" /><div className="line" />
            </div>

            <header className="app-header editorial-header">
                <div className="brand" onClick={() => navigate('/')}
                    style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Sprout size={32} color="#1A3C34" />
                    <h1 style={{ color: '#1A3C34', margin: 0, fontSize: '1.5rem' }}>{t.brand}</h1>
                </div>
                <button className="editorial-btn-small pro-back-btn" onClick={() => navigate(-1)}>
                    <ArrowLeft size={16} /> {t.back || 'Back'}
                </button>
            </header>

            <main className="main-content-dashboard relative-z">
                <div className="dashboard-title pro-title">
                    <h2>{t.premium_analysis || 'Pro Analysis'}</h2>
                    <p>
                        {formData?.crop} · {formData?.district} · {formData?.season}
                    </p>
                </div>

                {loading && (
                    <div style={{ textAlign: 'center', padding: '4rem', color: '#666' }}>
                        <div className="payment-spinner" style={{ margin: '0 auto 1rem' }} />
                        <p>Loading Pro analysis from real data...</p>
                    </div>
                )}

                {error && (
                    <div style={{ padding: '2rem', color: '#ef4444', textAlign: 'center' }}>
                        {error}
                    </div>
                )}

                {proData && (
                    <div className="pro-dashboard-grid">

                        {/* ── 1. Market Intelligence ─────────────────────────── */}
                        <motion.div className="editorial-card pro-card market-card"
                            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}>
                            <div className="pro-card-header"
                                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                                <div className="icon-bg"
                                    style={{ background: '#dcfce7', padding: '8px', borderRadius: '50%' }}>
                                    <TrendingUp size={24} color="#166534" />
                                </div>
                                <h3 style={{ margin: 0, color: '#1A3C34' }}>
                                    {t.market_intelligence || 'Market Intelligence'}
                                </h3>
                            </div>
                            <p className="pro-card-desc">
                                Revenue forecast based on ML yield prediction × MSP/market rate for {formData?.crop}.
                            </p>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.25rem' }}>
                                {[
                                    { label: 'Predicted Revenue', value: formatINR(proData.market.revenue_estimate), color: '#166534' },
                                    { label: 'Est. Input Cost',   value: formatINR(proData.market.cost_estimate),    color: '#92400e' },
                                    { label: 'Net Profit Est.',   value: formatINR(proData.market.profit_estimate),
                                      color: proData.market.profit_estimate >= 0 ? '#166534' : '#ef4444' },
                                ].map(({ label, value, color }) => (
                                    <div key={label} style={{ background: '#f0fdf4', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
                                        <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem' }}>{label}</div>
                                        <div style={{ fontSize: '1.25rem', fontWeight: '700', color }}>{value}</div>
                                    </div>
                                ))}
                            </div>

                            <div>
                                <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.75rem' }}>
                                    Price trend for {formData?.crop} (based on MSP growth)
                                </div>
                                <div className="market-content">
                                    <div className="price-forecast">
                                        <div className="forecast-bars">
                                            {proData.market.price_trend.map((item, i) => (
                                                <div key={i} className="bar-group">
                                                    <div className="bar"
                                                        style={{ height: `${(item.price / (proData.market.price_per_quintal * 1.15)) * 100}%` }} />
                                                    <span className="month">{item.period}</span>
                                                    <span className="price">₹{Math.round(item.price)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                                <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '0.5rem' }}>
                                    MSP rate: ₹{proData.market.price_per_quintal}/quintal ·
                                    Production: {proData.market.predicted_production_t} tonnes
                                </div>
                            </div>
                        </motion.div>

                        {/* ── 2. Soil Health ─────────────────────────────────── */}
                        <motion.div className="editorial-card pro-card soil-card"
                            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}>
                            <div className="pro-card-header"
                                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                                <div className="icon-bg"
                                    style={{ background: '#fef9c3', padding: '8px', borderRadius: '50%' }}>
                                    <Sprout size={24} color="#854d0e" />
                                </div>
                                <h3 style={{ margin: 0, color: '#1A3C34' }}>
                                    {t.soil_health || 'Soil & Nutrient Plan'}
                                </h3>
                            </div>
                            <p className="pro-card-desc">
                                Nutrient requirements for {formData?.crop} based on crop-specific agronomic data.
                            </p>

                            <div className="soil-grid">
                                {[
                                    { label: 'Nitrogen (N)', level: proData.soil.nitrogen },
                                    { label: 'Phosphorus (P)', level: proData.soil.phosphorus },
                                    { label: 'Potassium (K)', level: proData.soil.potassium },
                                ].map(({ label, level }) => {
                                    const pct = level === 'High' ? 85 : level === 'Medium' ? 55 : 30;
                                    const cls = level === 'High' ? 'optimal' : level === 'Medium' ? 'medium' : 'low';
                                    return (
                                        <div className="soil-item" key={label}>
                                            <span className="label">{label}</span>
                                            <div className="progress-bar">
                                                <div className={`fill ${cls}`} style={{ width: `${pct}%` }} />
                                            </div>
                                            <span className={`status ${level === 'High' ? 'good' : level === 'Medium' ? 'ok' : 'warning'}`}>
                                                {level} need
                                            </span>
                                        </div>
                                    );
                                })}
                                <div className="soil-item ph-item">
                                    <span className="label">Optimal pH</span>
                                    <span className="ph-value">{proData.soil.pH_range}</span>
                                    <span className="status">Target range for {formData?.crop}</span>
                                </div>
                                <div className="soil-item" style={{ gridColumn: '1 / -1' }}>
                                    <span className="label">Water Requirement</span>
                                    <span className="status good" style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
                                        <Droplets size={14} /> {proData.soil.water_need}
                                    </span>
                                </div>
                            </div>

                            {proData.soil.recommendations?.length > 0 && (
                                <div style={{ marginTop: '1rem', borderTop: '1px solid #e5e7eb', paddingTop: '0.75rem' }}>
                                    <div style={{ fontSize: '0.85rem', fontWeight: '600', color: '#1A3C34', marginBottom: '0.5rem' }}>
                                        Fertilizer Recommendations:
                                    </div>
                                    {proData.soil.recommendations.map((rec, i) => (
                                        <div key={i} style={{ fontSize: '0.82rem', color: '#444', display: 'flex', gap: '0.5rem', marginBottom: '0.35rem' }}>
                                            <CheckCircle size={13} color="#10b981" style={{ flexShrink: 0, marginTop: 2 }} />
                                            {rec}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </motion.div>

                        {/* ── 3. Pest Risk ───────────────────────────────────── */}
                        <motion.div className="editorial-card pro-card pest-card"
                            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}>
                            <div className="pro-card-header"
                                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                                <div className="icon-bg"
                                    style={{ background: '#fee2e2', padding: '8px', borderRadius: '50%' }}>
                                    <Bug size={24} color="#991b1b" />
                                </div>
                                <h3 style={{ margin: 0, color: '#1A3C34' }}>
                                    {t.pest_forecast || 'Pest Risk Forecast'}
                                </h3>
                            </div>
                            <p className="pro-card-desc">
                                Pest risk derived from live 14-day weather patterns (temperature, humidity, rainfall).
                            </p>
                            <div className="pest-timeline">
                                {proData.pest_risks.map((risk, i) => (
                                    <div key={i} className={`timeline-item ${risk.risk === 'High' ? 'warning' : 'info'}`}>
                                        <div className="date">{risk.date || 'Watch period'}</div>
                                        <div className="content">
                                            <h4 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                {risk.risk === 'High'
                                                    ? <AlertTriangle size={14} color="#f59e0b" />
                                                    : <Clock size={14} color="#3b82f6" />}
                                                {risk.pest}
                                                <span style={{
                                                    marginLeft: 'auto', fontSize: '0.7rem', padding: '2px 8px',
                                                    borderRadius: '9999px',
                                                    background: risk.risk === 'High' ? '#fee2e2' : '#dbeafe',
                                                    color: risk.risk === 'High' ? '#991b1b' : '#1e40af'
                                                }}>
                                                    {risk.risk}
                                                </span>
                                            </h4>
                                            <p style={{ margin: '0.25rem 0 0', fontSize: '0.82rem', color: '#555' }}>
                                                {risk.action}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        {/* ── 4. Crop Calendar ───────────────────────────────── */}
                        <motion.div className="editorial-card pro-card calendar-card"
                            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}>
                            <div className="pro-card-header"
                                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                                <div className="icon-bg"
                                    style={{ background: '#dbeafe', padding: '8px', borderRadius: '50%' }}>
                                    <Calendar size={24} color="#1e40af" />
                                </div>
                                <h3 style={{ margin: 0, color: '#1A3C34' }}>
                                    {t.smart_calendar || 'Crop Calendar'}
                                </h3>
                            </div>
                            <p className="pro-card-desc">
                                Stage-by-stage schedule computed from your sowing date and {formData?.season} season.
                            </p>
                            <div className="calendar-list">
                                {proData.calendar.map((stage, i) => (
                                    <div key={i} className={`cal-item ${stage.status}`}>
                                        {stage.status === 'completed'
                                            ? <CheckCircle size={15} color="#10b981" />
                                            : stage.status === 'active'
                                                ? <div className="circle" style={{ background: '#1A3C34' }} />
                                                : <div className="circle" />}
                                        <div style={{ flex: 1 }}>
                                            <span style={{ fontWeight: stage.status === 'active' ? '700' : '400' }}>
                                                {stage.stage}
                                            </span>
                                            <span style={{ float: 'right', fontSize: '0.8rem', color: '#888' }}>
                                                {stage.date}
                                            </span>
                                            {stage.status === 'active' && (
                                                <div style={{ fontSize: '0.75rem', color: '#1A3C34', marginTop: '2px' }}>
                                                    Due now
                                                </div>
                                            )}
                                            {stage.status !== 'active' && stage.status !== 'completed' && (
                                                <div style={{ fontSize: '0.75rem', color: '#888', marginTop: '2px' }}>
                                                    In {stage.days_from_today} days
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default ProAnalysisPage;
