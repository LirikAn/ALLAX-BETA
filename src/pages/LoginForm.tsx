import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import Input from '../components/ui/input';
import Label from '../components/ui/label';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function LoginForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://127.0.0.1:5000/login', formData);
      alert('Вхід успішний!');
      localStorage.setItem('token', response.data.token); // Сохранение токена
      navigate('/home'); // Перенаправление на /home
    } catch (error) {
      alert('Неправильні облікові дані');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form-header">
        <h2 className="auth-title animate-fade-in">Ласкаво просимо!</h2>
        <p className="auth-subtitle animate-fade-in-delayed">
          Раді бачити вас знову
        </p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group animate-slide-up">
          <Label htmlFor="email" className="form-label">Електронна пошта</Label>
          <Input 
            id="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="example@mail.com"
            className="form-input"
            required
          />
        </div>

        <div className="form-group animate-slide-up">
          <Label htmlFor="password" className="form-label">Пароль</Label>
          <Input 
            id="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="••••••••"
            className="form-input"
            required
          />
        </div>

        <Button 
          variant='primary'
          type='submit'
          className='submit-button'
        >
          Вхід
        </Button>
      </form>

      <div className="auth-footer animate-fade-in-delayed">
        <p>
          Ще немає облікового запису?
          <button 
              className="toggle-button"
              onClick={() => navigate('/register')}
              type='button'
          >
            Зареєструватися
          </button>
        </p>
      </div>
    </div>
  );
}