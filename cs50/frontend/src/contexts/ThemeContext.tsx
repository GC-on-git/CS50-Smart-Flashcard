import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { apiClient } from '../api/client';

type Theme = 'light' | 'dark' | 'auto';
type FontSize = 'small' | 'medium' | 'large';

interface ThemeContextType {
  theme: Theme;
  fontSize: FontSize;
  effectiveTheme: 'light' | 'dark'; // Resolved theme (auto becomes light/dark based on system)
  setTheme: (theme: Theme) => void;
  setFontSize: (size: FontSize) => void;
  loadPreferences: () => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>('dark');
  const [fontSize, setFontSizeState] = useState<FontSize>('medium');
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('dark');

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
    setSystemTheme(mediaQuery.matches ? 'light' : 'dark');

    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'light' : 'dark');
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Resolve effective theme (auto becomes light/dark based on system)
  const effectiveTheme: 'light' | 'dark' = theme === 'auto' ? systemTheme : theme;

  // Apply theme to document root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', effectiveTheme);
    document.documentElement.setAttribute('data-font-size', fontSize);
  }, [effectiveTheme, fontSize]);

  // Load preferences from backend
  const loadPreferences = useCallback(async () => {
    // Only load preferences if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      // Use defaults from localStorage or system defaults
      const savedTheme = (localStorage.getItem('theme') as Theme | null) || 'dark';
      const savedFontSize = (localStorage.getItem('fontSize') as FontSize | null) || 'medium';
      setThemeState(savedTheme);
      setFontSizeState(savedFontSize);
      return;
    }

    try {
      const prefs = await apiClient.getUserPreferences();
      setThemeState((prefs.theme as Theme) || 'dark');
      setFontSizeState((prefs.font_size as FontSize) || 'medium');
      // Also update localStorage
      localStorage.setItem('theme', prefs.theme || 'dark');
      localStorage.setItem('fontSize', prefs.font_size || 'medium');
    } catch (error: any) {
      // Only log error if it's not a 401 (unauthorized) - 401 is expected when not logged in
      if (error?.response?.status !== 401) {
        console.error('Failed to load preferences:', error);
      }
      // Use defaults from localStorage or system defaults
      const savedTheme = (localStorage.getItem('theme') as Theme | null) || 'dark';
      const savedFontSize = (localStorage.getItem('fontSize') as FontSize | null) || 'medium';
      setThemeState(savedTheme);
      setFontSizeState(savedFontSize);
    }
  }, []);

  // Load preferences on mount
  useEffect(() => {
    loadPreferences();
  }, [loadPreferences]);

  const setTheme = async (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
    try {
      await apiClient.updateUserPreferences({ theme: newTheme });
    } catch (error) {
      console.error('Failed to update theme preference:', error);
    }
  };

  const setFontSize = async (newSize: FontSize) => {
    setFontSizeState(newSize);
    localStorage.setItem('fontSize', newSize);
    try {
      await apiClient.updateUserPreferences({ font_size: newSize });
    } catch (error) {
      console.error('Failed to update font size preference:', error);
    }
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        fontSize,
        effectiveTheme,
        setTheme,
        setFontSize,
        loadPreferences,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}
