import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading data...',
  size = 'md',
  className = '',
}) => {
  const iconSizes = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <Loader2 className={`${iconSizes[size]} animate-spin text-blue-600 mb-3`} />
      <p className="text-sm font-medium text-slate-600">{message}</p>
    </div>
  );
};

export default LoadingState;
