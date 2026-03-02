import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

const docsDirectory = path.join(process.cwd(), 'content/docs');

export interface DocMetadata {
  title: string;
  description?: string;
  slug: string;
}

export function getDocSlugs() {
  return fs.readdirSync(docsDirectory);
}

export function getDocBySlug(slug: string) {
  const realSlug = slug.replace(/\.mdx$/, '');
  const fullPath = path.join(docsDirectory, `${realSlug}.mdx`);
  const fileContents = fs.readFileSync(fullPath, 'utf8');
  const { data, content } = matter(fileContents);

  return {
    metadata: { ...data, slug: realSlug } as DocMetadata,
    content,
  };
}

export function getAllDocs(): DocMetadata[] {
  const slugs = getDocSlugs();
  const docs = slugs.map((slug) => getDocBySlug(slug).metadata);
  return docs;
}
