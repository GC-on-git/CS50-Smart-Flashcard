import { createContext, useContext, ReactNode } from 'react';

export interface ToastContextType {
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
  warning: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToastContext() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
}

interface ToastProviderProps {
  children: ReactNode;
  value: ToastContextType;
}

export function ToastProvider({ children, value }: ToastProviderProps) {
  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}
