/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/core/:path*',
        destination: `${process.env.PYTHON_CORE_URL || 'http://localhost:8000'}/:path*`,
      },
    ]
  },
}

export default nextConfig
