import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  transpilePackages: ['@limitboard/ui', '@limitboard/db-types'],
  experimental: {
    typedRoutes: true
  }
}

export default nextConfig
