import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PlantDetail from './pages/PlantDetail';
import Maintenance from './pages/Maintenance';
import Network from './pages/Network';
import Workforce from './pages/Workforce';
import Energy from './pages/Energy';
import Scenarios from './pages/Scenarios';
import Analytics from './pages/Analytics';
import Compliance from './pages/Compliance';
import Sequencing from './pages/Sequencing';
import Sensors from './pages/Sensors';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/plant/:plantId" element={<PlantDetail />} />
          <Route path="/maintenance" element={<Maintenance />} />
          <Route path="/network" element={<Network />} />
          <Route path="/workforce" element={<Workforce />} />
          <Route path="/energy" element={<Energy />} />
          <Route path="/scenarios" element={<Scenarios />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/sequencing" element={<Sequencing />} />
          <Route path="/sensors" element={<Sensors />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
