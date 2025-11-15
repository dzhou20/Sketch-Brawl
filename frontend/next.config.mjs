/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [],
  experimental: {
    instrumentationHook: true,
  },
};

export default nextConfig;
