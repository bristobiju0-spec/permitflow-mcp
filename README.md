# PermitFlow Pro - Industrial HVAC Compliance

PermitFlow Pro is a high-performance PWA for field contractors to verify Title 24 compliance instantly using AI-powered OCR.

## 🚀 Deploy to Vercel (Free)

This project is pre-configured for Vercel's Python Serverless Runtimes and Static Hosting.

### 1. Prerequisites
- A [Vercel Account](https://vercel.com) (Free Tier)
- A [Supabase Project](https://supabase.com) (for persistent production data)

### 2. Deployment Steps

1. **Install Vercel CLI** (optional):
   ```bash
   npm i -g vercel
   ```

2. **Deploy via GitHub**:
   - Push this directory to a new GitHub repository.
   - Import the project into Vercel.
   - Vercel will automatically detect `vercel.json` and `api/index.py`.

3. **Configure Environment Variables**:
   In your Vercel Project Settings, add:
   - `SUPABASE_URL`: Your Supabase Project URL
   - `SUPABASE_ANON_KEY`: Your Supabase Anon Key
   - `PADDLE_VENDOR_ID`: Your Paddle Vendor ID

4. **Persistence**:
   The app will automatically use Supabase if `SUPABASE_URL` is detected, ensuring your audit logs persist across Vercel's serverless restarts.

## 🛠 Tech Stack
- **Frontend**: Vanilla JS + Tailwind CSS + Framer Motion (SPA)
- **Backend**: FastAPI (Serverless Python)
- **Auth**: Supabase Magic Links & Google OAuth
- **Database**: SQLite (Local) / Supabase (Production)
- **PWA**: manifest.json + Service Worker for Offline Capture
