/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0a0f18", // Deep dark blue/black foundation
                surface: "#111827",    // Slightly lighter for cards/panels
                primary: "#3b82f6",    // Electric blue for main actions
                secondary: "#6366f1",  // Indigo for gradients
                accent: "#06b6d4",     // Cyan for highlights
                success: "#10b981",
                warning: "#f59e0b",
                error: "#ef4444",
                text: {
                    main: "#f3f4f6",
                    muted: "#9ca3af",
                },
                border: "#1f2937",
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['Fira Code', 'monospace'],
            },
        },
    },
    plugins: [],
}
