import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import { AppFrame } from "@/components/AppFrame";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-plus-jakarta",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Pocket Nori",
  description: "Pocket Nori — personal intelligence layer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>
        <AppFrame>{children}</AppFrame>
      </body>
    </html>
  );
}
