import Link from "next/link";
import {Brand} from "./Brand";
import {ThemeToggle} from "./ThemeToggle";
import {AuthActions} from "./AuthActions";
const navItems=[["Intelligence","/platform"],["LiquidationGuard","/liquidationguard"],["GasGuard","/gasguard"],["Methodology","/methodology"]] as const;
export function PublicNav(){return <header className="top folioNav"><Brand/><nav className="desktopPublicNav" aria-label="Primary navigation">{navItems.map(([label,href])=><Link key={href} href={href}>{label}</Link>)}</nav><div className="publicActions"><ThemeToggle/><AuthActions/></div><details className="mobileNav"><summary aria-label="Menu — open navigation">Menu</summary><nav aria-label="Mobile navigation">{navItems.map(([label,href])=><Link key={href} href={href}>{label}</Link>)}<Link href="/defense-frontier">Defense Frontier</Link><Link href="/demo">Educational demo</Link></nav></details></header>}
