import Head from 'next/head';
import Link from 'next/link';
import type { CSSProperties } from 'react';

type CSSVarStyle = CSSProperties & { [key: `--${string}`]: string };

const backgroundTexture = 'https://www.figma.com/api/mcp/asset/3d3f5cbc-ed06-4a54-9f54-3bda5312d30c';

export default function Home() {
  const heroStyle: CSSVarStyle = {
    '--hero-texture': `url(${backgroundTexture})`,
  };

  return (
    <>
      <Head>
        <title>Sketch Brawl</title>
      </Head>
      <div className="hero-screen" data-node-id="42:2667" style={heroStyle}>
        <div className="hero-nav">
          <Link href="/tutorial">Judge Tutorial</Link>
        </div>
        <div className="hero-content">
          <p className="hero-title" data-node-id="42:2669">
            Sketch Brawl!
          </p>
          <Link className="hero-cta" data-node-id="42:2670" href="/match">
            start sketching
          </Link>
        </div>
      </div>
    </>
  );
}
