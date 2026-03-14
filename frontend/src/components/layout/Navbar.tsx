import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { CreditsBalance } from "@/components/credits/CreditsBalance";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Menu } from "lucide-react";

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, signOut } = useAuth();

  return (
    <header
      className="navbar-midnight px-6 md:px-10"
      style={{ paddingLeft: '2.5rem', paddingRight: '2.5rem' }}
    >
      <div className="w-full flex items-center justify-between gap-6">

        {/* Logo */}
        <Link
          to="/"
          className="text-gold-gradient font-extrabold text-lg tracking-tight flex-shrink-0"
          style={{ letterSpacing: '-0.02em' }}
        >
          CreditClarity
        </Link>

        {/* Desktop nav links */}
        <nav className="hidden md:flex items-center gap-1 flex-1">
          <Link
            to="/dashboard"
            className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            Dashboard
          </Link>
          <Link
            to="/credit-report-upload"
            className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            Upload
          </Link>
          <Link
            to="/tradelines"
            className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            Tradelines
          </Link>
          <Link
            to="/dispute-wizard"
            className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            Disputes
          </Link>
          {user && (
            <Link
              to="/dispute-history"
              className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
            >
              History
            </Link>
          )}
          <Link
            to="/pricing"
            className="px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            Pricing
          </Link>
        </nav>

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center gap-2 flex-shrink-0">
          {user ? (
            <>
              <CreditsBalance />
              <Link to="/profile">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-foreground hover:bg-white/5"
                >
                  {user.email?.split('@')[0] ?? 'Profile'}
                </Button>
              </Link>
              <Button
                size="sm"
                className="btn-gold rounded-md px-4"
                onClick={signOut}
              >
                Sign Out
              </Button>
            </>
          ) : (
            <>
              <Link to="/login">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-foreground hover:bg-white/5"
                >
                  Sign In
                </Button>
              </Link>
              <Link to="/signup">
                <Button size="sm" className="btn-gold rounded-md px-5">
                  Get Started
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-foreground hover:bg-white/5"
            >
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent
            side="left"
            className="sm:max-w-xs"
            style={{ background: '#0C1220', borderRight: '1px solid #1E2D47' }}
          >
            <SheetHeader>
              <SheetTitle className="text-gold-gradient font-extrabold text-lg">
                CreditClarity
              </SheetTitle>
            </SheetHeader>
            <nav className="flex flex-col gap-1 mt-6">
              {[
                { to: '/dashboard', label: 'Dashboard' },
                { to: '/credit-report-upload', label: 'Upload Report' },
                { to: '/tradelines', label: 'Tradelines' },
                { to: '/dispute-wizard', label: 'Dispute Wizard' },
                ...(user ? [{ to: '/dispute-history', label: 'Dispute History' }] : []),
                { to: '/pricing', label: 'Pricing' },
                { to: '/about', label: 'About' },
                { to: '/faq', label: 'FAQ' },
              ].map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  onClick={() => setIsOpen(false)}
                  className="px-3 py-2.5 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
                >
                  {label}
                </Link>
              ))}
              <div className="mt-4 pt-4 border-t border-[#1E2D47] flex flex-col gap-2">
                {user ? (
                  <>
                    <Link to="/profile" onClick={() => setIsOpen(false)}>
                      <Button variant="ghost" size="sm" className="w-full justify-start text-muted-foreground">
                        {user.email?.split('@')[0] ?? 'Profile'}
                      </Button>
                    </Link>
                    <Button size="sm" className="btn-gold rounded-md w-full" onClick={signOut}>
                      Sign Out
                    </Button>
                  </>
                ) : (
                  <>
                    <Link to="/login" onClick={() => setIsOpen(false)}>
                      <Button variant="ghost" size="sm" className="w-full text-muted-foreground">
                        Sign In
                      </Button>
                    </Link>
                    <Link to="/signup" onClick={() => setIsOpen(false)}>
                      <Button size="sm" className="btn-gold rounded-md w-full">
                        Get Started
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            </nav>
          </SheetContent>
        </Sheet>

      </div>
    </header>
  );
}
