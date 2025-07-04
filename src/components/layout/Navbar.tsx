import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Menu } from "lucide-react";
import { ModeToggle } from "@/components/layout/ModeToggle";
import { CurrentUserAvatar } from "@/components/current-user-avatar";

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, signOut } = useAuth();

  return (
    <header className="bg-background border-b">
      <div className="container flex items-center justify-between h-10">
        <Link to="/" className="font-bold text-xl">
          Credit Clarity
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          <Link to="/" className="text-sm font-medium transition-colors hover:text-primary">
            Home
          </Link>
          <Link to="/admin" className="text-sm font-medium transition-colors hover:text-primary">
            Admin
          </Link>
          {/* <Link to="/blog" className="text-sm font-medium transition-colors hover:text-primary">
            Blog
          </Link> */}
          <Link to="/about" className="text-sm font-medium transition-colors hover:text-primary">
            About
          </Link>
          {/* Other links commented out */}
          <Link to="/faq" className="text-sm font-medium transition-colors hover:text-primary">
            FAQ
          </Link>
        </nav>

        <div className="flex items-center gap-4">
          <ModeToggle />
          {user ? (
            <div className="hidden md:flex items-center gap-2">
              <Link to="/profile">
                <Button variant="ghost" size="sm">
                  <CurrentUserAvatar user={user} />
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                className="rounded-full"
                onClick={signOut}
              >
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-2">
              <Link to="/login">
                <Button variant="outline" size="sm" className="rounded-full">
                  Sign In
                </Button>
              </Link>
              <Link to="/signup">
                <Button size="sm">Sign Up</Button>
              </Link>
            </div>
          )}
        </div>

        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="sm:max-w-sm">
            <SheetHeader>
              <SheetTitle>Menu</SheetTitle>
              <SheetDescription>
                Explore our site and discover how we can help you.
              </SheetDescription>
            </SheetHeader>
            <div className="grid gap-4 py-2">
              <Link to="/" className="block text-sm font-medium transition-colors hover:text-primary">
                Home
              </Link>
              <Link to="/about" className="block text-sm font-medium transition-colors hover:text-primary">
                About
              </Link>
              <Link to="/blog" className="block text-sm font-medium transition-colors hover:text-primary">
                Blog
              </Link>
              <Link to="/credit-reports" className="block text-sm font-medium transition-colors hover:text-primary">
                Credit Reports
              </Link>
              <Link to="/credit-report-upload" className="block text-sm font-medium transition-colors hover:text-primary">
                Credit Report Upload
              </Link>
              <Link to="/faq" className="block text-sm font-medium transition-colors hover:text-primary">
                FAQ
              </Link>
              <Link to="/pricing" className="block text-sm font-medium transition-colors hover:text-primary">
                Pricing
              </Link>
              <Link to="/profile" className="block text-sm font-medium transition-colors hover:text-primary">
                Profile
              </Link>
              {!user ? (
                <>
                  <Link to="/login" className="block text-sm font-medium transition-colors hover:text-primary">
                    Sign In
                  </Link>
                  <Link to="/signup" className="block text-sm font-medium transition-colors hover:text-primary">
                    Sign Up
                  </Link>
                </>
              ) : (
                <div className="flex flex-col gap-2">
                  <Link to="/profile" className="block text-sm font-medium transition-colors hover:text-primary">
                    <CurrentUserAvatar user={user} />
                  </Link>
                  <Button variant="outline" size="sm" onClick={signOut} className="rounded-full">
                    Sign Out
                  </Button>
                </div>
              )}
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
