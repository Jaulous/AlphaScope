import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  transpilePackages: ["@limitboard/ui", "@limitboard/db-types"],
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
