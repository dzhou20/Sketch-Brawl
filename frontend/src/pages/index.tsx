import Head from 'next/head';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="layout">
      <Head>
        <title>Sketch Brawl</title>
      </Head>
      <main>
        <h1>Sketch Brawl Demo</h1>
        <p>Launch the dual-player canvas and judge tooling.</p>
        <Link href="/match">Open Lobby</Link>
      </main>
    </div>
  );
}
