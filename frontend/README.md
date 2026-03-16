# Antigravity Frontend (Next.js)

The user interface for the Agentic AI Platform.

## 🛠️ Tech Stack
*   **Next.js 16** (App Router).
*   **React 19**.
*   **TailwindCSS 4**: Zero-runtime styling.
*   **Framer Motion**: Animations.
*   **Lucide React**: Iconography.

## 🏃‍♂️ Running Locally

1.  **Install**:
    ```bash
    npm install
    ```

2.  **Dev Server**:
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000).

## 🧩 Structure
*   `src/app/`: Next.js App Router pages.
    *   `agents/`: Dynamic agent dashboards.
*   `src/components/ui/`: Reusable design systems components (Buttons, Cards).
*   `src/services/api.ts`: Centralized Axios instance for backend communication.
