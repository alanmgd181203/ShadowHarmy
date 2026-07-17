/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./*.{js,jsx}", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        abyss: "#0a0c10",
        igris: "#ff0055",
      },
    },
  },
  plugins: [],
};
