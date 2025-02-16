import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import Input from '../components/ui/input';
import Label from '../components/ui/label';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function RegisterForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:5000/register', formData);
      alert('Реєстрація успішна!');
      navigate('/login');
    } catch (error) {
      alert('Електронна пошта вже використовується');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form-header">
        <h2 className="auth-title animate-fade-in">Реєстрація</h2>
        <p className="auth-subtitle animate-fade-in-delayed">
          Створіть свій обліковий запис
        </p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group animate-slide-up">
          <Label htmlFor="name" className="form-label">Ім'я</Label>
          <Input 
            id="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Іван Іваненко"
            className="form-input"
            required
          />
        </div>
        
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
          type="submit"
          className="submit-button animate-fade-in"
        >
          Зареєструватися
        </Button>
      </form>

      <div className="auth-footer animate-fade-in-delayed">
        <p>
          Вже є обліковий запис?
          <button 
            className="toggle-button"
            onClick={() => navigate('/login')}
            type="button"
          >
            Увійти
          </button>
        </p>
      </div>
    </div>
  );
}