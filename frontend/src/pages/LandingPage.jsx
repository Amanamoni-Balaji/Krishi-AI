import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Play, Globe } from 'lucide-react';
import './LandingPage.css';
import heroImage from '../assets/hero_new.jpg';
import { translations } from '../utils/translations';

const LandingPage = ({ language, setLanguage }) => {
    const navigate = useNavigate();
    const t = translations[language] || translations['en'];

    return (
        <div className="landing-container-editorial">
            {/* Background Grid Lines */}
            <div className="grid-lines">
                <div className="line"></div>
                <div className="line"></div>
                <div className="line"></div>
                <div className="line"></div>
            </div>

            {/* Header */}
            <nav className="editorial-nav">
                <div className="nav-left">
                    <span className="brand-name">{t.brand}</span>
                </div>
                <div className="nav-center">
                    <span>06:04:02</span>
                    <span className="separator">|</span>
                    <span>Meghalaya</span>
                </div>
                <div className="nav-right" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <div className="lang-selector" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Globe size={16} color="#1A3C34" />
                        <select
                            value={language}
                            onChange={(e) => setLanguage(e.target.value)}
                            style={{ border: 'none', background: 'transparent', fontSize: '0.9rem', color: '#1A3C34', cursor: 'pointer', fontFamily: 'inherit' }}
                        >
                            <option value="en">English</option>
                            <option value="hi">हिंदी</option>
                            <option value="kha">Khasi</option>
                        </select>
                    </div>
                    <a href="#about">{t.about}</a>
                    <a href="#product">{t.product}</a>
                    <a href="/mlops" style={{ fontWeight: 700, color: '#1A3C34', background: 'rgba(212,240,88,0.35)', padding: '0.25rem 0.75rem', borderRadius: '6px', textDecoration: 'none', fontSize: '0.85rem' }}>MLOps</a>
                </div>
            </nav>

            {/* Main Hero Content */}
            <header className="editorial-hero">
                <div className="hero-text-wrapper">
                    <motion.h1
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        className="main-headline"
                    >
                        {t.sowing_seeds} <span className="italic-accent">{t.of_sustainability}</span>
                    </motion.h1>

                    <div className="hero-sub-elements">
                        <motion.button
                            className="editorial-cta"
                            onClick={() => navigate('/app')}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            {t.get_started} <div className="btn-icon"><ArrowRight size={16} /></div>
                        </motion.button>

                        <div className="small-image-inset">
                            <img src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?q=80&w=1740&auto=format&fit=crop" alt="Soil detail" />
                        </div>
                    </div>
                </div>

                {/* Large Farmer Image (Absolute Positioned) */}
                <motion.div
                    className="hero-image-container"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1, delay: 0.2 }}
                >
                    <img src={heroImage} alt="Smiling Farmer" className="main-farmer-img" />
                </motion.div>

                {/* Floating Card (Benedict Pedro style) */}
                <motion.div
                    className="floating-feature-card"
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8, delay: 0.5 }}
                >
                    <div className="feature-img-box">
                        <img src="https://images.unsplash.com/photo-1500937386664-56d1dfef3854?q=80&w=1740&auto=format&fit=crop" alt="Field" />
                    </div>
                    <div className="feature-content">
                        <div>
                            <span className="feature-label">{t.smart_farming}</span>
                            <h3>{t.yield_prediction}</h3>
                        </div>
                        <button className="play-btn"><Play size={16} fill="currentColor" /></button>
                    </div>
                </motion.div>
            </header>

            {/* Footer / Bottom Text */}
            <div className="hero-footer-text">
                <motion.h2
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.8 }}
                >
                    {t.innovative_solutions} <br /> {t.to_feed_world}
                </motion.h2>
            </div>
        </div>
    );
};

export default LandingPage;
