import { tr } from './tr';
import { en } from './en';

export type Lang = 'tr' | 'en';

export const translations = { tr, en };

export function t(lang: Lang) {
  return translations[lang];
}

export function getLangFromUrl(url: URL): Lang {
  const [, lang] = url.pathname.split('/');
  if (lang === 'en') return 'en';
  return 'tr';
}
