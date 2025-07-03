
import { render } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';
import { ThemeProvider } from '@/components/theme-provider';

describe('Navbar', () => {
  it('renders navigation links correctly', () => {
    const { getByText } = render(
      <Router>
        <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
          <Navbar />
        </ThemeProvider>
      </Router>,
    );

    expect(getByText(/Home/i)).toBeInTheDocument();
    expect(getByText(/About/i)).toBeInTheDocument();
  });

  it('renders the business name', () => {
    const { getByText } = render(
      <Router>
        <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
          <Navbar />
        </ThemeProvider>
      </Router>,
    );
    expect(getByText(/Credit Clarity/i)).toBeInTheDocument();
  });
});
