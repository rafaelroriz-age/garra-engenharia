import type { Metadata, Viewport } from "next";
import { Inter, Manrope } from "next/font/google";

import { AppShell } from "@/components/layout/app-shell";
import { cn } from "@/lib/utils";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Garra Engenharia · Relatórios Prediais",
    template: "%s · Garra Engenharia",
  },
  description:
    "Sistema de automação de relatórios de inspeção predial (RFO, LTIP, vistorias cautelares) da Garra Engenharia.",
  manifest: "/manifest.json",
  icons: {
    icon: "/icon.svg",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Garra Engenharia",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#1e3a5f",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={cn(inter.variable, manrope.variable)}>
      <body className="font-sans antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
