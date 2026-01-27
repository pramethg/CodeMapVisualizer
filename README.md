# CodeMap Visualizer

CodeMap Visualizer is a developer tool designed to transform static source code into interactive, explorable mind maps. By leveraging Abstract Syntax Tree (AST) parsing, it visualizes the relationships between classes, functions, and methods across multiple programming languages (Python, MATLAB, C++).

## Installation

### Prerequisites
*   **Node.js** (v18+)
*   **Python** (v3.8+)
*   **npm** or **yarn**

### Quick Start

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/codemap-visualizer.git
    cd codemap-visualizer
    ```

2.  **Backend Setup (FastAPI)**

    **Option A: Using pip (traditional)**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

    **Option B: Using uv (recommended, faster)**
    ```bash
    cd backend
    uv venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    uv pip install -r requirements.txt
    uvicorn main:app --reload
    ```
    
    The API will be available at `http://localhost:8000`.

3.  **Frontend Setup (Next.js)**
    Open a new terminal window:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
    The application will be accessible at `http://localhost:3000`.

---

## Architecture & Implementation

CodeMap Visualizer operates on a decoupled client-server architecture designed for extensibility and performance.

### Backend (Python/FastAPI)
The backend serves as the parsing engine and file system interface.
*   **AST Parsing**: Utilizes language-specific libraries (`ast` for Python, custom parsing for C++/MATLAB) to extract structural metadata (functions, classes, arguments) without executing code.
*   **API Layer**: Exposes endpoints for file scanning (`/scan-file`, `/scan-folder`) and data persistence.
*   **Storage**: Metadata and comments are persisted in a non-intrusive `.visualizer` directory within your project's `assets/` folder (`{project_root}/assets/.visualizer/`). Files are named using a collision-resistant strategy based on relative paths.

### Frontend (TypeScript/Next.js)
The frontend handles visualization, state management, and user interaction.
*   **Graph Rendering**: Powered by **React Flow** for performant interactive node-based UIs and **Dagre** for deterministic, hierarchical graph layout algorithms.
*   **State Management**: React State and Effect hooks manage the graph data, user preferences (theme, spacing), and file system traversal.
*   **Design System**: Built with Tailwind CSS for a responsive, dark-mode-first aesthetic.

---

## Key Features

*   **Multi-Language AST Support**: Accurate parsing for Python, MATLAB, and C++.
*   **Interactive Visualization**:
    *   **Dynamic Layout**: Adjustable node spacing and auto-layout.
    *   **Zoom & Pan**: Infinite canvas navigation.
    *   **Mini-Map**: High-level structural overview.
*   **Annotation System**:
    *   **Rich Comments**: Add context-aware notes to any code node.
    *   **Tagging**: Categorize nodes (e.g., TODO, BUG, REVIEW).
    *   **Centralized Storage**: Annotations persist across sessions.
*   **Developer Tools**:
    *   **Search**: Fuzzy search for function/class names with keyboard navigation.
    *   **Bookmarks & Recents**: Quick navigation to frequently accessed files.
    *   **Export**: Save visualizations as high-resolution images or PDFs.

## Advanced Functionality

CodeMap Visualizer is built for power users who demand precision and control.

*   **Zero-Hallucination Parsing**: Unlike LLM-based or regex tools, CodeMap uses **language-native AST parsers**. This guarantees that every class, function, and argument shown in the graph exists exactly as written in your source code.
*   **Intelligent Caching**: The application utilizes a smart caching layer (`.visualizer`) that persists your comments and layout metadata. Annotations survive git checkouts and branch switches, making it a robust companion for long-term projects.
*   **Deterministic Layout Engine**: Powered by **Dagre**, the graph layout is mathematically calculated to minimize edge crossing and maximize readability. It's not just a random scattering of nodes; it's a structural blueprint of your logic.
*   **Privacy-First Architecture**: Your code never leaves your machine. All scanning, parsing, and visualization happens locally on your device, ensuring 100% data privacy for proprietary codebases.

## Usage

1.  **Launch the App**: Ensure both backend and frontend servers are running.
2.  **Select a Project**: Use the sidebar folder picker to open a local directory.
3.  **Visualize Code**: Click on any file in the file tree to generate its graph.
4.  **Annotate**: Right-click nodes to add comments or tags.
5.  **Configure**: Use the Sidebar settings to adjust layout density, font size, or clear application cache.
