import type { AppProps } from 'next/app';
import '@/styles/globals.css';

function SketchBrawlApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}

export default SketchBrawlApp;
