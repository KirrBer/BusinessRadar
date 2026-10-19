"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import dynamic from "next/dynamic";

import type { DistrictCollection, DistrictProperties } from "../lib/districts";

const DistrictMap = dynamic(() => import("./DistrictMap"), { ssr: false });

type Features = {
  lat: number; lon: number; traffic: number; pop_density: number; competitors: number;
  avg_check: number; peak_factor: number; income_area: number; rent_cost: number;
};
type Prediction = {
  score: number; demand_forecast: number; demand_percentile: number;
  cluster_name: string; recommendation_text: string;
};
type District = DistrictProperties;
type Saved = { id: number; name: string; district: string | null; features: Features; result: Prediction; tag?: string; time?: string };
type Field = {
  group: "point" | "area"; key: keyof Features; label: string; unit: string;
  min: number; max: number; step: number; hint: string;
};

const FIELDS: Field[] = [
  { group: "point", key: "avg_check", label: "Средний чек", unit: "₽", min: 200, max: 2000, step: 10, hint: "Ожидаемый чек в вашем формате." },
  { group: "point", key: "peak_factor", label: "Пиковость потока", unit: "0–1", min: 0, max: 1, step: 0.05, hint: "0 — поток ровный, 1 — почти всё приходится на час пик." },
  { group: "area", key: "traffic", label: "Пешеходный трафик", unit: "чел./час", min: 50, max: 1500, step: 10, hint: "Сколько людей проходит мимо точки в среднем за час." },
  { group: "area", key: "pop_density", label: "Плотность населения", unit: "усл. ед.", min: 30, max: 400, step: 5, hint: "Жилая плотность вокруг точки. Типичное значение около 140." },
  { group: "area", key: "competitors", label: "Конкуренты рядом", unit: "шт.", min: 0, max: 12, step: 1, hint: "Заведения вашей ниши рядом с точкой." },
  { group: "area", key: "income_area", label: "Платёжеспособность района", unit: "индекс", min: 0.2, max: 1.8, step: 0.05, hint: "1,0 соответствует среднему уровню по городу." },
  { group: "area", key: "rent_cost", label: "Стоимость аренды", unit: "индекс", min: 0.05, max: 1, step: 0.05, hint: "1 соответствует самой дорогой аренде в городе." },
];

const QUANTILES = [14.18, 23.21, 25.59, 26.97, 27.79, 28.65, 29.38, 30.01, 30.64, 31.13, 31.7, 32.21, 32.69, 33.21, 33.62, 34.14, 34.58, 35.01, 35.34, 35.71, 36.14, 36.48, 36.88, 37.19, 37.52, 37.81, 38.15, 38.45, 38.82, 39.18, 39.49, 39.84, 40.23, 40.54, 40.81, 41.05, 41.37, 41.73, 41.99, 42.28, 42.56, 42.84, 43.07, 43.41, 43.67, 43.96, 44.2, 44.5, 44.76, 45.05, 45.37, 45.61, 45.88, 46.13, 46.42, 46.73, 47.1, 47.38, 47.75, 48.09, 48.4, 48.75, 49.07, 49.37, 49.76, 50.13, 50.53, 51, 51.36, 51.79, 52.24, 52.71, 53.16, 53.69, 54.21, 54.61, 55.18, 55.8, 56.35, 56.72, 57.48, 58.13, 58.77, 59.44, 60.16, 60.77, 61.47, 62.43, 63.11, 64.07, 64.82, 66.04, 67.09, 68.36, 69.7, 71.08, 72.95, 75.45, 77.93, 82.99, 124.16];
const DEFAULT_POINT = { avg_check: 650, peak_factor: 0.3 };
const DEMO_BENCHMARKS = { pop_density: 205, income_area: 1.01, traffic: 470 };
const numberFormat = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 });
const format = (value: number) => numberFormat.format(value);
const districtFor = (districts: District[], id: string | null) => districts.find((district) => district.id === id);

function featuresFor(district: District, point = DEFAULT_POINT): Features {
  return {
    lat: district.center.lat,
    lon: district.center.lon,
    traffic: district.traffic,
    pop_density: district.pop_density,
    competitors: district.competitors,
    income_area: district.income_area,
    rent_cost: district.rent_cost,
    ...point,
  };
}

function demoPredict(features: Features): Prediction {
  const demand = Math.exp(0.45 * Math.log1p(features.traffic) + 0.25 * Math.log1p(features.pop_density) + 0.15 * features.income_area + 0.1 * features.peak_factor - 0.2 * Math.log1p(features.competitors) + 0.05 * features.avg_check / 1000);
  let low = 0;
  let high = QUANTILES.length;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (QUANTILES[middle] < demand) low = middle + 1;
    else high = middle;
  }
  const percentile = low / QUANTILES.length;
  const score = Math.max(1, Math.min(10, Math.round(percentile * 9 + 1)));
  const cluster = `${features.pop_density > DEMO_BENCHMARKS.pop_density ? "плотный" : "спальный"}·${features.income_area > DEMO_BENCHMARKS.income_area ? "платёж." : "эконом"}·${features.traffic > DEMO_BENCHMARKS.traffic ? "трафик." : "локальный"}`;
  const demandBand = percentile >= 0.7 ? "высокий" : percentile >= 0.35 ? "средний" : "низкий";
  const competition = features.competitors >= 5 ? "много" : features.competitors >= 2 ? "умеренно" : "мало";
  const advice = percentile >= 0.7
    ? features.competitors >= 5 ? "Спрос высокий, но конкуренция плотная — нужен уникальный формат." : "Спрос высокий — сильная локация, можно захватывать поток."
    : percentile < 0.35
      ? "Спрос низкий. Проверьте экономику и стоимость аренды до открытия."
      : "Спрос умеренный — решение зависит от юнит-экономики и текущей аренды.";
  const rentNote = features.rent_cost > 0.66 ? " Высокая аренда давит на маржу." : "";
  return {
    score,
    demand_forecast: Math.round(demand * 100) / 100,
    demand_percentile: Math.round(percentile * 1000) / 1000,
    cluster_name: cluster,
    recommendation_text: `Скоринг ${score}/10 (${demandBand} спрос, конкурентов ${competition}). ${advice}${rentNote} Район: «${cluster}».`,
  };
}

async function predict(features: Features, url: string, signal?: AbortSignal): Promise<Prediction> {
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(features), signal });
  if (!response.ok) {
    if (response.status === 503) throw new Error("Модели недоступны. Пересоберите backend-образ, чтобы обучить их.");
    if (response.status === 422) throw new Error("API отклонил параметры. Проверьте значения полей.");
    throw new Error(`API вернул ошибку ${response.status}.`);
  }
  return response.json() as Promise<Prediction>;
}

function scoreLevel(score: number) { return score >= 7 ? "good" : score >= 4 ? "warn" : "bad"; }
function verdict(score: number) { return score >= 7 ? "Высокий потенциал" : score >= 4 ? "Средний потенциал" : "Низкий потенциал"; }
function prettyCluster(name: string) {
  const labels: Record<string, string> = { плотный: "Плотный", спальный: "Спальный", "платёж.": "платёжеспособный", эконом: "эконом-сегмент", "трафик.": "проходной", локальный: "локальный" };
  return name.split("·").map((part) => labels[part.trim()] ?? part.trim()).join(" · ");
}
function gaugeArc(radius: number, start: number, end: number) {
  const point = (degrees: number) => {
    const radians = degrees * Math.PI / 180;
    return `${(150 + radius * Math.cos(radians)).toFixed(2)} ${(150 + radius * Math.sin(radians)).toFixed(2)}`;
  };
  return `M${point(start)} A${radius} ${radius} 0 0 1 ${point(end)}`;
}

const initialFeatures: Features = {
  lat: 59.934, lon: 30.335, traffic: 520, pop_density: 250, competitors: 4,
  avg_check: DEFAULT_POINT.avg_check, peak_factor: DEFAULT_POINT.peak_factor,
  income_area: 1, rent_cost: 0.65,
};

export default function Home() {
  const [features, setFeatures] = useState(initialFeatures);
  const [districtData, setDistrictData] = useState<DistrictCollection | null>(null);
  const [districts, setDistricts] = useState<District[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);
  const [mode, setMode] = useState<"demo" | "api">("demo");
  const [apiUrl, setApiUrl] = useState("/api/v1/predict");
  const [result, setResult] = useState<Prediction | null>(() => demoPredict(initialFeatures));
  const [heat, setHeat] = useState<Record<string, number>>({});
  const [saved, setSaved] = useState<Saved[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");
  const nextId = useRef(1);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/v1/districts", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Не удалось загрузить районы города.");
        return response.json() as Promise<DistrictCollection>;
      })
      .then((data) => {
        const districtFeatures = data.features.map((feature) => feature.properties);
        const central = districtFeatures.find((district) => district.id === "cen") ?? districtFeatures[0];
        if (!central) throw new Error("В наборе геоданных нет районов.");
        setDistrictData(data);
        setDistricts(districtFeatures);
        setSelectedDistrict(central.id);
        setFeatures(featuresFor(central, DEFAULT_POINT));
        setHeat(Object.fromEntries(districtFeatures.map((district) => [district.id, demoPredict(featuresFor(district)).score])));
        setSaved(["cen", "pet", "mos"].flatMap((id, index) => {
          const district = districtFeatures.find((item) => item.id === id);
          if (!district) return [];
          const features = featuresFor(district);
          return [{ id: index + 1, name: district.name, district: id, features, result: demoPredict(features), tag: "пример" }];
        }));
        nextId.current = 4;
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Не удалось загрузить районы.");
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    let active = true; const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(mode === "api"); setError("");
      try {
        const next = mode === "api" ? await predict(features, apiUrl, controller.signal) : demoPredict(features);
        if (active) setResult(next);
      } catch (cause) {
        if (active && !(cause instanceof DOMException && cause.name === "AbortError")) setError(cause instanceof Error ? cause.message : "Не удалось выполнить расчёт.");
      } finally { if (active) setLoading(false); }
    }, mode === "api" ? 350 : 100);
    return () => { active = false; clearTimeout(timer); controller.abort(); };
  }, [features, mode, apiUrl]);

  useEffect(() => {
    if (!districts.length) return;
    let active = true; const controller = new AbortController();
    const timer = setTimeout(async () => {
      const base = { avg_check: features.avg_check, peak_factor: features.peak_factor };
      try {
        const scores = await Promise.all(districts.map(async (district) => {
          const current = featuresFor(district, base);
          const value = mode === "api" ? await predict(current, apiUrl, controller.signal) : demoPredict(current);
          return [district.id, value.score] as const;
        }));
        if (active) setHeat(Object.fromEntries(scores));
      } catch { if (active) setHeat({}); }
    }, mode === "api" ? 450 : 120);
    return () => { active = false; clearTimeout(timer); controller.abort(); };
  }, [districts, features.avg_check, features.peak_factor, mode, apiUrl]);

  useEffect(() => () => { if (toastTimer.current) clearTimeout(toastTimer.current); }, []);

  function notify(message: string) {
    setToast(message); if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 2600);
  }
  function chooseDistrict(id: string) {
    const district = districtFor(districts, id); if (!district) return;
    setSelectedDistrict(id);
    setFeatures((current) => featuresFor(district, { avg_check: current.avg_check, peak_factor: current.peak_factor }));
  }
  function reset() {
    const district = districtFor(districts, "cen") ?? districts[0];
    if (!district) return;
    chooseDistrict(district.id);
    setFeatures(featuresFor(district, DEFAULT_POINT));
  }
  function saveCalculation() {
    if (!result || loading || error) return;
    const district = districtFor(districts, selectedDistrict); const name = district?.name ?? `Своя точка ${nextId.current - 3}`;
    const time = new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
    setSaved((current) => [{ id: nextId.current++, name, district: selectedDistrict, features: { ...features }, result: { ...result }, time }, ...current]);
    notify(`Расчёт сохранён: ${name}`);
  }
  function openSaved(item: Saved) {
    setFeatures({ ...item.features }); setSelectedDistrict(item.district);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const selected = districtFor(districts, selectedDistrict);
  const ranked = districts.filter((district) => typeof heat[district.id] === "number").sort((a, b) => (heat[b.id] ?? 0) - (heat[a.id] ?? 0)).slice(0, 3);
  const percentile = result ? Math.round(result.demand_percentile * 100) : 0;
  const currentLevel = result ? scoreLevel(result.score) : "warn";

  return (
    <main className="page">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Бизнес-Радар, главная">
          <svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" strokeWidth="2" /><circle cx="18" cy="18" r="9" fill="none" stroke="currentColor" strokeWidth="1.5" opacity=".65" /><path d="M18 18 18 2a16 16 0 0 1 13.8 7.9Z" fill="currentColor" opacity=".28" /><circle cx="24.5" cy="11.5" r="2.3" fill="currentColor" /></svg>
          <span>Бизнес-Радар</span>
        </a>
        <div className="mode-control" role="group" aria-label="Источник расчёта">
          <button type="button" aria-pressed={mode === "demo"} onClick={() => setMode("demo")}>Демо</button>
          <button type="button" aria-pressed={mode === "api"} onClick={() => setMode("api")}>API</button>
        </div>
      </header>

      {mode === "api" && <div className="api-row"><label htmlFor="api-url">Адрес метода</label><input id="api-url" value={apiUrl} onChange={(event) => setApiUrl(event.target.value)} spellCheck={false} /><p>POST-запрос к модели проекта. Через Nginx адрес работает без дополнительных настроек.</p></div>}
      <section className="intro" id="top"><p className="eyebrow">АНАЛИТИКА ЛОКАЦИЙ · САНКТ-ПЕТЕРБУРГ</p><h1>Выберите район для новой точки</h1><p>Оцените потенциал места по спросу, окружению и экономике. Выберите район на карте или уточните параметры вручную.</p></section>
      <nav className="tabs" aria-label="Задачи сервиса"><button className="tab active" type="button" aria-current="page">Где открыть точку</button><button className="tab" type="button" disabled>Прогноз спроса <span>скоро</span></button><button className="tab" type="button" disabled>Ассортимент <span>скоро</span></button></nav>

      <div className="dashboard-grid">
        <section className="panel map-panel" aria-labelledby="map-title">
          <div className="panel-heading"><h2 className="section-label" id="map-title">Районы города</h2><div className="legend" aria-hidden="true"><span>НИЖЕ</span><i /><span>ВЫШЕ</span></div></div>
          <div className="map-frame">
            {districtData ? <DistrictMap data={districtData} selectedId={selectedDistrict} scores={heat} onSelect={chooseDistrict} /> : <div className="map-loading">Загружаем карту районов Санкт-Петербурга…</div>}
          </div>
          <p className="picked" aria-live="polite">{selected ? <>Выбрано: <strong>{selected.name}</strong></> : "Своя точка"}</p>
          <div className="top-districts"><h3 className="section-label">Лучшие районы сейчас</h3><ol>{ranked.length ? ranked.map((district, index) => <li key={district.id}><button type="button" onClick={() => chooseDistrict(district.id)}><span>{index + 1}</span>{district.name.replace(" округ", "")}<b>{heat[district.id]}/10</b></button></li>) : <li className="muted">Оценки районов недоступны.</li>}</ol></div>
          <p className="map-note">Границы районов: OpenStreetMap, ODbL 1.0. Оценки спроса и показатели районов в демо-режиме синтетические.</p>
        </section>

        <section className="panel parameters-panel" aria-labelledby="form-title">
          <h2 className="section-label" id="form-title">Параметры точки</h2>
          <div className="field-groups">{(["point", "area"] as const).map((group) => <div className="field-group" key={group}>
            <div><h3 className="section-label">{group === "point" ? "О вашей точке" : "Об окружении"}</h3><p className="group-subtitle">{group === "point" ? "Эти параметры задаёте вы." : "Подставлены по району, их можно уточнить."}</p></div>
            {FIELDS.filter((field) => field.group === group).map((field) => {
              const value = features[field.key]; const progress = (value - field.min) / (field.max - field.min) * 100;
              return <div className="field" key={field.key}><div className="field-heading"><label htmlFor={`field-${field.key}`}>{field.label}</label><output htmlFor={`field-${field.key}`}>{format(value)} <small>{field.unit}</small></output></div>
                <input className="range" id={`field-${field.key}`} type="range" min={field.min} max={field.max} step={field.step} value={value} style={{ "--range-progress": `${progress}%` } as CSSProperties} onChange={(event) => setFeatures((current) => ({ ...current, [field.key]: Number(event.target.value) }))} />
                <p className="field-hint">{field.hint}</p></div>;
            })}
          </div>)}</div>
        </section>

        <section className="panel result-panel" aria-labelledby="result-title">
          <div className="result-heading"><h2 className="section-label" id="result-title">Оценка локации</h2><span className="source-badge">{mode === "api" ? "ответ API" : "демо-расчёт"}</span></div>
          {error && <p className="error-message" role="alert">{error}</p>}
          <div className="gauge-wrap" aria-busy={loading}>
            <svg className="gauge" viewBox="0 0 300 300" role="img" aria-label={result ? `Оценка локации: ${result.score} из 10` : "Расчёт оценки локации"} data-level={currentLevel}>
              <defs><linearGradient id="sweep-grad" x1="73" y1="86" x2="150" y2="50" gradientUnits="userSpaceOnUse"><stop offset="0" stopColor="var(--accent)" stopOpacity="0" /><stop offset="1" stopColor="var(--accent)" stopOpacity=".3" /></linearGradient></defs>
              <circle className="gauge-ring" cx="150" cy="150" r="96" /><circle className="gauge-ring" cx="150" cy="150" r="66" /><circle className="gauge-ring" cx="150" cy="150" r="36" /><path className="gauge-cross" d="M54 150h192M150 54v192" />
              <g className="sweep"><path d="M150 150 73 86a100 100 0 0 1 77-36Z" fill="url(#sweep-grad)" /><path d="M150 150V50" stroke="var(--accent)" opacity=".7" /></g>
              {Array.from({ length: 10 }, (_, index) => { const start = -90 + index * 36 + 4; return <path key={index} className={`gauge-segment${result && index < result.score ? " on" : ""}`} d={gaugeArc(122, start, start + 28)} />; })}
              <text className="gauge-score" x="150" y="170">{result?.score ?? "–"}</text><text className="gauge-of" x="150" y="196">ИЗ 10</text>
            </svg>
            <p className="verdict" data-level={currentLevel} aria-live="polite">{loading ? "Обновляем расчёт…" : result ? verdict(result.score) : "Ожидание данных"}</p>
          </div>
          <dl className="metrics">
            <div><dt>Прогноз спроса</dt><dd className="metric-value">{result ? format(result.demand_forecast) : "–"}<small>усл. ед.</small></dd><dd className="metric-sub">Единицы тестовой модели, не выручка.</dd></div>
            <div><dt>Тип района</dt><dd className="district-value">{result ? prettyCluster(result.cluster_name) : "–"}</dd><dd className="metric-sub">Группа, к которой модель отнесла точку.</dd></div>
          </dl>
          <div className="percentile"><span className="section-label">Место среди типовых локаций</span><div className="percentile-track" aria-hidden="true"><div className="percentile-fill" style={{ width: `${percentile}%` }} /><i style={{ left: `${percentile}%` }} /></div><div className="percentile-scale"><span>0</span><span>50</span><span>100</span></div><p>Спрос выше, чем у {percentile}% типовых локаций.</p></div>
          <div className="recommendation"><h3 className="section-label">Что это значит</h3><p>{result?.recommendation_text ?? "Рекомендация появится после расчёта."}</p></div>
          <div className="actions"><button className="button primary" type="button" onClick={saveCalculation} disabled={!result || loading || Boolean(error)}>Сохранить расчёт</button><button className="button" type="button" onClick={reset}>Сбросить параметры</button></div>
        </section>
      </div>

      <section className="saved-section" aria-labelledby="saved-title"><div className="saved-heading"><h2 id="saved-title">Сохранённые расчёты</h2><span>{saved.length} вариантов</span></div><ul className="saved-list">
        {!saved.length ? <li className="saved-empty">Сохранённых расчётов пока нет. Выберите район и сохраните результат.</li> : saved.map((item) => {
          const best = saved.length > 1 && item.result.score === Math.max(...saved.map((entry) => entry.result.score));
          return <li className="saved-row" key={item.id}><div className="saved-name"><strong>{item.name}</strong>{item.tag && <span className="tag">{item.tag}</span>}{best && <span className="tag best">лучший балл</span>}<small>трафик {format(item.features.traffic)} · конкурентов {format(item.features.competitors)} · аренда {format(item.features.rent_cost)}{item.time ? ` · ${item.time}` : ""}</small></div>
            <span className={`saved-score ${scoreLevel(item.result.score)}`}>{item.result.score}<small>/10</small></span><span className="saved-forecast">{format(item.result.demand_forecast)} усл. ед.</span>
            <div className="saved-actions"><button type="button" onClick={() => openSaved(item)}>Открыть</button><button type="button" aria-label={`Удалить расчёт ${item.name}`} onClick={() => setSaved((current) => current.filter((entry) => entry.id !== item.id))}>Удалить</button></div></li>;
        })}
      </ul></section>

      <section className="next-step"><div><h2>Следующий шаг</h2><p>Нашли подходящее место? Рассчитайте кредит на открытие или подключите приём карт.</p></div><div className="actions"><button className="button primary" type="button" onClick={() => notify("Здесь откроется раздел расчёта кредита.")}>Рассчитать кредит</button><button className="button" type="button" onClick={() => notify("Здесь откроется подключение эквайринга.")}>Подключить эквайринг</button></div></section>
      <p className="footnote">Демо-режим использует синтетическую формулу проекта. Типовые оценки районов приведены для примера; подключите API, чтобы получить расчёт ML-моделей. Метрики не основаны на актуальных данных карт или транзакций.</p>
      {toast && <div className="toast" role="status">{toast}</div>}
    </main>
  );
}
