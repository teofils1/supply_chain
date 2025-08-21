import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

// Apply stored theme BEFORE bootstrapping to avoid FOUC and ensure PrimeNG uses class selector
(() => {
  try {
    const pref = localStorage.getItem('app.theme');
    if (pref === 'dark') {
      document.documentElement.classList.add('dark');
    } else if (pref === 'light') {
      document.documentElement.classList.remove('dark');
    }
  } catch (e) {
    // ignore
  }
})();

bootstrapApplication(App, appConfig).catch((err) => console.error(err));
