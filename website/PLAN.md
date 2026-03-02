# OpenPango Ecosystem Website - Technical Phase Plan

This plan outlines the steps required to transform the current Next.js application into a production-ready, interactive ecosystem website.

## Phase 1: Shared UI Foundation & Global Layouts
**Goal:** Create a consistent look and feel across all pages with unified navigation and footer.

- [x] **Task 1.1: Extract Global Components**
  - Create `src/components/layout/Navbar.tsx` (Unified navigation with active state).
  - Create `src/components/layout/Footer.tsx` (Standardized footer from home page).
- [x] **Task 1.2: Refactor Root Layout**
  - Update `src/app/layout.tsx` to include `Navbar` and `Footer`.
  - Remove redundant nav/footer code from `src/app/page.tsx`, `src/app/agents/page.tsx`, and `src/app/docs/page.tsx`.
- [x] **Task 1.3: Design System Components**
  - Create `src/components/ui/Terminal.tsx` (A reusable terminal frame).
  - Create `src/components/ui/Button.tsx` (The signature 'brutalist' button style).

## Phase 2: Interactive Hero & Terminal Demo
**Goal:** Implement the "Initialize Workspace" typing animation demo in the landing page hero.

- [x] **Task 2.1: Develop Terminal Typing Component**
  - Create `src/components/home/TerminalDemo.tsx`.
  - Implement a state-driven typing animation (e.g., `initializing...`, `fetching souls...`, `workspace active`).
- [x] **Task 2.2: Integrate Trigger in Hero**
  - Update `src/app/page.tsx` Hero section.
  - Link the 'Initialize Workspace' button to the `TerminalDemo` animation state.
  - Add Framer Motion transitions for the terminal appearance.

## Phase 3: Dynamic Documentation System
**Goal:** Build a robust, MDX-powered multi-page documentation section.

- [x] **Task 3.1: MDX Infrastructure**
  - Install dependencies: `next-mdx-remote`, `gray-matter`.
  - Create `src/lib/docs.ts` to handle file system reading of MDX files.
  - Create `content/docs/*.mdx` files (Workspace Contract, Agent Lifecycle, etc.).
- [x] **Task 3.2: Dynamic Routing**
  - Create `src/app/docs/[slug]/page.tsx` for individual doc pages.
  - Implement a `DocsSidebar` component for easy navigation between chapters.
- [x] **Task 3.3: MDX Renderer**
  - Create `src/components/docs/MDXComponents.tsx` to style markdown elements (h1, code blocks, etc.) to match the OpenPango aesthetic.

## Phase 4: Enhanced Agents Simulation
**Goal:** Add live load telemetry simulation to the Agents page.

- [x] **Task 4.1: Live Telemetry State**
  - Update `src/app/agents/page.tsx` to use React state/effects.
  - Implement a "flickering" load value (CPU/Memory) that updates every few seconds.
- [x] **Task 4.2: Interaction Enhancements**
  - Add Framer Motion "layout" transitions when agent statuses change.
  - Implement a modal or detail view for the "Inspect" button.

## Phase 5: Final Polish & Verification
**Goal:** Ensure performance, accessibility, and visual consistency.

- [ ] **Task 5.1: Responsive Audit**
  - Verify terminal and docs layout on mobile/tablet.
- [x] **Task 5.2: Build & Lint**
  - Run `npm run build` and `npm run lint` to ensure no regressions.

---

## Technical Dependencies
- `framer-motion`: For all animations.
- `lucide-react`: For iconography.
- `next-mdx-remote` & `gray-matter`: For documentation content.
- `tailwind-merge` & `clsx`: For dynamic styling.
