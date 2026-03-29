import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  transpilePackages: ["@limitboard/ui", "@limitboard/db-types"],
  typedRoutes: true,
};

export default nextConfig;
