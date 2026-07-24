import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Auth from './pages/Auth';
import Cameras from './pages/Cameras';
import Models from './pages/Models';
import Events from './pages/Events';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Auth />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Cameras />} />
          <Route path="models" element={<Models />} />
          <Route path="events" element={<Events />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}