import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer
      className="border-t py-8 px-6 text-sm"
      style={{ borderColor: '#1E2D47', background: 'rgba(8,13,26,0.6)' }}
    >
      <div className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-8">
        {/* branding */}
        <div className="flex flex-col items-start gap-2">
          <span className="text-gold-gradient font-bold text-lg tracking-tight">CreditClarity</span>
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} CreditClarity. All rights reserved.
          </p>
        </div>

        {/* navigation links */}
        <nav className="flex flex-col space-y-2">
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

        {/* contact & social */}
        <div className="flex flex-col space-y-2">
          <p className="text-muted-foreground">Contact us:</p>
          <a
            href="mailto:support@creditclarity.com"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            support@creditclarity.com
          </a>
          <div className="flex items-center gap-4 mt-2">
            {/* placeholder social icons */}
            <a href="https://twitter.com/creditclarity" className="text-muted-foreground hover:text-foreground transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
                <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53A4.48 4.48 0 0 0 22.43 1s-4.11 1.72-6.12 4.27a4.48 4.48 0 0 0-7.62 3.08A12.85 12.85 0 0 1 1.64 2.15a4.48 4.48 0 0 0 1.39 5.97A4.44 4.44 0 0 1 .96 7v.06a4.48 4.48 0 0 0 3.6 4.39 4.52 4.52 0 0 1-2.02.08 4.48 4.48 0 0 0 4.18 3.11A9 9 0 0 1 .41 16.6a12.74 12.74 0 0 0 6.92 2.03c8.29 0 12.83-6.87 12.83-12.83 0-.2 0-.39-.01-.58A9.18 9.18 0 0 0 23 3z"/>
              </svg>
            </a>
            <a href="https://facebook.com/creditclarity" className="text-muted-foreground hover:text-foreground transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" className="h-5 w-5">
                <path d="M22 12a10 10 0 1 0-11.5 9.87v-6.99h-2.1v-2.88h2.1V9.41c0-2.07 1.23-3.22 3.1-3.22.9 0 1.84.16 1.84.16v2.02h-1.04c-1.03 0-1.35.64-1.35 1.3v1.55h2.3l-.37 2.88h-1.93v6.99A10 10 0 0 0 22 12z"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
