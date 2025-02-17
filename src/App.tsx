import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from './components/PrivateRoute';

// Ленивая загрузка компонентов
const LoginForm = lazy(() => import('./pages/LoginForm'));
const RegisterForm = lazy(() => import('./pages/RegisterForm'));
const Home = lazy(() => import('./pages/Home'));
const CreateTest = lazy(() => import('./pages/CreateTest'));
const EnterTest = lazy(() => import('./pages/EnterTest'));

const App = () => (
  <BrowserRouter>
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/login" element={<LoginForm />} />
        <Route path="/register" element={<RegisterForm />} />
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/home" element={<PrivateRoute><Home /></PrivateRoute>} />
        <Route path="/create-test" element={<PrivateRoute><CreateTest /></PrivateRoute>} />
        <Route path="/enter-test" element={<PrivateRoute><EnterTest /></PrivateRoute>} />
      </Routes>
    </Suspense>
  </BrowserRouter>
);

export default App;