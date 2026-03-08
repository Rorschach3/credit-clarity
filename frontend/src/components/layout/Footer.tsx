import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer
      className="border-t py-8 px-6"
      style={{ borderColor: '#1E2D47', background: 'rgba(8,13,26,0.6)' }}
    >
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <span className="text-gold-gradient font-bold text-sm tracking-tight">CreditClarity</span>
          <p className="text-xs text-muted-foreground">
            © 2025 CreditClarity. All rights reserved.
          </p>
        </div>
        <nav className="flex items-center gap-5 text-xs">
          {[
            { to: '/about', label: 'About' },
            { to: '/pricing', label: 'Pricing' },
            { to: '/blog', label: 'Blog' },
            { to: '/faq', label: 'FAQ' },
            { to: '/privacy-policy', label: 'Privacy' },
            { to: '/terms-and-conditions', label: 'Terms' },
          ].map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
