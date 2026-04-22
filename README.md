# Canadian Food Recall Alert System

A cloud-based system that automatically detects new food recalls from Health Canada, generates AI-powered summaries, and notifies subscribers via email.

---

## Architecture

```
CloudWatch (daily schedule)
    → AWS Lambda
        → FastAPI on AWS EC2
            → Health Canada Open Data JSON
                → AWS RDS (PostgreSQL)
                    → Google Gemini (AI summaries)
                        → Gmail SMTP (email alerts)
```

---

## Cloud Services

| Service | Provider | Purpose |
|---|---|---|
| EC2 | AWS | Hosts FastAPI backend |
| RDS (PostgreSQL) | AWS | Stores recalls and subscribers |
| Lambda | AWS | Serverless sync trigger |
| CloudWatch | AWS | Schedules Lambda daily |
| Google Gemini | Google AI Studio | Generates AI summaries |
| Gmail SMTP | Google | Delivers email notifications |

---

## Features

### Data Ingestion
- Fetches recall data from Health Canada's Open Data JSON (`HCRSAMOpenData.json`)
- Filters CFIA food recalls only
- Limits to recalls from the last 30 days
- Excludes archived recalls

### Data Storage
- Stores recalls in PostgreSQL on AWS RDS
- Detects and skips duplicate recalls by NID
- Tracks dispatch status per recall

### AI Processing
- Class 1 recalls get a 2-sentence plain-language summary via Google Gemini
- Class 2 and 3 recalls get template-based summaries (cost-efficient)

### Anomaly Detection
- Flags Class 1 (high risk) recalls automatically
- Detects repeat recalls — same product recalled twice within 30 days

### Notification System
- Class 1 recalls trigger immediate email
- Class 2 and 3 recalls batched into a daily digest
- Emails include severity badge, AI summary, and repeat recall warning

### Subscription System
- Users subscribe via frontend form
- One-click email confirmation link
- Category-based preferences (Dairy, Meat, Seafood, etc.)

### Frontend
- Single HTML file — no framework required
- Recall dashboard with search, severity filter, and category filter
- Category checkboxes with live recall counts per category
- Live email preview card

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/recalls` | Returns all stored recalls |
| GET | `/recalls/sync` | Fetches new recalls and triggers alerts |
| GET | `/recalls/dashboard` | Filterable recall list for frontend |
| GET | `/recalls/digest` | Sends batched Class 2/3 email digest |
| GET | `/categories/counts` | Recall counts per food category (last 30 days) |
| POST | `/subscribe` | Subscribe with email and category preferences |
| GET | `/confirm` | Confirms email subscription via token |

---

## Database Tables

### `recalls`
Stores all fetched CFIA food recalls.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| recall_id | VARCHAR | Same as NID |
| nid | VARCHAR | Health Canada recall ID |
| title | TEXT | Full recall title |
| recall_class | VARCHAR | Class 1 / Class 2 / Class 3 |
| food_category | TEXT | e.g. Dairy, Meat, Seafood |
| issue | TEXT | e.g. Listeria, Salmonella |
| url | TEXT | Recall detail URL |
| last_updated | DATE | Date from Health Canada |
| ai_summary | TEXT | Gemini-generated summary |
| dispatched | BOOLEAN | Whether email was sent |
| created_at | TIMESTAMP | When record was inserted |

### `users`
Stores subscriber information.

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| email | VARCHAR | Subscriber email |
| categories | TEXT[] | Selected food categories |
| is_confirmed | BOOLEAN | Email confirmed status |
| confirmation_token | VARCHAR | One-time confirmation token |
| created_at | TIMESTAMP | Signup timestamp |

---

## Project Structure

```
food-recall-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # RDS connection + table creation
│   │   ├── ai_service.py        # Google Gemini summary generation
│   │   ├── email_service.py     # Gmail SMTP email delivery
│   │   └── routes/
│   │       ├── recalls.py       # Recall fetch, sync, dashboard endpoints
│   │       └── users.py         # Subscribe, confirm, category count endpoints
│   ├── .env                     # Environment variables (not committed)
│   └── requirements.txt
└── frontend/
    └── index.html               # Single-file frontend
```

---

## Environment Variables

```
DB_HOST=your-rds-endpoint
DB_PORT=5432
DB_NAME=recalls
DB_USER=postgres
DB_PASSWORD=your-password
GMAIL_SENDER=your@gmail.com
GMAIL_APP_PASSWORD=your-app-password
GMAIL_RECIPIENT=your@gmail.com
BASE_URL=http://your-ec2-ip:8000
GEMINI_API_KEY=your-google-ai-studio-key
```

---

## Data Source

Health Canada Open Data JSON:
`https://recalls-rappels.canada.ca/sites/default/files/opendata-donneesouvertes/HCRSAMOpenData.json`

Filtered by:
- `Organization = CFIA`
- `Last updated` within last 30 days
- `Archived = 0`
