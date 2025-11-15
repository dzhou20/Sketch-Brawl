import type { NextApiRequest, NextApiResponse } from 'next';

const backendBase =
  process.env.BACKEND_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_BACKEND_URL ??
  'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const path = (req.query.path as string[]).join('/');
  const url = `${backendBase}/${path}`;

  const response = await fetch(url, {
    method: req.method,
    headers: {
      'Content-Type': req.headers['content-type'] ?? 'application/json',
    },
    body: ['GET', 'HEAD'].includes(req.method ?? '') ? undefined : JSON.stringify(req.body),
  });

  const text = await response.text();
  res.status(response.status).send(text);
}
