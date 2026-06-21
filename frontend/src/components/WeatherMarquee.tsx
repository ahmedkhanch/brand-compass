"use client";

import { useEffect, useState } from "react";

const PARIS_LAT = 48.8566;
const PARIS_LON = 2.3522;
const WEATHER_URL = `https://api.open-meteo.com/v1/forecast?latitude=${PARIS_LAT}&longitude=${PARIS_LON}&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto`;
const SCROLL_DURATION_S = 40;

const WEATHER_CODE_LABEL: Record<number, string> = {
  0: "Ciel dégagé",
  1: "Principalement clair",
  2: "Partiellement nuageux",
  3: "Couvert",
  45: "Brouillard",
  48: "Brouillard givrant",
  51: "Bruine légère",
  53: "Bruine",
  55: "Bruine dense",
  61: "Pluie légère",
  63: "Pluie",
  65: "Pluie forte",
  71: "Neige légère",
  73: "Neige",
  75: "Neige forte",
  80: "Averses",
  81: "Averses fortes",
  82: "Averses violentes",
  95: "Orage",
  96: "Orage avec grêle",
  99: "Orage violent",
};

type Forecast = {
  label: string;
  temp: number;
  min: number;
  max: number;
  wind: number;
};

export default function WeatherMarquee() {
  const [data, setData] = useState<Forecast | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(WEATHER_URL)
      .then((r) => r.json())
      .then((j) => {
        if (cancelled) return;
        setData({
          label: WEATHER_CODE_LABEL[j.current?.weather_code] ?? "Météo",
          temp: Math.round(j.current?.temperature_2m),
          min: Math.round(j.daily?.temperature_2m_min?.[0]),
          max: Math.round(j.daily?.temperature_2m_max?.[0]),
          wind: Math.round(j.current?.wind_speed_10m),
        });
      })
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
    };
  }, []);

  const message = error
    ? "Météo indisponible pour le moment."
    : data
      ? `Paris — ${data.label} · ${data.temp}°C (min ${data.min}° / max ${data.max}°) · Vent ${data.wind} km/h`
      : "Chargement de la météo…";

  const segment = ` ${message}  •  `;

  return (
    <div className="w-full overflow-hidden bg-slate-900 text-slate-100 text-sm border-b border-slate-800">
      <div
        className="whitespace-nowrap py-1.5 animate-[weather-scroll_var(--weather-duration)_linear_infinite]"
        style={
          {
            "--weather-duration": `${SCROLL_DURATION_S}s`,
          } as React.CSSProperties
        }
      >
        <span>{segment.repeat(8)}</span>
      </div>
      <style jsx>{`
        @keyframes weather-scroll {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
