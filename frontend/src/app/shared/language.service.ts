import { Injectable, signal } from '@angular/core';

export type LanguageCode = 'en' | 'ro';

@Injectable({ providedIn: 'root' })
export class LanguageService {
  private storageKey = 'app.language';
  current = signal<LanguageCode>(this.load());

  private load(): LanguageCode {
    const raw = localStorage.getItem(this.storageKey);
    if (raw === 'en' || raw === 'ro') return raw;
    return 'en';
  }

  set(lang: LanguageCode) {
    this.current.set(lang);
    localStorage.setItem(this.storageKey, lang);
  }
}
