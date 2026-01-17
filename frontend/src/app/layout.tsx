import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'SOTA - 세피리아 석판 최적화',
  description: '세피리아 석판 배치 최적화 도구',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <div className="min-h-screen">
          <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold text-white">
                SOTA <span className="text-gray-400 text-sm font-normal">Sephiria Optimal Tablet Arranger</span>
              </h1>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
