import { BookOpen, Terminal, Shield, Zap } from "lucide-react";
import Link from 'next/link';
import { getAllDocs } from '@/lib/docs';

export default async function DocsPage() {
  const docs = getAllDocs();

  const iconMap: Record<string, React.ReactNode> = {
    'Workspace Contract': <Terminal className="w-5 h-5" />,
    'Agent Lifecycle': <Zap className="w-5 h-5" />,
    'CLI Reference': <Terminal className="w-5 h-5" />,
    'Bounty Program': <Shield className="w-5 h-5" />,
    'Memory & State': <BookOpen className="w-5 h-5" />,
    'Security Models': <Shield className="w-5 h-5" />,
  };

  return (
    <main className="min-h-screen bg-black pt-24 pb-24 px-5">
      <div className="max-w-5xl mx-auto">
        <div className="mb-12">
          <div className="pill w-fit mb-5">Documentation</div>
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-3">
            System Architecture
          </h1>
          <p className="text-[15px] text-zinc-400 max-w-lg leading-relaxed">
            Read the manuals to understand how digital souls are constructed and orchestrated.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-3">
          {docs.map((doc) => (
            <Link key={doc.slug} href={`/docs/${doc.slug}`} className="bento p-7 block group">
              <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/[0.04] text-zinc-400 group-hover:text-[#ff4d00] transition-colors mb-5">
                {iconMap[doc.title] || <BookOpen className="w-5 h-5" />}
              </div>
              <h3 className="text-[15px] font-medium text-zinc-200 mb-1.5 group-hover:text-white transition-colors">{doc.title}</h3>
              <p className="text-[13px] text-zinc-500 leading-relaxed">{doc.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
