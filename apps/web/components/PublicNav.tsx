import Link from "next/link";
import {Brand} from "@/components/Brand";
import {ThemeToggle} from "./ThemeToggle";

const navItems=[
  ["Platform","/platform"],
  ["Defense Frontier","/defense-frontier"],
  ["Methodology","/methodology"],
  ["Security","/security"],
  ["Docs","/docs"],
] as const;

export function PublicNav(){
  return <header className="top">
    <Brand/>
    <nav className="desktopPublicNav" aria-label="Primary navigation">
      {navItems.map(([label,href])=><Link key={href} href={href}>{label}</Link>)}
    </nav>
    <div className="publicActions"><ThemeToggle/><Link className="ghost" href="/login">Log in</Link><Link className="button" href="/app">Open app</Link></div>
    <details className="mobileNav">
      <summary aria-label="Open navigation">Menu</summary>
      <nav aria-label="Mobile navigation">
        {navItems.map(([label,href])=><Link key={href} href={href}>{label}</Link>)}
        <Link className="mobileNavLogin" href="/login">Log in</Link>
        <Link className="button mobileNavCta" href="/signup">Start workspace</Link>
      </nav>
    </details>
  </header>;
}
