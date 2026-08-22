import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The repo already has its own AGENTS.md/CLAUDE.md conventions at the
  // repo root (see AGENTS.md). Disable Next.js's auto-generated
  // apps/web/AGENTS.md and apps/web/CLAUDE.md so they don't shadow those.
  agentRules: false,
};

export default nextConfig;
