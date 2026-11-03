import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SupplynDemand",
  description: "Local Nifty 50 supply and demand chart study app",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
