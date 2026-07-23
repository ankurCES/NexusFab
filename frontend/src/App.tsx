import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PlantDetail from './pages/PlantDetail';
import Maintenance from './pages/Maintenance';
import Network from './pages/Network';
import Workforce from './pages/Workforce';

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
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
