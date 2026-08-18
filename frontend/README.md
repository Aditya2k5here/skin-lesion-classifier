# DermaCare Frontend - React UI

Modern web interface for AI-powered skin condition detection.

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Technology

- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type-safe development
- **Tailwind CSS 4** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Lucide React** - Icon library

## Features

✨ **Drag & Drop Upload** - Easy image upload
📷 **Camera Capture** - Direct webcam access
⚡ **Real-time Analysis** - Instant predictions
📊 **Confidence Scores** - Detailed results
🎨 **Responsive Design** - Mobile-friendly UI
🌙 **Dark Mode** - Eye-friendly interface

## Project Structure

```
frontend/
├── src/app/
│   ├── page.tsx          # Main analysis interface
│   ├── layout.tsx        # HTML structure
│   └── globals.css       # Styling & theme
├── package.json          # Dependencies
└── tsconfig.json         # TypeScript config
```

## Development

**Code Quality:**

```bash
npm run lint          # Run ESLint
```

**Production Build:**

```bash
npm run build        # Optimize bundle
npm start            # Run production server
```

## API Integration

Connects to backend at `http://localhost:8000`

**Endpoints:**

- `GET /health` - Health check
- `POST /analyze` - Image analysis

## Browser Support

✅ Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
📱 Works on mobile with camera support

## Tips

- Use HTTPS for camera access in production
- Ensure backend is running before testing
- Check console for debugging info
- Test with various image sizes

---

Built with ❤️ for DermaCare | Version 1.0.0
