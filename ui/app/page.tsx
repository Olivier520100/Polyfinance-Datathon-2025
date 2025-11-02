"use client";

import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Treemap } from 'recharts';
import { ChevronDown, ChevronUp } from 'lucide-react';

const SECTORS = [
  'Information Technology',
  'Communication Services',
  'Healthcare',
  'Financials',
  'Consumer Discretionary',
  'Industrials',
  'Energy',
  'Materials',
  'Consumer Staples',
  'Utilities',
  'Real Estate'
];

const SECTOR_COLORS = {
  'Information Technology': '#3b82f6',
  'Communication Services': '#14b8a6',
  'Healthcare': '#ef4444',
  'Financials': '#10b981',
  'Consumer Discretionary': '#f59e0b',
  'Industrials': '#8b5cf6',
  'Energy': '#ec4899',
  'Materials': '#06b6d4',
  'Consumer Staples': '#84cc16',
  'Utilities': '#f97316',
  'Real Estate': '#6366f1'
};

const portfolioData = [
  { name: 'Information Technology', value: 30.0, color: SECTOR_COLORS['Information Technology'] },
  { name: 'Communication Services', value: 9.0, color: SECTOR_COLORS['Communication Services'] }, // <--- ADD THIS
  { name: 'Healthcare', value: 12.5, color: SECTOR_COLORS['Healthcare'] },
  { name: 'Financials', value: 13.0, color: SECTOR_COLORS['Financials'] },
  { name: 'Consumer Discretionary', value: 10.6, color: SECTOR_COLORS['Consumer Discretionary'] },
  { name: 'Industrials', value: 8.0, color: SECTOR_COLORS['Industrials'] },
  { name: 'Energy', value: 4.0, color: SECTOR_COLORS['Energy'] },
  { name: 'Materials', value: 2.0, color: SECTOR_COLORS['Materials'] },
  { name: 'Consumer Staples', value: 6.0, color: SECTOR_COLORS['Consumer Staples'] },
  { name: 'Utilities', value: 1.5, color: SECTOR_COLORS['Utilities'] },
  { name: 'Real Estate', value: 2.5, color: SECTOR_COLORS['Real Estate'] }
].sort((a, b) => b.value - a.value);

const getSectorStocks = (sector) => {
  // Fixed stock data for each sector
  const sectorStockData = {
    'Information Technology': [
      { ticker: 'AAPL', riskIndex: 0.3, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.2 },
      { ticker: 'MSFT', riskIndex: 0.1, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.8 },
      { ticker: 'NVDA', riskIndex: 0.9, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.1 },
      { ticker: 'GOOGL', riskIndex: 0.2, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.3 },
      { ticker: 'META', riskIndex: 0.6, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.1 }
    ],
    'Healthcare': [
      { ticker: 'JNJ', riskIndex: 0.4, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.5 },
      { ticker: 'UNH', riskIndex: 0.8, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.9 },
      { ticker: 'PFE', riskIndex: 0.2, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.4 },
      { ticker: 'ABBV', riskIndex: 0.9, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.7 }
    ],
    'Financials': [
      { ticker: 'JPM', riskIndex: 0.1, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.8 },
      { ticker: 'BAC', riskIndex: 0.5, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.1 },
      { ticker: 'WFC', riskIndex: 0.3, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.6 },
      { ticker: 'GS', riskIndex: 0.7, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.9 }
    ],
    'Consumer Discretionary': [
      { ticker: 'AMZN', riskIndex: 0.8, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.6 },
      { ticker: 'TSLA', riskIndex: 0.2, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.3 },
      { ticker: 'HD', riskIndex: 0.4, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.2 }
    ],
    'Industrials': [
      { ticker: 'CAT', riskIndex: 0.5, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.3 },
      { ticker: 'BA', riskIndex: 0.2, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.1 },
      { ticker: 'HON', riskIndex: 0.9, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.8 }
    ],
    'Energy': [
      { ticker: 'XOM', riskIndex: 0.6, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.4 },
      { ticker: 'CVX', riskIndex: 0.1, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.1 }
    ],
    'Materials': [
      { ticker: 'LIN', riskIndex: 0.3, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.7 },
      { ticker: 'APD', riskIndex: 0.8, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.4 }
    ],
    'Consumer Staples': [
      { ticker: 'PG', riskIndex: 0.2, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.9 },
      { ticker: 'KO', riskIndex: 0.8, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.7 }
    ],
    'Utilities': [
      { ticker: 'NEE', riskIndex: 0.4, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.3 },
      { ticker: 'DUK', riskIndex: 0.7, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.1 }
    ],
    'Real Estate': [
      { ticker: 'AMT', riskIndex: 0.9, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.5 },
      { ticker: 'PLD', riskIndex: 0.3, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.2 }
    ],
    'Communication Services': [
      { ticker: 'GOOGL', riskIndex: 0.2, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.3 },
      { ticker: 'META', riskIndex: 0.6, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.1 },
      { ticker: 'NFLX', riskIndex: 0.5, exposureValue: 0.4, contractorExposure: '0.2', timeFactor: 0.5 }
    ]
  };
  
  return sectorStockData[sector] || [];
};

const getRiskColor = (risk) => {
  if (risk < 33) return '#10b981';
  if (risk < 66) return '#f59e0b';
  return '#ef4444';
};

const CustomTreemapContent = ({ x, y, width, height, name, value, riskIndex }) => {
  if (width < 30 || height < 20) return null;
  
  // Get riskIndex from the data
  const risk = riskIndex || value || 0;
  
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={getRiskColor(risk)}
        stroke="#fff"
        strokeWidth={2}
      />
      {width > 60 && height > 30 && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 5}
            textAnchor="middle"
            fill="#fff"
            fontSize={14}
            fontWeight="bold"
          >
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 12}
            textAnchor="middle"
            fill="#fff"
            fontSize={11}
          >
            Cap : {risk.toFixed(0)}
          </text>
        </>
      )}
    </g>
  );
};

export default function PortfolioRiskDashboard() {
  const [activeSection, setActiveSection] = useState('portfolio');
  const [hoveredSector, setHoveredSector] = useState(null);
  const [sectorDropdownOpen, setSectorDropdownOpen] = useState(false);
  const [tooltipVisible, setTooltipVisible] = useState(null);

  const getTreemapData = (sector) => {
    const stocks = getSectorStocks(sector);
    return stocks.map(stock => ({
      name: stock.ticker,
      size: stock.exposureValue,
      riskIndex: stock.riskIndex
    }));
  };

  const columnTooltips = {
    'Total Risk Index': 'Composite score of all risk factors for this stock',
    'Direct Exposure': 'Effect factor of the laws passed on the stock',
    'Indirect Exposure': 'Effect factor of the laws passed on entities related to this stock',
    'Time Factor': 'Time factor is based on the recency of the laws (recency leads to volatility)'
  };

  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-900">
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-zinc-800 border-r border-zinc-200/50 dark:border-zinc-700/50 flex flex-col">
        {/* Logo */}
        <div className="h-20 flex items-center justify-center border-b border-zinc-200/50 dark:border-zinc-700/50">
          <div className="w-32 h-12 bg-zinc-100 dark:bg-zinc-700/50 rounded flex items-center justify-center text-zinc-400 dark:text-zinc-500 text-sm font-light">
            LOGO
          </div>
        </div>

        {/* Menu */}
        <nav className="flex-1 p-4">
          <button
            onClick={() => setActiveSection('portfolio')}
            className={`w-full text-left px-4 py-2.5 rounded-lg mb-1 transition-all font-light ${
              activeSection === 'portfolio'
                ? 'bg-blue-500 text-white'
                : 'hover:bg-zinc-50 dark:hover:bg-zinc-700/50 text-zinc-600 dark:text-zinc-400'
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
              {sectorDropdownOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
            {sectorDropdownOpen && (
              <div className="mt-1 ml-2 space-y-0.5">
                {SECTORS.map(sector => (
                  <button
                    key={sector}
                    onClick={() => setActiveSection(sector)}
                    className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-all font-light ${
                      activeSection === sector
                        ? 'bg-blue-500 text-white'
                        : 'hover:bg-zinc-50 dark:hover:bg-zinc-700/50 text-zinc-500 dark:text-zinc-500'
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
        {activeSection === 'portfolio' ? (
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
                    activeIndex={hoveredSector}
                    activeShape={{
                      outerRadius: 175,
                      style: {
                        filter: 'drop-shadow(0 6px 16px rgba(0, 0, 0, 0.12))',
                        transition: 'all 0.1s cubic-bezier(0.4, 0, 0.2, 1)'
                      }
                    }}
                    outerRadius={165}
                    animationDuration={800}
                    animationBegin={0}
                    isAnimationActive={true}
                    label={({ name, value, cx, cy, midAngle, innerRadius, outerRadius, index }) => {
                      const RADIAN = Math.PI / 180;
                      const radius = outerRadius + 25;
                      const x = cx + radius * Math.cos(-midAngle * RADIAN);
                      const y = cy + radius * Math.sin(-midAngle * RADIAN);
                      
                      return (
                        <text
                          x={x}
                          y={y}
                          fill="#52525b"
                          textAnchor={x > cx ? 'start' : 'end'}
                          dominantBaseline="central"
                          className="text-sm font-light"
                          style={{
                            opacity: hoveredSector !== null ? 0 : 1,
                            transition: 'opacity 200ms ease-in-out'
                          }}
                        >
                          {`${value.toFixed(1)}%`}
                        </text>
                      );
                    }}
                    labelLine={{
                      stroke: '#d4d4d8',
                      strokeWidth: 1,
                      style: {
                        opacity: hoveredSector !== null ? 0 : 1,
                        transition: 'opacity 200ms ease-in-out'
                      }
                    }}
                  >
                    {portfolioData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        style={{
                          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.06))'
                        }}
                      />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              
              {/* Custom Legend */}
              <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-white/80 dark:bg-zinc-800/80 backdrop-blur-sm border border-zinc-200/50 dark:border-zinc-700/50 rounded-lg px-4 py-2.5 shadow-sm">
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
                  content={<CustomTreemapContent />}
                />
              </ResponsiveContainer>
              <div className="flex items-center gap-6 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
                  <span className="text-zinc-600 dark:text-zinc-400">Low Risk (0-33)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
                  <span className="text-zinc-600 dark:text-zinc-400">Medium Risk (34-66)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }}></div>
                  <span className="text-zinc-600 dark:text-zinc-400">High Risk (67-100)</span>
                </div>
              </div>
            </div>

            {/* Bottom Section */}
            <div className="grid grid-cols-3 gap-6" style={{ height: '60vh' }}>
              {/* AI Overview */}
              <div className="col-span-1 bg-white dark:bg-zinc-800 rounded-lg p-6">
                <h2 className="text-lg font-light text-zinc-800 dark:text-white mb-4">
                  AI Overview
                </h2>
                <div className="text-zinc-500 dark:text-zinc-500 space-y-3 text-sm font-light">
                  <p>
                    The {activeSection} sector shows moderate volatility with concentrated exposure
                    in several high-risk positions.
                  </p>
                  <p className="font-normal text-zinc-700 dark:text-white">
                    Key Insights:
                  </p>
                  <ul className="list-disc list-inside space-y-2">
                    <li>Top 3 holdings represent 45% of sector exposure</li>
                    <li>Average risk index: 52.3 (elevated)</li>
                    <li>Contractor dependencies exceed industry average</li>
                    <li>Consider rebalancing high-risk positions</li>
                  </ul>
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
                        {Object.keys(columnTooltips).map(col => (
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
                          className="border-t border-zinc-100 dark:border-zinc-700/50 hover:bg-zinc-50 dark:hover:bg-zinc-700/30 transition-colors"
                        >
                          <td className="p-3 font-mono text-zinc-800 dark:text-white font-normal text-sm">
                            {stock.ticker}
                          </td>
                          <td className="p-3">
                            <span
                              className="px-2 py-1 rounded text-white font-normal text-sm"
                              style={{ backgroundColor: getRiskColor(stock.riskIndex) }}
                            >
                              {stock.riskIndex.toFixed(1)}
                            </span>
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400 text-sm font-light">
                            {stock.exposureValue.toLocaleString()}
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400 text-sm font-light">
                            {stock.contractorExposure}
                          </td>
                          <td className="p-3 text-zinc-600 dark:text-zinc-400 text-sm font-light">
                            {stock.timeFactor}
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