import { en } from "./locales/en.js";
import { hi } from "./locales/hi.js";

const dictionaries = { en, hi };

class I18nManager {
  constructor() {
    this.currentLang = localStorage.getItem("bizsync_lang") || "en";
    this.listeners = [];
  }

  get lang() {
    return this.currentLang;
  }

  setLanguage(lang) {
    if (dictionaries[lang]) {
      this.currentLang = lang;
      localStorage.setItem("bizsync_lang", lang);
      this.notify();
    }
  }

  toggleLanguage() {
    const nextLang = this.currentLang === "en" ? "hi" : "en";
    this.setLanguage(nextLang);
  }

  t(path) {
    const dict = dictionaries[this.currentLang] || en;
    const parts = path.split(".");
    let current = dict;
    for (const part of parts) {
      if (current && current[part] !== undefined) {
        current = current[part];
      } else {
        // Fallback to English if key missing in current language
        let fallback = en;
        for (const p of parts) {
          if (fallback && fallback[p] !== undefined) fallback = fallback[p];
          else return path;
        }
        return fallback;
      }
    }
    return current;
  }

  onChange(callback) {
    this.listeners.push(callback);
  }

  notify() {
    this.listeners.forEach((cb) => cb(this.currentLang));
  }
}

export const i18n = new I18nManager();
