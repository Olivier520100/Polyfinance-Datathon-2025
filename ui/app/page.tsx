import { PortfolioRiskDashboard } from './PortfolioRiskDashboard';
import fs from 'fs';
import path from 'path';

async function loadPortfolioData() {
  try {
    const dataPath = path.join(process.cwd(), 'app', 'data.txt');
    const dataContent = await fs.promises.readFile(dataPath, 'utf-8');
    const mainData = JSON.parse(dataContent);
    
    const analysisMap = {};
    for (const company of mainData.company_details) {
      try {
        const analysisPath = path.join(process.cwd(), 'app', 'analysis', `${company.ticker}.json`);
        const analysisContent = await fs.promises.readFile(analysisPath, 'utf-8');
        analysisMap[company.ticker] = JSON.parse(analysisContent);
      } catch (err) {
        analysisMap[company.ticker] = {
          DirectRiskFactor: 0,
          IndirectRiskFactor: 0,
          TimeFactor: 0,
          Summary: 'No analysis available',
          SummaryKeypoints: []
        };
      }
    }
    
    return { mainData, analysisMap };
  } catch (error) {
    console.error('Error loading data:', error);
    return null;
  }
}

export default async function Page() {
  const data = await loadPortfolioData();
  
  if (!data) {
    return (
      <div className="flex items-center justify-center h-screen bg-zinc-50 dark:bg-zinc-900">
        <div className="text-red-500">Error loading portfolio data</div>
      </div>
    );
  }
  
  return <PortfolioRiskDashboard initialData={data.mainData} initialAnalysis={data.analysisMap} />;
}