# Gym Management System

A web-based Gym Management System with role-based dashboards for managing members, membership plans, fitness classes, and equipment usage.

> Built as part of Spring 2026 Computer Science coursework.

## Table of Contents

- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Application Architecture](#application-architecture)
- [Features](#features)
- [Installation & Setup](#installation--setup)
- [Demo Login Credentials](#demo-login-credentials)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Development Workflow](#development-workflow)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Technology Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL via SQLAlchemy ORM and the psycopg2 driver
- **Validation:** Pydantic v2
- **Authorization:** Role-based access control (RBAC); the caller is identified by a `staff_id` query parameter (see [Security Considerations](#security-considerations))
- **API docs:** OpenAPI / Swagger UI, auto-generated at `/docs`

### Frontend
- **Framework:** React 18 with TypeScript
- **Build tool:** Vite
- **Routing:** React Router v6
- **HTTP client:** Axios
- **Forms:** React Hook Form

### Database
- **DBMS:** PostgreSQL 12+
- **Schema:** Designed from an ER diagram — four core entities (Member, Staff, Class, Machine) plus membership plans and the relationships between them (Membership, ClassEnrollment, MachineUsage)

## Project Structure

```
gym-management-system/
├── backend/                 # FastAPI backend
│   ├── routes/              # API route handlers: members, staff, classes,
│   │                        #   machines, usage, plans, memberships,
│   │                        #   manager, trainer
│   ├── schemas/             # Pydantic validation schemas
│   ├── models.py            # SQLAlchemy ORM models
│   ├── main.py              # App entry point, CORS, router registration
│   ├── config.py            # Settings (incl. hardcoded CORS origins)
│   ├── database.py          # Engine, connection pool, session management
│   ├── auth.py              # Authentication & role checks
│   ├── import_csv.py        # CSV data import utility
│   ├── seed_data.py         # Demo data seeder
│   ├── setup.sh / setup.bat # Automated setup scripts
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variable template
├── frontend/                # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/           # Login, Manager, Reception, Trainer dashboards
│   │   ├── components/      # Reusable components (currently empty)
│   │   ├── services/        # API service layer (api.ts)
│   │   ├── context/         # React context (AuthContext)
│   │   ├── App.tsx          # Root component & routes
│   │   └── main.tsx         # Entry point
│   ├── setup.sh / setup.bat # Automated setup scripts
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── tsconfig.json        # TypeScript configuration
├── .gitignore
└── README.md
```

## Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend  (React 18 + TypeScript · Vite · localhost:5173)  │
│                                                             │
│  LoginPage → AuthContext (localStorage)                     │
│      ↓  role-based redirect                                 │
│  ManagerDashboard | ReceptionDashboard | TrainerDashboard   │
│                                                             │
│  src/services/api.ts  (Axios)                               │
│    • Interceptor appends ?staff_id=<id> to every request    │
│      so the backend can look up the caller's role           │
└──────────────────────────────┬──────────────────────────────┘
                               │  HTTP/JSON
                               │  (CORS: localhost:3000/5173/8000)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Application Layer  (FastAPI · Python · localhost:8000)     │
│                                                             │
│  main.py — CORS middleware, init_db() on startup, 9 routers │
│                                                             │
│  Request pipeline per endpoint:                             │
│    1. Pydantic v2 schema  — type & constraint validation    │
│    2. require_role()      — RBAC (MANAGER / TRAINER /       │
│                             RECEPTION); 403 on failure      │
│    3. Route handler       — business logic, duplicate checks│
│    4. SQLAlchemy ORM or   — parameterized queries           │
│       text() + params       (SQL-injection safe)            │
│    5. get_db() dependency — per-request session, closed     │
│                             in a finally block              │
│                                                             │
│  Routers under /api/v1/:                                    │
│    members · staff · classes · machines · usage · plans     │
│    memberships · manager · trainer                          │
└──────────────────────────────┬──────────────────────────────┘
                               │  SQLAlchemy + psycopg2
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Database  (PostgreSQL 12+ · port 5432 · gym_db)            │
│                                                             │
│  Connection pool: 10 persistent + 20 overflow connections   │
│  pool_pre_ping=True — stale connections are discarded       │
│                                                             │
│  8 tables:                                                  │
│    member · staff · class · machine · member_plan           │
│    membership · class_enrollment · machine_usage            │
│                                                             │
│  Schema created from SQLAlchemy metadata (init_db on start) │
└─────────────────────────────────────────────────────────────┘
```

**Data flow example — Reception signs a member onto a machine:**
1. `ReceptionDashboard` calls `usageAPI.startUsage(machineId, memberId)` in `api.ts`.
2. Axios sends `POST /api/v1/machines/{machine_id}/start?staff_id=<id>` to FastAPI.
3. `require_role(RECEPTION, TRAINER, MANAGER)` looks up the caller in the `staff` table and verifies their role.
4. The route handler confirms the machine and member exist and that the member is not suspended.
5. SQLAlchemy `text()` inserts a row into `machine_usage` with `NOW()` as `start_time`.
6. The JSON response returns the new `usage_id` to the frontend.

## Features

### Member Management
- Register new members with personal information
- Assign membership plans (Basic, Premium, VIP) and renew them
- Track member status (Active, Inactive, Suspended)
- View member history and machine usage

### Class Management
- Create and manage fitness classes
- Assign trainers to classes
- Enroll and remove members
- Track attendance via check-ins

### Machine Usage Tracking
- Record machine sessions (start/end times)
- Manage machine status (Available, Maintenance, Retired)
- View usage statistics per machine or per member

### Role-Based Dashboards

| Role | Capabilities |
|------|--------------|
| **Reception** | Register members, sign members onto machines, view machine status, manage class enrollments |
| **Trainer** | View assigned classes, view class rosters, mark attendance |
| **Manager** | Dashboard overview, machine usage and class enrollment analytics, membership status reports, top-member rankings, create staff accounts |

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+ (running locally)

### 1. Create the database

```bash
createdb -U postgres gym_db
# or, inside psql:  CREATE DATABASE gym_db;
```

The tables themselves are created automatically from the SQLAlchemy models.

### 2. Backend

```bash
cd backend
```

**Option A — Automated setup script (recommended)**
```bash
# Linux / macOS
bash setup.sh

# Windows
setup.bat
```

**Option B — Manual setup**
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
```
Then edit `.env` with your PostgreSQL credentials (see [Environment Variables](#environment-variables)).

**Then (either option), with the virtual environment active:**
```bash
python seed_data.py             # Populate demo data
uvicorn main:app --reload       # Start the API server
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### 3. Frontend

In a second terminal:

```bash
cd frontend
```

**Option A — Automated setup script (recommended)**
```bash
# Linux / macOS
bash setup.sh

# Windows
setup.bat
```

**Option B — Manual setup**
```bash
npm install
```

**Then (either option):**
```bash
npm run dev
```

Frontend: http://localhost:5173

## Demo Login Credentials

After running `python seed_data.py`, log in with any of these accounts:

| Role      | Email               | Password    |
|-----------|---------------------|-------------|
| Manager   | manager@gym.com     | password123 |
| Trainer   | trainer@gym.com     | password123 |
| Reception | reception@gym.com   | password123 |

These are for local development only — do not use them in any deployed environment.

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/gym_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=gym_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DEBUG=True
API_TITLE=Gym Management System API
API_VERSION=1.0.0
```

Keep `DATABASE_URL` consistent with the individual `DATABASE_*` values. Never commit your `.env` file.

CORS origins (`localhost:3000`, `localhost:5173`, `localhost:8000`) are hardcoded in `config.py` and are not read from `.env`.

## API Documentation

All endpoints are prefixed with `/api/v1`. Protected endpoints expect a `staff_id` query parameter, which the frontend adds automatically. Full interactive docs are at http://localhost:8000/docs.

### Staff / Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/staff/login` | Staff login |
| POST | `/staff/register` | Create staff account (Manager only) |
| GET | `/staff/` | List all staff |
| GET | `/staff/{staff_id}` | Get staff details |

### Members
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/members/` | List members (optional `status_filter`) |
| GET | `/members/{member_id}` | Get member details |
| POST | `/members/` | Create member |
| PUT | `/members/{member_id}` | Update member |
| DELETE | `/members/{member_id}` | Delete member |
| PATCH | `/members/{member_id}/status` | Update member status |
| GET | `/members/{member_id}/current-membership/` | Get active membership |
| GET | `/members/{member_id}/usage` | Get machine usage history |

### Classes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/classes/` | List classes (optional `trainer_id`) |
| GET | `/classes/{class_id}` | Get class details |
| POST | `/classes/` | Create class |
| PUT | `/classes/{class_id}` | Update class |
| DELETE | `/classes/{class_id}` | Delete class |
| POST | `/classes/{class_id}/enroll/{member_id}` | Enroll member |
| DELETE | `/classes/{class_id}/enroll/{member_id}` | Remove member |
| PUT | `/classes/{class_id}/checkin/{member_id}` | Mark attendance |

### Machines
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/machines/` | List machines (optional `status_filter`, `category_filter`) |
| GET | `/machines/{machine_id}` | Get machine details |
| POST | `/machines/` | Add machine |
| PUT | `/machines/{machine_id}` | Update machine |
| DELETE | `/machines/{machine_id}` | Delete machine |
| PATCH | `/machines/{machine_id}/status` | Update machine status |
| GET | `/machines/{machine_id}/usage` | Get machine usage history |

### Machine Usage
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/machines/{machine_id}/start` | Start a session (sign member onto machine) |
| PUT | `/machines/{machine_id}/end/{usage_id}` | End a session |
| GET | `/stats/machine/{machine_id}` | Usage stats for a machine |
| GET | `/stats/member/{member_id}` | Usage stats for a member |

### Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/plans/` | List plans |
| GET | `/plans/{plan_id}` | Get plan details |
| POST | `/plans/` | Create plan |
| PUT | `/plans/{plan_id}` | Update plan |
| DELETE | `/plans/{plan_id}` | Delete plan |

### Memberships
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/memberships/members/{member_id}/enroll` | Enroll member in a plan |
| GET | `/memberships/members/{member_id}/current` | Get current membership |
| PUT | `/memberships/members/{member_id}/{plan_id}/renew` | Renew membership |

### Trainer Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/trainer/my-classes` | Classes taught by the logged-in trainer |
| GET | `/trainer/classes/{class_id}/roster` | Full roster for a class |

### Manager Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/manager/dashboard/overview` | Dashboard summary stats |
| GET | `/manager/analytics/machine-usage` | Machine usage analytics (optional `days`) |
| GET | `/manager/analytics/class-enrollment` | Class enrollment stats |
| GET | `/manager/analytics/membership-status` | Membership status breakdown |
| GET | `/manager/analytics/staff-roles` | Staff role distribution |
| GET | `/manager/analytics/top-members` | Most active members |

## Database Schema

### Tables

| Table | Type | Description |
|-------|------|-------------|
| `member` | Entity | Member profiles and status |
| `staff` | Entity | Employee accounts with a role (Reception, Trainer, Manager) |
| `class` | Entity | Fitness classes, each assigned to a trainer |
| `machine` | Entity | Equipment with status and category |
| `member_plan` | Entity | Subscription plans (Basic, Premium, VIP) |
| `membership` | Relationship | Links a member to a plan, with dates |
| `class_enrollment` | Association | Member ↔ Class enrollment and attendance |
| `machine_usage` | Relationship | Member ↔ Machine sessions with start/end times |

### Relationships
- Member → Membership (1 : many)
- Membership → MemberPlan (many : 1)
- Staff (Trainer) → Class (1 : many)
- Member ↔ Class (many : many, via `class_enrollment`)
- Member ↔ Machine (many : many, via `machine_usage`)

## Development Workflow

### Adding a new feature

**Backend**
1. Add or modify the ORM model in `models.py`.
2. Create Pydantic schemas in `schemas/`.
3. Implement the routes in `routes/`, using `require_role()` where access should be restricted.
4. Register any new router in `main.py`.

**Frontend**
1. Add the API call to `src/services/api.ts`.
2. Build the UI in `src/components/` (reusable) or directly in a page under `src/pages/`.
3. Wire it into the relevant dashboard.

**Testing**
1. Exercise the new endpoints in Swagger UI at `/docs`.
2. Verify the frontend integration in the browser.

## Security Considerations

What's in place:
- Passwords are hashed before storage.
- Role checks (`require_role()`) on protected endpoints.
- Input validation via Pydantic schemas.
- Parameterized SQL queries to prevent SQL injection.
- CORS restricted to local development origins.

Known limitations (this is a coursework project, not production-ready):
- **The `staff_id` query parameter is not real authentication.** It is supplied by the client, so anyone who knows or guesses a valid staff ID can call the API with that staff member's role. Replacing it with signed tokens (e.g. JWT) is the top item under [Future Enhancements](#future-enhancements).
- Staff IDs appear in URLs, so they can end up in browser history and server logs.
- The logged-in user is stored in `localStorage`.
- Demo credentials are weak and shared; seed data must not be used in a deployed environment.

## Troubleshooting

### Backend won't start
- Make sure PostgreSQL is running and the `gym_db` database exists.
- Check the credentials in `backend/.env`.
- If port 8000 is in use: `uvicorn main:app --reload --port 8001` (then update the API base URL in `frontend/src/services/api.ts`).

### Frontend can't reach the API
- Confirm the backend is running at http://localhost:8000.
- Check the CORS origins in `backend/config.py` include the port the frontend is running on.
- Check the browser console for the specific error.
- If port 5173 is in use: `npm run dev -- --port 5174` (and add that origin to `config.py`).

### Database errors
- Make sure the PostgreSQL user has permission to create tables in `gym_db`.
- Check that the database name in `.env` matches the one you created.
- Review the PostgreSQL logs for details.

## Future Enhancements

- JWT authentication with refresh tokens (replacing the `staff_id` parameter)
- Email and SMS notifications for member events
- Payment integration for membership renewals
- Charts and graphs for manager analytics
- QR code check-ins
- Equipment maintenance scheduling
- Mobile app

## Contributing

1. Create a feature branch.
2. Implement your changes following the project structure above.
3. Test via Swagger UI and the frontend.
4. Open a pull request describing the change.

## License

This project is part of Spring 2026 Computer Science coursework.

## Acknowledgments

- **GitHub Copilot** — AI pair-programming assistant used throughout development to help implement features, debug issues, and speed up code generation.
