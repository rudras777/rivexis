import Link from "next/link";
import {Brand} from "@/components/Brand";

const navItems=[
  ["Platform","/platform"],
  ["Blockchain","/blockchain-intelligence"],
  ["Crypto Finance","/crypto-finance"],
  ["Methodology","/methodology"],
  ["Security","/security"],
] as const;

export function PublicNav(){
  return <header className="top">
    <Brand/>
    <nav className="desktopPublicNav" aria-label="Primary navigation">
      {navItems.map(([label,href])=><Link key={href} href={href}>{label}</Link>)}
    </nav>
    <div className="publicActions"><Link className="ghost" href="/login">Log in</Link><Link className="button" href="/signup">Start workspace</Link></div>
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
