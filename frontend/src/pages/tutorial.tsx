'use client';

import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import tutorialCopy from '@/i18n/demo.json';

const locales = ['en', 'zh'] as const;
type Locale = (typeof locales)[number];

type TutorialSection = {
  title: string;
  bullets: string[];
};

type TutorialContent = {
  title: string;
  subtitle: string;
  steps: TutorialSection[];
  cta: Record<
    string,
    {
      label: string;
      href: string;
    }
  >;
};

const translations = tutorialCopy as Record<Locale, TutorialContent>;

export default function TutorialPage() {
  const [locale, setLocale] = useState<Locale>('en');

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('zh')) {
      setLocale('zh');
    }
  }, []);

  const content = translations[locale];
  const steps = content.steps;
  const ctas = useMemo(() => Object.values(content.cta), [content.cta]);

  return (
    <div className="tutorial-layout">
      <Head>
        <title>{content.title}</title>
      </Head>
      <header className="tutorial-header">
        <div>
          <p className="eyebrow">sketch brawl demo</p>
          <h1>{content.title}</h1>
          <p className="subtitle">{content.subtitle}</p>
        </div>
        <div className="locale-toggle">
          {locales.map((code) => (
            <button
              key={code}
              className={code === locale ? 'active' : ''}
              onClick={() => setLocale(code)}
            >
              {code === 'en' ? 'English' : '中文'}
            </button>
          ))}
        </div>
      </header>
      <section className="tutorial-grid">
        {steps.map((section) => (
          <article key={section.title} className="tutorial-card">
            <h2>{section.title}</h2>
            <ul>
              {section.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>
      <footer className="tutorial-cta">
        {ctas.map((cta) =>
          cta.href.startsWith('http') ? (
            <a key={cta.href} href={cta.href} target="_blank" rel="noreferrer">
              {cta.label}
            </a>
          ) : (
            <Link key={cta.href} href={cta.href}>
              {cta.label}
            </Link>
          ),
        )}
      </footer>
    </div>
  );
}
