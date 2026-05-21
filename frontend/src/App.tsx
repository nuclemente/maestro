import { Route, Routes } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import Home from './pages/Home';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
      </Route>
    </Routes>
  );
}
