import type { Metadata } from "next";

import { AppFrame } from "@/components/AppFrame";

import "./globals.css";

export const metadata: Metadata = {
  title: "Farz Frontend",
  description: "Farz private intelligence layer frontend",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppFrame>{children}</AppFrame>
      </body>
    </html>
  );
}
