import type { NextConfig } from "next";

// In production (Railway), set NEXT_PUBLIC_API_URL to the backend Railway URL.
// In development it falls back to localhost:8001.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
