import nextConfig from "eslint-config-next";

// Flat config, per issue #16. `eslint-config-next` already ships as a flat
// config array (React, react-hooks, jsx-a11y, @next/next, and the
// TypeScript-aware rules) -- no @eslint/eslintrc / FlatCompat shim needed
// on this version.
const config = [...nextConfig];

export default config;
