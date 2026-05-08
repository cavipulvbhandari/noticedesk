/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@noticedesk/shared'],
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
