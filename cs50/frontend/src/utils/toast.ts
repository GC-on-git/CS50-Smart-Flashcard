import { ToastData } from '../components/Toast';

// Global toast state management
let toastListeners: Array<(toasts: ToastData[]) => void> = [];
let toasts: ToastData[] = [];

const notifyListeners = () => {
  toastListeners.forEach((listener) => listener([...toasts]));
};

export const toast = {
  show: (message: string, type: ToastData['type'] = 'info', duration?: number) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: ToastData = { id, message, type, duration };
    toasts = [...toasts, newToast];
    notifyListeners();
    return id;
  },
  
  success: (message: string, duration?: number) => {
    return toast.show(message, 'success', duration);
  },
  
  error: (message: string, duration?: number) => {
    return toast.show(message, 'error', duration);
  },
  
  info: (message: string, duration?: number) => {
    return toast.show(message, 'info', duration);
  },
  
  warning: (message: string, duration?: number) => {
    return toast.show(message, 'warning', duration);
  },
  
  remove: (id: string) => {
    toasts = toasts.filter((toast) => toast.id !== id);
    notifyListeners();
  },
  
  subscribe: (listener: (toasts: ToastData[]) => void) => {
    toastListeners.push(listener);
    listener([...toasts]);
    
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener);
    };
  },
};
