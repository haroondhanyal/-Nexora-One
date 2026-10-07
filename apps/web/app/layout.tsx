import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Nexora One | Business workspace",
  description: "A business operating platform for ERP, finance, people and commerce.",
  icons: { icon: "/brand/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
