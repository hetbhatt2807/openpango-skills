import type { Metadata } from "next";
import { Syne, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

const syne = Syne({ 
  subsets: ["latin"], 
  variable: "--font-syne",
  display: 'swap',
});

const jbMono = JetBrains_Mono({ 
  subsets: ["latin"], 
  variable: "--font-mono",
  display: 'swap',
});

export const metadata: Metadata = {
  title: "OpenPango | True Autonomous Agents",
  description: "Beyond skills. True digital souls instantiated with IDENTITY and SOUL.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body
        className={`${syne.variable} ${jbMono.variable} font-sans bg-black text-zinc-100 antialiased selection:bg-[#ff3e00] selection:text-white`}
      >
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <div className="flex-grow">
            {children}
          </div>
          <Footer />
        </div>
      </body>
    </html>
  );
}
