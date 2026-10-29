// Aplica el tema guardado antes de pintar para evitar un destello. Es un archivo del mismo
// origen porque la CSP (script-src 'self') no permite scripts en línea.
try {
  var preference = localStorage.getItem("sc-theme");
  var dark =
    preference === "dark" ||
    (preference !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  if (dark) document.documentElement.classList.add("dark");
} catch (error) {
  // Sin almacenamiento: se usa el tema claro.
}
