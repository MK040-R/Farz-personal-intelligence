"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { navItems } from "@/components/app-frame/nav-items";

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav className="space-y-1">
      {navItems.map((item) => {
        const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`sidebar-nav-link block px-4 py-2.5 text-sm font-medium ${
              isActive ? "sidebar-nav-link--active" : ""
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
