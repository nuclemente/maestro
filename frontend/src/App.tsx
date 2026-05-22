import { Route, Routes } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import Home from './pages/Home';
import People from './pages/People';
import PeopleDrafts from './pages/PeopleDrafts';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="people" element={<People />} />
        <Route path="people/drafts" element={<PeopleDrafts />} />
      </Route>
    </Routes>
  );
}
