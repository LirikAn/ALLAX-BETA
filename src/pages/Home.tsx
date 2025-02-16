import React from 'react';
import { Button } from '../components/ui/button';
import { useNavigate } from 'react-router-dom';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form-header">
        <h2 className="auth-title animate-fade-in">Домашняя страница</h2>
        <p className="auth-subtitle animate-fade-in-delayed">
          Добро пожаловать!
        </p>
      </div>

      <div className="auth-form">
        <Button 
          variant='primary'
          onClick={() => navigate('/create-test')}
          className='submit-button'
        >
          Создать тест
        </Button>
        <Button 
          variant='primary'
          onClick={() => navigate('/enter-test')}
          className='submit-button'
        >
          Вход в тест
        </Button>
        <Button 
          variant='primary'
          onClick={handleLogout}
          className='submit-button'
        >
          Выйти
        </Button>
      </div>
    </div>
  );
};

export default Home;