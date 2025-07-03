
import { render, screen } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';
import { ThemeProvider } from '@/components/theme-provider';

describe('Navbar', () => {
  it('renders navigation links correctly', () => {
    render(
      <Router>
        <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
          <Navbar />
        </ThemeProvider>
      </Router>,
    );

    expect(screen.getByText(/Home/i)).toBeInTheDocument();
    expect(screen.getByText(/About/i)).toBeInTheDocument();
  });

  it('renders the business name', () => {
    render(
      <Router>
        <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
          <Navbar />
        </ThemeProvider>
      </Router>,
    );
    expect(screen.getByText(/CreditClarity/i)).toBeInTheDocument();
  });
});
