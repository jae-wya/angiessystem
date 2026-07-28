# 🌸 Angie's Florist — Supabase + Streamlit Community Cloud Edition

Complete flower shop management system, ready to deploy to the cloud.

---

## 🆕 Recent Improvements

### Live Boards — Auto-Refresh
The 🌹 Florist Board and 🚴 Rider Board now auto-refresh every 30 seconds, so staff see new rush orders or status changes without manually reloading.

### 👤 Customers (CRM)
A new Customers page aggregates every customer by contact number — total orders, completed vs cancelled, lifetime spend, last order date, and full order history per customer. Exportable as CSV. Great for spotting VIPs and repeat buyers.

### 📋 Shareable Daily/Weekly Recap
The Dashboard now includes a copy-paste recap (Today or This Week) — order counts, revenue, top arrangement, rush orders, and low-stock alerts — formatted for pasting straight into a group chat.

### 📈 Restock Forecast (Reports)
Estimates daily usage of each inventory item based on flowers used in orders over the last 30 days, and projects days-until-stockout. Flags anything projected to run out within 14 days. Improves in accuracy as more orders are logged via the Flower Builder.

### 🏪 Branch Comparison (Reports, Super Admin only)
Side-by-side comparison of all branches: order volume, revenue, average order value, cancellations, failed deliveries, and waste cost — with bar charts.

### Performance — Caching
All read operations (`get_orders`, `get_inventory`, etc.) are now cached for **10 seconds** using `st.cache_data`. This makes navigation feel instant. Any write (new order, status update, etc.) immediately clears the cache so your own changes show right away — other users see updates within ~10 seconds, or can hit **🔄 Refresh Data** in the sidebar for an instant pull.

### Persistent File Uploads — Supabase Storage
Inspiration pictures, proof of payment, finished product photos, and proof of delivery are now uploaded to a **Supabase Storage bucket** (`angies-florist-uploads`) instead of local disk. This is critical because Streamlit Community Cloud wipes local files on every restart — Storage makes them permanent and accessible from any device.

**Setup required:** Run the updated `supabase_schema.sql` — it creates the bucket and storage policies automatically. If the bucket creation SQL fails (some projects restrict this), create it manually:
1. Supabase Dashboard → **Storage** → **New bucket**
2. Name: `angies-florist-uploads`
3. Toggle **Public bucket: ON**
4. Then re-run just the `create policy ...` statements from the bottom of `supabase_schema.sql`

### Pagination & Date Filtering (All Orders)
At higher order volumes (500-1,000+/month), loading every order at once gets slow. All Orders now:
- Defaults to showing only the **last 60 days** (toggle "Show all orders" to see everything)
- Paginates results **25 per page**

### Database Indexes
Added indexes on `status`, `branch`, `target_date`, `customer_contact`, `assigned_florist`, `assigned_rider`, and `created_at` — keeps filtering fast as your order history grows.

---

## 📁 File Structure

```
angies_florist_supabase/
├── angies_florist_v3.py          ← Main app (run this)
├── db.py                         ← Supabase data layer
├── requirements.txt              ← Python dependencies
├── supabase_schema.sql           ← Run once in Supabase SQL Editor
├── .streamlit/
│   ├── config.toml               ← App theme & settings
│   └── secrets.toml.template     ← Copy → secrets.toml, fill in credentials
└── README.md
```

---

## 🚀 Deployment Steps

### STEP 1 — Set Up Supabase

1. Go to [https://app.supabase.com](https://app.supabase.com) and create a free account
2. Click **New Project**, give it a name (e.g. `angies-florist`), set a password, choose a region
3. Wait for the project to finish provisioning (~1 min)
4. In the left sidebar, go to **SQL Editor**
5. Paste the entire contents of `supabase_schema.sql` and click **Run**
   - This creates all 7 tables: `orders`, `inventory`, `waste`, `florists`, `riders`, `payment_transactions`, `hr_logs`
6. Go to **Project Settings → API** and copy:
   - **Project URL** (looks like `https://xxxxxxxxxxxx.supabase.co`)
   - **anon public key** (long JWT string)

---

### STEP 2 — Push to GitHub

1. Create a new **private** GitHub repository
2. Upload all files in this folder to the repo root
3. Make sure `.streamlit/secrets.toml` is in `.gitignore` (never commit secrets!)

```
# .gitignore
.streamlit/secrets.toml
__pycache__/
*.pyc
uploads/
```

---

### STEP 3 — Deploy on Streamlit Community Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repository, branch (`main`), and set the main file path to:
   ```
   angies_florist_v3.py
   ```
5. Click **Advanced settings → Secrets**
6. Paste the following (replace with your actual values):

```toml
[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
key = "YOUR_SUPABASE_ANON_KEY"
```

7. Click **Deploy!** — Your app will be live in ~2 minutes 🎉

---

## 🔄 Updating the App (after the first deploy)

Once your app is live, applying future updates (new features, bug fixes) is much simpler than the first deploy — **no need to repeat Supabase or Streamlit setup** unless a change specifically says so.

1. **Get the updated files** (you'll usually be given: `angies_florist_v3.py`, `db.py`, `requirements.txt`, and sometimes `supabase_schema.sql` or `README.md`)
2. Go to your GitHub repo
3. For each updated file:
   - Click the file → click the **pencil (edit) icon**, or
   - Use **Add file → Upload files** at the repo root and drag in the new version — GitHub will ask to confirm overwriting
4. Scroll down, write a short commit message describing the change, click **Commit changes**
5. **Streamlit Community Cloud auto-redeploys** within 1-2 minutes of detecting the push — no manual redeploy needed
6. **If a `supabase_schema.sql` update is included**: go to Supabase → SQL Editor → run only the **new** statements mentioned in the changelog (don't re-run the whole file unless told to — most statements use `if not exists` / `on conflict do nothing` so they're safe to re-run, but it's cleaner to run just what's new)
7. Refresh the live app and verify the new feature appears

**If the build fails after an update:**
- Check the Streamlit Cloud build logs (click on your app → **Manage app** → logs)
- Most common cause: a new package was added to `requirements.txt` and failed to install — check the log for a `pip install` error
- If something looks broken, you can always re-upload the previous working version of the file to roll back

---

## 🔑 Staff Login System (PIN-based)

Every staff member logs in with their own **4-6 digit PIN** — no usernames, emails, or passwords needed. Fast on mobile.

### First login
A default **Super Admin** account is seeded by `supabase_schema.sql`:
- **PIN: `123456`**
- ⚠️ **Log in immediately and create your real accounts**, then deactivate or change this seed account's PIN (Staff Management → 🔐 Accounts).

### Roles & what they can access

| Role | Access |
|------|--------|
| **Staff** | Dashboard, New Order, All Orders, Florist Board, Rider Board, Schedule, Inventory, Waste Tracker, Reports — scoped to their branch |
| **Florist** | Dashboard, New Order, All Orders, Florist Board, Schedule — scoped to their branch |
| **Rider** | Dashboard, Rider Board, Schedule — scoped to their branch |
| **Branch Manager** | Everything Staff can see, plus Staff Management & Reports — scoped to their branch |
| **Super Admin** | Everything, all branches, plus the HR Module |

**Branch scoping** means non-Super-Admin accounts only see orders, inventory, waste, florists, and riders belonging to their assigned branch. Super Admin (and accounts with branch = `All`) see everything across all branches.

### Managing accounts
Go to **👥 Staff Management → 🔐 Accounts** (visible to Branch Managers and Super Admins):
- Create new accounts (name, role, branch, PIN)
- Reset a forgotten PIN
- Activate / deactivate / delete accounts
- Branch Managers can only manage Staff/Florist/Rider accounts for their own branch; Super Admin can manage everyone.

---

### STEP 4 — Local Development (optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Create secrets file (local only — do NOT commit)
mkdir -p .streamlit
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your credentials

# Run the app
streamlit run angies_florist_v3.py
```

---

## 🔐 Security Notes

| What | Recommendation |
|------|---------------|
| Supabase anon key | Safe to use in client apps — already restricted by RLS |
| Row Level Security | Enabled on all tables. Currently set to "allow all" — the app enforces access via PINs/roles, but a determined user with the anon key could bypass this at the database level. Tighten with Supabase Auth + per-row policies for stronger guarantees |
| Secrets in git | **Never commit** `.streamlit/secrets.toml` |
| PINs | Stored as salted SHA-256 hashes, never in plaintext. Still, PINs are short — don't reuse them for anything sensitive elsewhere |
| Seed Super Admin (PIN `123456`) | Change or deactivate this immediately after first login |
| HR Module | Restricted to the Super Admin role via the login system |

---

## 🗄️ What Changed from the JSON Version

| Feature | Before (JSON) | After (Supabase) |
|---------|--------------|-----------------|
| Data storage | `angies_florist_complete.json` local file | Supabase PostgreSQL cloud DB |
| Multi-device | ❌ One machine only | ✅ Any device, anywhere |
| Data persistence | ❌ Lost if server restarts | ✅ Permanent in cloud |
| Concurrent users | ❌ File locking issues | ✅ Safe concurrent writes |
| Backups | ❌ Manual | ✅ Supabase auto-backups |
| File uploads (inspo pics, proof of payment/delivery, finished product) | Saved to local `/uploads/` | ✅ Supabase Storage — synced across all devices |
| Data layer | Scattered `json.load`/`json.dump` calls | Centralized `db.py` module |

---

## 📦 Supabase Free Tier Limits

- 500 MB database storage
- 5 GB bandwidth/month
- 2 projects
- Sufficient for a single flower shop! Upgrade only if needed.

---

## 🛠️ Troubleshooting

**`supabase.exceptions.APIError: Invalid API key`**
→ Double-check the `key` in your secrets. Use the **anon public** key, not the service role key.

**`relation "orders" does not exist`**
→ You forgot to run `supabase_schema.sql`. Go to Supabase → SQL Editor and run it.

**`ModuleNotFoundError: No module named 'supabase'`**
→ Make sure `requirements.txt` is in your repo root and Streamlit Cloud picked it up. Redeploy if needed.

**App shows old data / data not saving**
→ Check Supabase → Table Editor to confirm rows are being inserted. Check the browser console for API errors.
