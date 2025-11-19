# Policy Navigator - React UI

Modern, elegant React-based user interface for the Policy Navigator chatbot application.

## Features

- 🎨 **Modern Design**: Clean, minimal, elegant UI with floating card-style components
- 💬 **Chat Interface**: Beautiful message bubbles with smooth animations
- 📜 **Chat History**: Slide-in drawer for accessing previous conversations
- 📱 **Responsive**: Fully responsive design for mobile and desktop
- ⚡ **Fast**: Built with Vite for optimal performance
- ♿ **Accessible**: Keyboard navigation and focus management

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Flask API backend running on `http://localhost:5000`

### Installation

1. Navigate to the React UI directory:
```bash
cd web/react-ui
```

2. Install dependencies:
```bash
npm install
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Building for Production

Build the production bundle:
```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

Preview the production build:
```bash
npm run preview
```

## Project Structure

```
web/react-ui/
├── src/
│   ├── components/          # React components
│   │   ├── PolicyNavigator.jsx
│   │   ├── Header.jsx
│   │   ├── ChatWindow.jsx
│   │   ├── ChatMessage.jsx
│   │   ├── ChatInputBar.jsx
│   │   ├── ChatHistoryDrawer.jsx
│   │   └── FloatingContainer.jsx
│   ├── hooks/              # Custom React hooks
│   │   └── useChat.js
│   ├── services/           # API service layer
│   │   └── api.js
│   ├── styles/             # Styling
│   │   ├── theme.js
│   │   └── global.css
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## Configuration

### API URL

By default, the app connects to `http://localhost:5000`. To change this, create a `.env` file:

```env
VITE_API_URL=http://your-api-url:5000
```

## Design System

The UI follows a modern design system with:

- **Primary Color**: #4A6CF7 (Modern Indigo Blue)
- **Background**: #F7F8FA (Light gray)
- **Surface**: #FFFFFF (White)
- **Text**: #1E1E1E (Dark gray)

See `src/styles/theme.js` for the complete color palette and design tokens.

## Features

### Chat Interface
- Real-time message display
- Auto-scrolling to latest messages
- Loading states and error handling
- Example query chips for quick access

### Chat History
- Persistent chat history (localStorage)
- Slide-in drawer with smooth animations
- Card-based history entries
- Quick access to previous conversations

### Responsive Design
- Mobile-first approach
- Breakpoints at 768px and 480px
- Touch-friendly interactions
- Optimized spacing for small screens

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

Part of the Policy Navigator project.

