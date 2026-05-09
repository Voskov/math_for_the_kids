const DARK_START = 19;
const LIGHT_START = 7;

function shouldBeDark(): boolean {
  const saved = localStorage.getItem("theme");
  if (saved) return saved === "dark";
  const h = new Date().getHours();
  return h >= DARK_START || h < LIGHT_START;
}

export function initTheme(): void {
  document.documentElement.classList.toggle("dark", shouldBeDark());
}

export function toggleTheme(): boolean {
  const dark = document.documentElement.classList.toggle("dark");
  localStorage.setItem("theme", dark ? "dark" : "light");
  return dark;
}

export function isDark(): boolean {
  return document.documentElement.classList.contains("dark");
}
