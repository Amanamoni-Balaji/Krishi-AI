// District slopes match the uppercase names used in the model/backend
const DISTRICT_SLOPES = {
    "EAST KHASI HILLS":      { slope: "Steep",  degrees: 28 },
    "WEST KHASI HILLS":      { slope: "Steep",  degrees: 26 },
    "SOUTH WEST KHASI HILLS":{ slope: "Steep",  degrees: 30 },
    "EAST JAINTIA HILLS":    { slope: "Steep",  degrees: 24 },
    "WEST JAINTIA HILLS":    { slope: "Steep",  degrees: 22 },
    "EAST GARO HILLS":       { slope: "Gentle", degrees: 12 },
    "WEST GARO HILLS":       { slope: "Gentle", degrees: 10 },
    "NORTH GARO HILLS":      { slope: "Gentle", degrees: 8  },
    "SOUTH GARO HILLS":      { slope: "Steep",  degrees: 20 },
    "SOUTH WEST GARO HILLS": { slope: "Gentle", degrees: 9  },
    "RI BHOI":               { slope: "Gentle", degrees: 11 },
};

export const getSlopeFromDistrict = (district) => {
    const info = DISTRICT_SLOPES[district];
    return info ? info.slope : "Gentle";
};

export const getSlopeDegreesFromDistrict = (district) => {
    const info = DISTRICT_SLOPES[district];
    return info ? info.degrees : 10;
};

export const calculateErosionRisk = (slope, rainfall) => {
    if (slope === "Steep") {
        if (rainfall > 200) return { risk: "High",     percentage: 85, color: "#ef4444" };
        if (rainfall > 100) return { risk: "Moderate", percentage: 60, color: "#f59e0b" };
        return                      { risk: "Low",      percentage: 30, color: "#10b981" };
    } else if (slope === "Gentle") {
        if (rainfall > 250) return { risk: "Moderate", percentage: 45, color: "#f59e0b" };
        return                      { risk: "Low",      percentage: 18, color: "#10b981" };
    } else {
        if (rainfall > 300) return { risk: "Low",      percentage: 15, color: "#10b981" };
        return                      { risk: "Minimal",  percentage: 5,  color: "#10b981" };
    }
};

export const fetchWeatherForecast = async (lat, lon) => {
    try {
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
            `&daily=temperature_2m_max,precipitation_sum,wind_speed_10m_max,relative_humidity_2m_max` +
            `&timezone=auto&forecast_days=14`;
        const response = await fetch(url);
        const data     = await response.json();
        const daily    = data.daily;

        return daily.time.map((date, i) => ({
            date,
            temp:     daily.temperature_2m_max[i],
            rain:     daily.precipitation_sum[i] || 0,
            wind:     daily.wind_speed_10m_max[i] || 0,
            humidity: daily.relative_humidity_2m_max
                ? (daily.relative_humidity_2m_max[i] || 70)
                : 70,
        }));
    } catch (error) {
        console.error("Error fetching weather from Open-Meteo:", error);
        return [];
    }
};
