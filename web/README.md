# IG Follower Analyzer - Web Dashboard

Modern Next.js web application for VAs to manage Instagram client data, trigger scrapes, and categorize pages.

## Features

### 1. Clients Tab
- Add new clients with name + Instagram username
- View all clients with following counts
- Select multiple clients for batch scraping
- Delete clients
- Real-time status updates

### 2. Pages Tab
- View pages followed by multiple clients
- Filter by minimum client count
- Click to view detailed profile information:
  - Profile picture
  - Bio
  - Contact email
  - Promo status with indicators
  - Recent posts grid
- Visual indicators for verified accounts

### 3. Scrape Jobs Tab
- Real-time scrape job monitoring (auto-refresh every 5s)
- Job status tracking (pending → processing → completed/failed)
- Coverage metrics for client following scrapes (highlights <95% coverage)
- Failed usernames displayed for debugging
- Job history with timestamps

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Query** - Data fetching & caching
- **Axios** - HTTP client
- **date-fns** - Date formatting
- **lucide-react** - Icons

## Setup

### Install Dependencies
```bash
npm install
```

### Environment Variables
Create a `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production:
```
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

### Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build for Production
```bash
npm run build
npm start
```

## Deployment

### Vercel (Recommended)
1. Push code to GitHub
2. Import project to Vercel
3. Set environment variable: `NEXT_PUBLIC_API_URL=https://your-api.com`
4. Deploy!

Vercel auto-detects Next.js and handles build/deploy automatically.

### Netlify
1. Connect GitHub repo
2. Build command: `npm run build`
3. Publish directory: `.next`
4. Add environment variable: `NEXT_PUBLIC_API_URL`

### Railway / Render
1. Create a new **Web Service**
2. Connect your GitHub repo
3. Set build command: `cd web && npm install && npm run build`
4. Set start command: `cd web && npm start`
5. Add environment variable: `NEXT_PUBLIC_API_URL`

### Docker
```bash
# Build
docker build -t ig-web .

# Run
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 ig-web
```

## Project Structure

```
web/
├── app/
│   ├── components/
│   │   ├── QueryProvider.tsx    # React Query setup
│   │   ├── ClientsTab.tsx       # Clients management UI
│   │   ├── PagesTab.tsx         # Pages browsing UI
│   │   └── ScrapesTab.tsx       # Scrape jobs monitoring
│   ├── lib/
│   │   └── api.ts               # API client & types
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Main dashboard
│   └── globals.css              # Global styles
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

## API Integration

The app communicates with the FastAPI backend via REST endpoints:

**Clients:**
- `GET /api/clients` - List clients
- `POST /api/clients` - Add client
- `DELETE /api/clients/:id` - Delete client

**Pages:**
- `GET /api/pages?min_client_count=2` - List pages
- `GET /api/pages/:id/profile` - Get profile details

**Scrapes:**
- `GET /api/scrapes` - List scrape runs
- `POST /api/scrapes/client-following` - Trigger client scrape
- `POST /api/scrapes/profile-scrape` - Trigger profile scrape

## Features in Detail

### Auto-Refresh
The Scrape Jobs tab automatically refreshes every 5 seconds to show real-time job progress.

### Coverage Indicators
When scraping client following lists, the app displays:
- ✅ Green "Excellent" badge for ≥95% coverage
- ⚠️ Yellow warning for 90-94% coverage
- ❌ Red warning for <90% coverage

### Batch Operations
Select multiple clients and trigger scrapes for all at once. Jobs are queued automatically and processed by workers.

### Profile Previews
View full profile details including bio, contact email, promo status, and a grid of recent posts (loaded from base64-encoded images).

## Development Tips

### Adding New Tabs
1. Create component in `app/components/NewTab.tsx`
2. Add tab button in `app/page.tsx`
3. Import and render in tab content section

### Customizing Styles
Edit `app/globals.css` for global styles or use Tailwind classes inline.

### API Types
All types are defined in `app/lib/api.ts`. Update when backend schema changes.

## Troubleshooting

### API Connection Errors
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify API server is running
- Check browser console for CORS errors

### Build Errors
- Delete `.next` folder and rebuild: `rm -rf .next && npm run build`
- Clear node_modules: `rm -rf node_modules && npm install`

### Styling Issues
- Restart dev server after changing Tailwind config
- Check Tailwind purge settings aren't removing needed classes

## Future Enhancements

- [ ] Search/filter clients and pages
- [ ] Pagination for large datasets
- [ ] Export data to CSV
- [ ] Bulk page categorization UI
- [ ] Real-time websocket updates (instead of polling)
- [ ] Dark mode toggle
- [ ] User authentication
- [ ] Multi-user collaboration features

## Contributing

When adding features:
1. Use TypeScript for type safety
2. Follow existing component patterns
3. Add loading states for async operations
4. Handle errors gracefully with user-friendly messages
5. Update this README with new features

