import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'search' | 'password';
}

const Input: React.FC<InputProps> = ({ 
  className = '', 
  error, 
  label,
  icon,
  variant = 'default',
  type,
  ...props 
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const inputType = variant === 'password' 
    ? (showPassword ? 'text' : 'password')
    : type;

  return (
    <div className="form-group">
      {label && (
        <label className="form-label">
          {label}
        </label>
      )}
      
      <div className="input-group">
        <input
          type={inputType}
          className={`form-input ${error ? 'border-red-500' : ''} ${className}`}
          {...props}
        />
        
        {variant === 'password' && (
          <div 
            className="input-group-append"
            onClick={togglePasswordVisibility}
          >
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </div>
        )}
        
        {icon && variant === 'search' && (
          <div className="input-group-append">
            {icon}
          </div>
        )}
      </div>
      
      {error && (
        <p className="form-error">
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;