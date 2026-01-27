# 🗺️ CodeMap Visualizer

**Interactive code structure visualization and annotation tool for software engineers and researchers.**

Transform your codebase into an interactive mind map. Explore functions, classes, and their relationships visually. Add comments, tags, and bookmarks to document your understanding.

---

## ✨ Features

### 🔍 Visualization
- **Mind Map View** - See your code structure as an interactive graph
- **Multi-Language Support** - Python, MATLAB, and C++ parsing
- **Function Signatures** - Click any node to see full function signatures
- **Dynamic Sizing** - Nodes sized based on content length

### 🎯 Navigation
- **Search (⌘F/Ctrl+F)** - Find any function or class instantly
- **Arrow Key Navigation** - Move between search matches
- **Zoom to Node** - Double-click to center and zoom
- **Mini-Map** - Overview navigation panel

### 📝 Annotations
- **Right-Click Comments** - Add notes to any node
- **Color-Coded Tags** - TODO, BUG, REFACTOR, REVIEW, DONE
- **Editable Labels** - Custom titles for each comment
- **Persistent Storage** - Comments saved with your project

### 🛠️ Tools
- **Recent Files** - Quick access to recently opened files
- **Bookmarks** - Star files for easy access
- **Copy Signature** - One-click copy function signatures

### 🎨 Customization
- **Dark/Light Theme** - Toggle with one click
- **Custom Dot Color** - Personalize the background grid
- **Native Folder Picker** - macOS system folder selection

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
API available at http://localhost:8000

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
App available at http://localhost:3000

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘/Ctrl + F` | Focus search bar |
| `Escape` | Clear search / Close panels |
| `↑` / `↓` | Navigate search matches |
| `Enter` | Jump to next match |
| `Double-click` | Zoom to node |
| `Right-click` | Add comment to node |

---

## 📁 Project Structure

```
CodeMapVisualizer/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── app/
│   │   ├── services/        # Scanner service
│   │   └── utils/parsers/   # Language parsers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── lib/             # API & utilities
│   │   └── types/           # TypeScript types
│   └── package.json
└── assets/                   # Scanned file cache (JSON)
```

---

## 🎯 Tag System

Comments support color-coded tags for organization:

| Tag | Color | Use Case |
|-----|-------|----------|
| `TODO` | 🔵 Blue | Planned improvements |
| `BUG` | 🔴 Red | Known issues |
| `REFACTOR` | 🟣 Purple | Code cleanup needed |
| `REVIEW` | 🟡 Amber | Needs code review |
| `DONE` | 🟢 Green | Completed tasks |

---

## 🔧 Supported Languages

| Language | Extension | Features |
|----------|-----------|----------|
| Python | `.py` | Functions, Classes, Methods |
| MATLAB | `.m` | Functions, Classes, Properties |
| C++ | `.cpp`, `.h` | Functions, Classes, Structs |

---

## 📄 License

MIT License - Feel free to use and modify!

---

Built with ❤️ using [Next.js](https://nextjs.org), [FastAPI](https://fastapi.tiangolo.com), and [React Flow](https://reactflow.dev)
