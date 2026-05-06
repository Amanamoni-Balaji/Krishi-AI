import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
    Sprout, CloudRain, Activity, MapPin, Droplets,
    ChevronRight, Calendar, Globe
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../App.css';
import {
    getSlopeFromDistrict,
    getSlopeDegreesFromDistrict,
    calculateErosionRisk,
    fetchWeatherForecast
} from '../utils/agriLogic';
import { translations } from '../utils/translations';
import heroImage from '../assets/hero_new.jpg';

import icon       from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

L.Marker.prototype.options.icon = L.icon({
    iconUrl: icon, shadowUrl: iconShadow,
    iconSize: [25, 41], iconAnchor: [12, 41]
});

const API_URL = 'http://127.0.0.1:5000';

// District centre coordinates (for map auto-pan)
const DISTRICT_COORDS = {
    'EAST KHASI HILLS':       { lat: 25.4670, lon: 91.3662 },
    'WEST KHASI HILLS':       { lat: 25.3500, lon: 91.0800 },
    'SOUTH WEST KHASI HILLS': { lat: 25.1800, lon: 91.2000 },
    'EAST JAINTIA HILLS':     { lat: 25.3700, lon: 92.2000 },
    'WEST JAINTIA HILLS':     { lat: 25.4500, lon: 92.0500 },
    'EAST GARO HILLS':        { lat: 25.5700, lon: 90.6500 },
    'WEST GARO HILLS':        { lat: 25.5200, lon: 90.2500 },
    'NORTH GARO HILLS':       { lat: 25.7800, lon: 90.5100 },
    'SOUTH GARO HILLS':       { lat: 25.2200, lon: 90.4200 },
    'SOUTH WEST GARO HILLS':  { lat: 25.3500, lon: 89.9500 },
    'RI BHOI':                { lat: 25.7600, lon: 91.6700 },
};

function LocationMarker({ setLocation }) {
    const [position, setPosition] = useState(null);
    const map = useMapEvents({
        click(e) {
            setPosition(e.latlng);
            setLocation(e.latlng.lat, e.latlng.lng);
            map.flyTo(e.latlng, map.getZoom());
        },
    });
    return position ? <Marker position={position} /> : null;
}

function MainTool({ language, setLanguage }) {
    const navigate = useNavigate();
    const t = translations[language] || translations['en'];

    const [info, setInfo]       = useState({ districts: [], seasons: [], crops: [] });
    const [formData, setFormData] = useState({
        district:    '',
        season:      '',
        crop:        '',
        area:        '',
        rainfall:    '',
        slope:       'Gentle',
        sowing_date: '',
        lat:         25.4670,
        lon:         91.3662,
        soil_type:   'Loamy'
    });
    const [loading, setLoading]               = useState(false);
    const [rainfallHint, setRainfallHint]     = useState('');
    const [districtInfo, setDistrictInfo]     = useState(null);

    // Load dropdowns from backend
    useEffect(() => {
        axios.get(`${API_URL}/info`)
            .then(res => {
                setInfo(res.data);
                const firstDistrict = res.data.districts[0] || '';
                const firstSeason   = res.data.seasons[0]   || '';
                const firstCrop     = res.data.crops[0]     || '';
                setFormData(prev => ({
                    ...prev,
                    district: firstDistrict,
                    season:   firstSeason,
                    crop:     firstCrop,
                    slope:    getSlopeFromDistrict(firstDistrict),
                    lat:      DISTRICT_COORDS[firstDistrict]?.lat || 25.4670,
                    lon:      DISTRICT_COORDS[firstDistrict]?.lon || 91.3662,
                }));
            })
            .catch(err => console.error("Error fetching info:", err));
    }, []);

    // When district changes → fetch real rainfall & slope from backend
    useEffect(() => {
        if (!formData.district) return;

        const slope   = getSlopeFromDistrict(formData.district);
        const coords  = DISTRICT_COORDS[formData.district];
        setFormData(prev => ({
            ...prev,
            slope,
            ...(coords ? { lat: coords.lat, lon: coords.lon } : {})
        }));

        axios.get(`${API_URL}/district-info`, { params: { district: formData.district } })
            .then(res => {
                setDistrictInfo(res.data);
                const currentMonthRain = res.data.current_month_rainfall;
                setRainfallHint(
                    `Avg for ${res.data.current_month}: ${currentMonthRain} mm ` +
                    `| Annual: ${res.data.annual_total_rainfall} mm`
                );
                // Auto-populate rainfall with current month's historical average
                setFormData(prev => ({
                    ...prev,
                    rainfall: String(Math.round(currentMonthRain))
                }));
            })
            .catch(() => setRainfallHint(''));
    }, [formData.district]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const setLocation = (lat, lon) => {
        setFormData(prev => ({ ...prev, lat, lon }));
    };

    const handlePredict = async () => {
        if (!formData.area || isNaN(formData.area) || Number(formData.area) <= 0) {
            alert("Please enter a valid area (in acres).");
            return;
        }
        if (!formData.crop) {
            alert("Please select a crop.");
            return;
        }

        setLoading(true);
        try {
            // 1. Real weather from Open-Meteo
            const weatherData = await fetchWeatherForecast(formData.lat, formData.lon);

            // 2. Erosion risk
            const totalRain30d = weatherData.reduce((s, d) => s + d.rain, 0);
            const risk         = calculateErosionRisk(formData.slope, totalRain30d);

            // 3. Convert area: acres → hectares
            const areaInHa = Number(formData.area) * 0.404686;

            // Determine rainfall to use
            const rainfallVal = formData.rainfall && Number(formData.rainfall) > 0
                ? Number(formData.rainfall)
                : (districtInfo ? districtInfo.annual_total_rainfall : 1500);

            // 4. Advisory (passes real weather from Open-Meteo to backend)
            const advisoryRes = await axios.post(`${API_URL}/advisory`, {
                lat:          formData.lat,
                lon:          formData.lon,
                crop:         formData.crop,
                sowing_date:  formData.sowing_date,
                weather_data: weatherData
            });

            // 5. ML Yield Prediction
            const predictRes = await axios.post(`${API_URL}/predict`, {
                district: formData.district,
                season:   formData.season,
                crop:     formData.crop,
                area:     areaInHa,
                rainfall: rainfallVal
            });

            // 6. Crop Recommendations
            const recommendRes = await axios.post(`${API_URL}/recommend`, {
                district: formData.district,
                season:   formData.season,
                area:     areaInHa,
                rainfall: rainfallVal,
                slope:    formData.slope
            });

            // 7. Forecast (monthly rainfall from CSV)
            const forecastRes = await axios.post(`${API_URL}/forecast`, {
                district: formData.district
            });

            setTimeout(() => {
                navigate('/results', {
                    state: {
                        prediction:     predictRes.data,
                        erosionRisk:    risk,
                        longForecast:   weatherData,
                        aiAdvice:       advisoryRes.data,
                        recommendation: recommendRes.data,
                        monthlyForecast: forecastRes.data.forecast,
                        formData:       { ...formData, areaInHa, rainfallUsed: rainfallVal },
                        inputAreaAcres: formData.area,
                        slopeInfo:      {
                            slope:   formData.slope,
                            degrees: getSlopeDegreesFromDistrict(formData.district)
                        }
                    }
                });
            }, 1200);

        } catch (err) {
            console.error("Prediction error:", err);
            const msg = err.response?.data?.error || "Failed to get prediction. Check inputs and ensure backend is running.";
            alert(`Error: ${msg}`);
            setLoading(false);
        }
    };

    return (
        <div className="app-container editorial-theme">
            <header className="app-header editorial-header">
                <div className="brand" onClick={() => navigate('/')}
                    style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Sprout size={32} color="#1A3C34" />
                    <h1 style={{ color: '#1A3C34', margin: 0, fontSize: '1.5rem' }}>{t.brand}</h1>
                </div>
                <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div className="lang-selector" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Globe size={18} color="#1A3C34" />
                        <select value={language} onChange={(e) => setLanguage(e.target.value)}
                            style={{ border: 'none', background: 'transparent', fontSize: '0.9rem',
                                     color: '#1A3C34', cursor: 'pointer', fontWeight: 'bold' }}>
                            <option value="en">English</option>
                            <option value="hi">हिंदी</option>
                            <option value="kha">Khasi</option>
                        </select>
                    </div>
                </div>
            </header>

            <main className="main-content-dashboard relative-z">
                <div className="dashboard-title">
                    <h2>{t.dashboard}</h2>
                    <p>{t.enter_details}</p>
                </div>

                <div className="dashboard-grid">
                    <div className="input-card editorial-card">

                        {/* District */}
                        <div className="form-group">
                            <label>{t.location}</label>
                            <div className="input-wrapper">
                                <MapPin size={18} className="input-icon" />
                                <select name="district" value={formData.district} onChange={handleInputChange}>
                                    {info.districts.map(d => <option key={d} value={d}>{d}</option>)}
                                </select>
                            </div>
                            {districtInfo && (
                                <small style={{ color: '#666', fontSize: '0.8rem', marginTop: '0.25rem', display: 'block' }}>
                                    Slope: {districtInfo.slope} ({districtInfo.slope_degrees}°) &nbsp;|&nbsp;
                                    Annual rainfall: {districtInfo.annual_total_rainfall} mm
                                </small>
                            )}
                        </div>

                        {/* Map */}
                        <div className="form-group" style={{ height: '200px', marginBottom: '1.5rem',
                            borderRadius: '8px', overflow: 'hidden', border: '1px solid #ddd' }}>
                            <label style={{ marginBottom: '0.5rem', display: 'block',
                                           fontSize: '0.9rem', color: '#1A3C34' }}>{t.pin_location}</label>
                            <MapContainer center={[formData.lat, formData.lon]} zoom={10}
                                style={{ height: '100%', width: '100%' }}>
                                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    attribution='&copy; OpenStreetMap contributors' />
                                <LocationMarker setLocation={setLocation} />
                            </MapContainer>
                        </div>

                        {/* Season */}
                        <div className="form-group">
                            <label>Season</label>
                            <div className="input-wrapper">
                                <Calendar size={18} className="input-icon" />
                                <select name="season" value={formData.season} onChange={handleInputChange}>
                                    {info.seasons.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                            </div>
                        </div>

                        {/* Crop */}
                        <div className="form-group">
                            <label>{t.crop_selection}</label>
                            <div className="input-wrapper">
                                <Sprout size={18} className="input-icon" />
                                <select name="crop" value={formData.crop} onChange={handleInputChange}>
                                    <option value="">-- Select Crop --</option>
                                    {info.crops.map(c => <option key={c} value={c}>{c}</option>)}
                                </select>
                            </div>
                        </div>

                        {/* Area */}
                        <div className="form-group">
                            <label>{t.area} (acres)</label>
                            <div className="input-wrapper">
                                <Activity size={18} className="input-icon" />
                                <input type="number" name="area" value={formData.area}
                                    onChange={handleInputChange} placeholder="e.g. 5" min="0.1" step="0.1" />
                            </div>
                        </div>

                        {/* Rainfall */}
                        <div className="form-group">
                            <label>
                                <CloudRain size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                                Annual Rainfall (mm)
                            </label>
                            <div className="input-wrapper">
                                <Droplets size={18} className="input-icon" />
                                <input type="number" name="rainfall" value={formData.rainfall}
                                    onChange={handleInputChange} placeholder="Auto-filled from district data" min="0" />
                            </div>
                            {rainfallHint && (
                                <small style={{ color: '#1A3C34', fontSize: '0.78rem', marginTop: '0.2rem', display: 'block' }}>
                                    {rainfallHint}
                                </small>
                            )}
                        </div>

                        {/* Sowing Date */}
                        <div className="form-group">
                            <label>Sowing Date (for calendar)</label>
                            <div className="input-wrapper">
                                <Calendar size={18} className="input-icon" />
                                <input type="date" name="sowing_date" value={formData.sowing_date}
                                    onChange={handleInputChange} />
                            </div>
                        </div>

                        <button className="analyze-btn editorial-btn" onClick={handlePredict} disabled={loading}>
                            {loading ? 'Analyzing...' : (t.analyze || 'Analyze')} <ChevronRight size={18} />
                        </button>
                    </div>

                    {/* Hero image */}
                    <div className="sentinel-card editorial-card"
                        style={{ padding: 0, overflow: 'hidden', border: 'none', background: 'transparent' }}>
                        <img src={heroImage} alt="Farm Analysis"
                            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '12px' }} />
                    </div>
                </div>
            </main>
        </div>
    );
}

export default MainTool;
