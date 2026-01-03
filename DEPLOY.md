# How to Deploy for Free on Vercel

You can deploy this entire application (Frontend + Backend) to Vercel in less than 2 minutes.

### Prerequisites
- A GitHub account.
- A Vercel account (log in with GitHub at [vercel.com](https://vercel.com)).

### Step 1: Push Code to GitHub
1. Create a new repository on GitHub (e.g., `delhi-waterlogging-app`).
2. Open your terminal in this project folder and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/<REPO_NAME>.git
   git push -u origin main
   ```

### Step 2: Deploy on Vercel
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** -> **"Project"**.
3. Import your `delhi-waterlogging-app` repository.
4. **Important**: In the configuration screen:
   - **Framework Preset**: Leave as "Other".
   - **Root Directory**: Leave as `./`.
   - **Environment Variables**: You don't need any (we hardcoded them for the hackathon).
5. Click **Deploy**.

### That's it!
Vercel will build your project, serve your HTML files, and spin up serverless functions for your API. You'll get a URL like `https://delhi-waterlogging-app.vercel.app`.

---

### Troubleshooting
- **Database**: We are using Supabase, so your data will persist automatically.
- **Images**: Since Vercel is serverless, image uploads to the `uploads/` folder are **ephemeral** (they will disappear after a while). For a real production app, you'd use S3 or Supabase Storage, but for a demo, this is expected behavior.
