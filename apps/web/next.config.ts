import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  outputFileTracingRoot: process.cwd(),
  turbopack: { root: process.cwd() },
  async rewrites() {
    return [{ source: "/api-proxy/:path*", destination: `${process.env.API_ORIGIN || "http://localhost:8000"}/api/:path*` }];
  },
};

export default nextConfig;
