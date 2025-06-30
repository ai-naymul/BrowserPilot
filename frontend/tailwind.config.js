/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        fontFamily: {
          'sans': ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        },
      },
    },
    plugins: [],
  }
  