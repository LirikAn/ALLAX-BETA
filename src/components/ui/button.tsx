import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'text' | 'success';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  icon,
  ...props
}) => {
  const variants = {
    primary: 'button-primary',
    secondary: 'button-secondary',
    outline: 'button-outline',
    success: 'button-success',
    text: 'button-text'
  } as const;
  
  const sizes = {
    sm: 'button-sm',
    md: 'button-md',
    lg: 'button-lg'
  } as const;

  const classes = [
    'button',
    variants[variant],
    sizes[size],
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      className={classes}
      {...props}
    >
      {icon && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};

export default Button;