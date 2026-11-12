import type { Metadata, Viewport } from "next";
import { Inter, Manrope } from "next/font/google";

import { AppShell } from "@/components/layout/app-shell";
import { SwRegister } from "@/components/sw-register";
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
    default: "Garra Perícias e Avaliações · Relatórios Prediais",
    template: "%s · Garra Perícias e Avaliações",
  },
  description:
    "Sistema de automação de relatórios de inspeção predial (RFO, LTIP, vistorias cautelares) da Garra Perícias e Avaliações.",
  manifest: "/manifest.json",
  icons: {
    icon: "/icon.svg",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Garra Perícias",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#253341",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={cn(inter.variable, manrope.variable)}>
      <body className="font-sans antialiased">
        <SwRegister />
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
