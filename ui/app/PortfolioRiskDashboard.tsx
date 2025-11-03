"use client";

import React, { useState, useEffect } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Treemap } from "recharts";
import { ChevronDown, ChevronUp } from "lucide-react";

const SECTOR_COLORS: Record<string, string> = {
  "Information Technology": "#3b82f6",
  "Communication Services": "#14b8a6",
  Healthcare: "#ef4444",
  Financials: "#10b981",
  "Consumer Discretionary": "#f59e0b",
  Industrials: "#8b5cf6",
  Energy: "#ec4899",
  Materials: "#06b6d4",
  "Consumer Staples": "#84cc16",
  Utilities: "#f97316",
  "Real Estate": "#6366f1",
};

const getRiskColor = (risk: number): string => {
  const clampedRisk = Math.max(-1, Math.min(1, risk));

  if (clampedRisk < 0) {
    const intensity = Math.abs(clampedRisk);
    const r = 255;
    const g = Math.round(255 * (1 - intensity));
    const b = Math.round(255 * (1 - intensity));
    return `rgb(${r}, ${g}, ${b})`;
  } else {
    const intensity = clampedRisk;
    const r = Math.round(255 * (1 - intensity));
    const g = 255;
    const b = Math.round(255 * (1 - intensity));
    return `rgb(${r}, ${g}, ${b})`;
  }
};

const CustomTreemapContent = ({
  x,
  y,
  width,
  height,
  name,
  value,
  riskIndex,
  onClick,
}: any) => {
  if (width < 30 || height < 20) return null;

  const bgColor = getRiskColor(riskIndex || 0);
  const risk = riskIndex || 0;

  const getTextColor = () => {
    if (risk < -0.5 || risk > 0.5) return "#fff";
    return "#000";
  };

  return (
    <g onClick={onClick} style={{ cursor: "pointer" }}>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={bgColor}
        stroke="#fff"
        strokeWidth={2}
      />
      {width > 60 && height > 30 && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 5}
            textAnchor="middle"
            fill={getTextColor()}
            fontSize={14}
            fontWeight="bold"
          >
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 12}
            textAnchor="middle"
            fill={getTextColor()}
            fontSize={11}
          >
            Risk: {risk.toFixed(2)}
          </text>
        </>
      )}
    </g>
  );
};

interface Company {
  ticker: string;
  company: string;
  gics_sector: string;
  weight: string;
}

interface Analysis {
  DirectRiskFactor: number;
  IndirectRiskFactor: number;
  TimeFactor: number;
  Summary: string;
  SummaryKeypoints: string[];
}

interface Props {
  initialData: {
    company_details: Company[];
  };
  initialAnalysis: Record<string, Analysis>;
}

interface PortfolioDataItem {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

interface Stock {
  ticker: string;
  company: string;
  riskIndex: number;
  exposureValue: number;
  directRisk: number;
  indirectRisk: number;
  timeFactor: number;
}

interface SummaryItem {
  ticker: string;
  summary: string;
  keypoints: string[];
}

export function PortfolioRiskDashboard({
  initialData,
  initialAnalysis,
}: Props) {
  const [activeSection, setActiveSection] = useState<string>("portfolio");
  const [hoveredSector, setHoveredSector] = useState<number | null>(null);
  const [sectorDropdownOpen, setSectorDropdownOpen] = useState<boolean>(false);
  const [tooltipVisible, setTooltipVisible] = useState<string | null>(null);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);

  const [portfolioData, setPortfolioData] = useState<PortfolioDataItem[]>([]);
  const [companyData, setCompanyData] = useState<Company[]>([]);
  const [analysisData, setAnalysisData] = useState<Record<string, Analysis>>({});
  const [sectors, setSectors] = useState<string[]>([]);

  useEffect(() => {
    if (initialData && initialAnalysis) {
      setCompanyData(initialData.company_details);
      setAnalysisData(initialAnalysis);

      const sectorMap: Record<string, number> = {};
      initialData.company_details.forEach((company) => {
        const sector = company.gics_sector;
        const weight = parseFloat(company.weight.replace(",", "."));
        if (!sectorMap[sector]) {
          sectorMap[sector] = 0;
        }
        sectorMap[sector] += weight;
      });

      const portfolioArray = Object.entries(sectorMap)
        .map(([name, value]) => ({
          name,
          value: value * 100,
          color: SECTOR_COLORS[name] || "#6b7280",
        }))
        .sort((a, b) => b.value - a.value);

      setPortfolioData(portfolioArray);
      setSectors(Object.keys(sectorMap).sort());
    }
  }, [initialData, initialAnalysis]);

  const getSectorStocks = (sector: string): Stock[] => {
    return companyData
      .filter((company) => company.gics_sector === sector)
      .map((company) => {
        const analysis = analysisData[company.ticker] || {
          DirectRiskFactor: 0,
          IndirectRiskFactor: 0,
          TimeFactor: 0,
          Summary: '',
          SummaryKeypoints: []
        };

        const weight = parseFloat(company.weight.replace(",", "."));
        const riskIndex =
          ((analysis.DirectRiskFactor + analysis.IndirectRiskFactor) / 2) *
          analysis.TimeFactor;

        return {
          ticker: company.ticker,
          company: company.company,
          riskIndex: riskIndex,
          exposureValue: weight,
          directRisk: analysis.DirectRiskFactor,
          indirectRisk: analysis.IndirectRiskFactor,
          timeFactor: analysis.TimeFactor,
        };
      })
      .sort((a, b) => b.exposureValue - a.exposureValue);
  };

  const getTreemapData = (sector: string) => {
    const stocks = getSectorStocks(sector);
    return stocks.map((stock) => ({
      name: stock.ticker,
      size: stock.exposureValue * 100,
      riskIndex: stock.riskIndex,
      ticker: stock.ticker,
    }));
  };

  const getSectorSummary = (sector: string): SummaryItem[] => {
    const stocks = getSectorStocks(sector);
    const summaries = stocks
      .map((stock) => {
        const analysis = analysisData[stock.ticker];
        return analysis
          ? {
              ticker: stock.ticker,
              summary: analysis.Summary,
              keypoints: analysis.SummaryKeypoints || [],
            }
          : null;
      })
      .filter((item): item is SummaryItem => item !== null);

    return summaries;
  };

  const getCurrentSectorExposure = (sector: string): number => {
    const stocks = getSectorStocks(sector);
    let totalWeightedRisk = 0;
    let totalWeight = 0;
    
    stocks.forEach(stock => {
      totalWeightedRisk += stock.riskIndex * stock.exposureValue;
      totalWeight += stock.exposureValue;
    });
    
    return totalWeight > 0 ? totalWeightedRisk / totalWeight : 0;
  };

  const columnTooltips: Record<string, string> = {
    "Total Risk Index": "Composite score: (Direct + Indirect) / 2 × Time Factor",
    "Portfolio Weight": "Percentage of total portfolio allocated to this stock",
    "Direct Risk": "Direct regulatory impact on the company",
    "Indirect Risk": "Indirect impact through suppliers/subsidiaries",
    "Time Factor": "Recency of regulatory changes (higher = more recent)",
  };

  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-900">
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-zinc-800 border-r border-zinc-200/50 dark:border-zinc-700/50 flex flex-col">
        {/* Logo */}
        <div className="h-24 flex items-center justify-center border-b border-zinc-200/50 dark:border-zinc-700/50">
          <div className="inline-flex items-center justify-center bg-zinc-100 dark:bg-zinc-700/50 rounded text-zinc-400 dark:text-zinc-500 text-sm font-light p-2">
            <img src="/content.png" alt="Logo" className="h-16 w-auto" />
          </div>
        </div>

        {/* Menu */}
        <nav className="flex-1 p-4">
          <button
            onClick={() => setActiveSection("portfolio")}
            className={`w-full text-left px-4 py-2.5 rounded-lg mb-1 transition-all font-light ${
              activeSection === "portfolio"
                ? "bg-blue-500 text-white"
                : "hover:bg-zinc-50 dark:hover:bg-zinc-700/50 text-zinc-600 dark:text-zinc-400"
            }`}
          >
            Portfolio
          </button>

          {/* Sector Dropdown */}
          <div className="mt-2">
            <button
              onClick={() => setSectorDropdownOpen(!sectorDropdownOpen)}
              className="w-full flex items-center justify-between px-4 py-2.5 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-700/50 text-zinc-600 dark:text-zinc-400 font-light transition-all"
            >
              <span>Sectors</span>
              {sectorDropdownOpen ? (
                <ChevronUp size={18} />
              ) : (
                <ChevronDown size={18} />
              )}
            </button>
            {sectorDropdownOpen && (
              <div className="mt-1 ml-2 space-y-0.5">
                {sectors.map((sector) => (
                  <button
                    key={sector}
                    onClick={() => setActiveSection(sector)}
                    className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-all font-light ${
                      activeSection === sector
                        ? "bg-blue-500 text-white"
                        : "hover:bg-zinc-50 dark:hover:bg-zinc-700/50 text-zinc-500 dark:text-zinc-500"
                    }`}
                  >
                    {sector}
                  </button>
                ))}
              </div>
            )}
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-8">
        {activeSection === "portfolio" ? (
          <div className="max-w-4xl mx-auto">
            <h1 className="text-2xl font-light text-zinc-800 dark:text-white mb-8">
              Portfolio Overview
            </h1>
            <div className="bg-white dark:bg-zinc-800 rounded-lg p-8 relative">
              <ResponsiveContainer width="100%" height={550}>
                <PieChart>
                  <Pie
                    data={portfolioData}
                    cx="50%"
                    cy="35%"
                    innerRadius={90}
                    fill="#8884d8"
                    dataKey="value"
                    onMouseEnter={(_, index) => setHoveredSector(index)}
                    onMouseLeave={() => setHoveredSector(null)}
                    onClick={(data) => setActiveSection(data.name)}
                    className="cursor-pointer"
                    outerRadius={165}
                    animationDuration={800}
                    animationBegin={0}
                    isAnimationActive={true}
                    label={({
                      name,
                      value,
                      cx,
                      cy,
                      midAngle,
                      innerRadius,
                      outerRadius,
                      index,
                    }: any) => {
                      const RADIAN = Math.PI / 180;
                      const radius = Number(outerRadius) + 25;
                      const x =
                        Number(cx) +
                        radius * Math.cos(-Number(midAngle) * RADIAN);
                      const y =
                        Number(cy) +
                        radius * Math.sin(-Number(midAngle) * RADIAN);

                      return (
                        <text
                          x={x}
                          y={y}
                          fill="#52525b"
                          textAnchor={x > Number(cx) ? "start" : "end"}
                          dominantBaseline="central"
                          className="text-sm font-light"
                          style={{
                            opacity: hoveredSector !== null ? 0 : 1,
                            transition: "opacity 200ms ease-in-out",
                          }}
                        >
                          {`${Number(value).toFixed(1)}%`}
                        </text>
                      );
                    }}
                    labelLine={{
                      stroke: "#d4d4d8",
                      strokeWidth: 1,
                      style: {
                        opacity: hoveredSector !== null ? 0 : 1,
                        transition: "opacity 200ms ease-in-out",
                      },
                    }}
                  >
                    {portfolioData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        style={{
                          filter:
                            hoveredSector === index
                              ? "drop-shadow(0 6px 16px rgba(0, 0, 0, 0.12))"
                              : "drop-shadow(0 2px 4px rgba(0, 0, 0, 0.06))",
                          transform:
                            hoveredSector === index
                              ? "scale(1.05)"
                              : "scale(1)",
                          transformOrigin: "center",
                          transition: "all 0.2s ease",
                        }}
                      />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>

              {/* Custom Legend */}
              <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-white/80 dark:bg-zinc-800/80 backdrop-blur-sm border border-zinc-200/50 dark:border-zinc-700/50 rounded-lg px-4 py-2.5 shadow-sm max-w-2xl">
                <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
                  {portfolioData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: entry.color }}
                      ></div>
                      <span className="text-zinc-600 dark:text-zinc-400 whitespace-nowrap font-light">
                        {entry.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-7xl mx-auto">
            <h1 className="text-2xl font-light text-zinc-800 dark:text-white mb-1">
              {activeSection}
            </h1>
            <p className="text-zinc-500 dark:text-zinc-500 mb-6 text-sm font-light">
              Sector composition and risk analysis
            </p>

            {/* Treemap */}
            <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 mb-6">
              <h2 className="text-lg font-light text-zinc-800 dark:text-white mb-4">
                Stock Composition
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <Treemap
                  data={getTreemapData(activeSection)}
                  dataKey="size"
                  stroke="#fff"
                  content={(props) => (
                    <CustomTreemapContent
                      {...props}
                      onClick={() => setSelectedStock(props.name)}
                    />
                  )}
                />
              </ResponsiveContainer>
              <div className="flex items-center gap-6 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: getRiskColor(-1) }}
                  ></div>
                  <span className="text-zinc-600 dark:text-zinc-400">
                    High Negative Risk (-1)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: getRiskColor(0) }}
                  ></div>
                  <span className="text-zinc-600 dark:text-zinc-400">
                    Neutral (0)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: getRiskColor(1) }}
                  ></div>
                  <span className="text-zinc-600 dark:text-zinc-400">
                    High Positive Risk (1)
                  </span>
                </div>
              </div>
            </div>

            {/* Bottom Section */}
            <div className="grid grid-cols-3 gap-6" style={{ height: "60vh" }}>
              {/* Left Column - AI Overview + Sector Exposure */}
              <div className="col-span-1 flex flex-col gap-6">
                {/* AI Overview */}
                <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 overflow-auto" style={{ maxHeight: "45vh" }}>
                  <h2 className="text-lg font-light text-zinc-800 dark:text-white mb-4">
                    AI Analysis
                  </h2>
                  {selectedStock ? (
                    <div className="text-zinc-500 dark:text-zinc-500 space-y-4 text-sm font-light">
                      {getSectorSummary(activeSection)
                        .filter((item) => item.ticker === selectedStock)
                        .map((item, idx) => (
                          <div key={idx}>
                            <div className="flex items-center justify-between mb-3">
                              <div className="font-mono font-medium text-zinc-700 dark:text-white text-lg">
                                {item.ticker}
                              </div>
                              <button
                                onClick={() => setSelectedStock(null)}
                                className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 text-xs"
                              >
                                Clear
                              </button>
                            </div>
                            <p className="mb-4 text-sm leading-relaxed">
                              {item.summary}
                            </p>
                            {item.keypoints.length > 0 && (
                              <div>
                                <h3 className="font-medium text-zinc-700 dark:text-white mb-2 text-sm">
                                  Key Points:
                                </h3>
                                <ul className="space-y-2 text-sm">
                                  {item.keypoints.map((point, pidx) => (
                                    <li
                                      key={pidx}
                                      className="pl-3 border-l-2 border-zinc-300 dark:border-zinc-600"
                                    >
                                      {point}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="text-zinc-400 dark:text-zinc-500 text-sm font-light text-center py-12">
                      Click on a stock in the treemap or table to view its AI
                      analysis
                    </div>
                  )}
                </div>

                {/* Sector Exposure Widget */}
                <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 flex-shrink-0">
                  <div className="relative inline-block mb-3">
                    <h2 
                      className="text-lg font-light text-zinc-800 dark:text-white cursor-help"
                      onMouseEnter={() => setTooltipVisible('sector-exposure')}
                      onMouseLeave={() => setTooltipVisible(null)}
                    >
                      Sector Exposure
                    </h2>
                    {tooltipVisible === 'sector-exposure' && (
                      <div className="absolute z-10 top-full mt-1 left-0 bg-zinc-900 text-white text-xs p-2 rounded shadow-lg w-64 whitespace-normal font-light">
                        Weighted average risk index for this sector, calculated by multiplying each stock's risk index by its portfolio weight and dividing by total sector weight
                      </div>
                    )}
                  </div>
                  <div className="flex items-center justify-between p-4 bg-zinc-50 dark:bg-zinc-700/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full flex-shrink-0"
                        style={{ backgroundColor: SECTOR_COLORS[activeSection] || '#6b7280' }}
                      ></div>
                      <span className="text-zinc-700 dark:text-zinc-300 font-medium">
                        {activeSection}
                      </span>
                    </div>
                    <span
                      className="px-3 py-1.5 rounded text-sm font-medium"
                      style={{
                        backgroundColor: getRiskColor(getCurrentSectorExposure(activeSection)),
                        color: Math.abs(getCurrentSectorExposure(activeSection)) > 0.5 ? '#fff' : '#000'
                      }}
                    >
                      {getCurrentSectorExposure(activeSection).toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Risk Table */}
              <div className="col-span-2 bg-white dark:bg-zinc-800 rounded-lg p-6 overflow-hidden flex flex-col">
                <h2 className="text-lg font-light text-zinc-800 dark:text-white mb-4">
                  Risk Analysis
                </h2>
                <div className="overflow-auto flex-1">
                  <table className="w-full">
                    <thead className="sticky top-0 bg-zinc-50 dark:bg-zinc-700/50">
                      <tr>
                        <th className="text-left p-3 text-zinc-700 dark:text-white font-normal text-sm">
                          Ticker
                        </th>
                        {Object.keys(columnTooltips).map((col) => (
                          <th
                            key={col}
                            className="text-left p-3 text-zinc-700 dark:text-white font-normal text-sm relative cursor-help"
                            onMouseEnter={() => setTooltipVisible(col)}
                            onMouseLeave={() => setTooltipVisible(null)}
                          >
                            {col}
                            {tooltipVisible === col && (
                              <div className="absolute z-10 top-full mt-1 left-0 bg-zinc-900 text-white text-xs p-2 rounded shadow-lg max-w-xs whitespace-normal font-light">
                                {columnTooltips[col]}
                              </div>
                            )}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {getSectorStocks(activeSection).map((stock, idx) => (
                        <tr
                          key={idx}
                          onClick={() => setSelectedStock(stock.ticker)}
                          className={`border-t border-zinc-100 dark:border-zinc-700/50 hover:bg-zinc-50 dark:hover:bg-zinc-700/30 transition-colors cursor-pointer ${
                            selectedStock === stock.ticker
                              ? "bg-blue-50 dark:bg-blue-900/20"
                              : ""
                          }`}
                        >
                          <td className="p-3 font-mono text-zinc-800 dark:text-white font-normal text-sm">
                            {stock.ticker}
                          </td>
                          <td className="p-3">
                            <span
                              className="px-2 py-1 rounded text-sm font-normal"
                              style={{
                                backgroundColor: getRiskColor(stock.riskIndex),
                                color:
                                  stock.riskIndex < -0.5 ||
                                  stock.riskIndex > 0.5
                                    ? "#fff"
                                    : "#000",
                              }}
                            >
                              {stock.riskIndex.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400 text-sm font-light">
                            {(stock.exposureValue * 100).toFixed(2)}%
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400 text-sm font-light">
                            {stock.directRisk.toFixed(2)}
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400 text-sm font-light">
                            {stock.indirectRisk.toFixed(2)}
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400 text-sm font-light">
                            {stock.timeFactor.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}