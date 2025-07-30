import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="bg-background border-t py-6">
      <div className="container flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          © 2025 CreditDispute. All rights reserved.
        </p>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/privacy-policy" className="text-muted-foreground hover:text-primary">
            Privacy Policy
          </Link>
          <Link to="/terms-and-conditions" className="text-muted-foreground hover:text-primary">
            Terms & Conditions
          </Link>
          <Link to="/about" className="text-muted-foreground hover:text-primary">
            About
          </Link>
          <Link to="/" className="text-muted-foreground hover:text-primary">
            Home
          </Link>
        </nav>
      </div>
    </footer>
  );
}
