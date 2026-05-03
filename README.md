# Gym Management System

A comprehensive web-based Gym Management System with role-based dashboards for managing members, classes, and equipment usage.

## Project Structure

```
gym-management-system/
├── backend/              # FastAPI backend application
│   ├── routes/          # API route handlers (members, staff, classes,
│   │                    #   machines, usage, plans, memberships,
│   │                    #   manager, trainer)
│   ├── schemas/         # Pydantic validation schemas
│   ├── models.py        # SQLAlchemy ORM models
│   ├── main.py          # FastAPI app entry point & router registration
│   ├── config.py        # Configuration settings
│   ├── database.py      # Database session management
│   ├── auth.py          # Authentication & authorization
│   ├── import_csv.py    # CSV data import utility
│   ├── seed_data.py     # Demo data seeder
│   ├── requirements.txt # Python dependencies
│   └── .env.example     # Environment variables template
├── frontend/            # React TypeScript frontend
│   ├── src/
│   │   ├── pages/       # Dashboard pages (Login, Manager, Reception,
│   │   │                #   Trainer)
│   │   ├── components/  # Reusable React components (currently empty)
│   │   ├── services/    # API service layer (api.ts)
│   │   ├── context/     # React context (AuthContext)
│   │   ├── App.tsx      # Main app component
│   │   └── main.tsx     # Entry point
│   ├── package.json     # Node dependencies
│   ├── vite.config.ts   # Vite configuration
│   └── tsconfig.json    # TypeScript configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM + psycopg2 driver
- **Authentication**: Session-based RBAC via `staff_id` query parameter
- **API Documentation**: OpenAPI / Swagger (auto-generated at `/docs`)

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Form Management**: React Hook Form

### Database
- **DBMS**: PostgreSQL
- **Schema**: ER diagram-based design with:
  - Members, Staff, Classes, Machines
  - Relationships: Memberships, ClassEnrollment, MachineUsage

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
│    • Axios interceptor attaches ?staff_id=<id> to every     │
│      request so the backend can verify the caller's role    │
└────────────────────┬────────────────────────────────────────┘
                     │  HTTP/JSON  (CORS: localhost:3000/5173/8000)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Application Layer  (FastAPI · Python · localhost:8000)     │
│                                                             │
│  main.py — CORS middleware, startup init_db(), 9 routers    │
│                                                             │
│  Request pipeline per endpoint:                             │
│    1. Pydantic v2 schema  — type & constraint validation    │
│    2. require_role()      — RBAC (MANAGER/TRAINER/         │
│                              RECEPTION); raises 403 if fail │
│    3. Route handler       — business logic + duplicate      │
│                              checks                         │
│    4. SQLAlchemy ORM /    — parameterised queries;          │
│       text() + params       injection-safe                  │
│    5. get_db() dependency — per-request session, always     │
│                              closed in finally block        │
│                                                             │
│  Routers under /api/v1/:                                    │
│    members · staff · classes · machines · usage · plans     │
│    memberships · manager · trainer                          │
└────────────────────┬────────────────────────────────────────┘
                     │  SQLAlchemy + psycopg2
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Database  (PostgreSQL 12+ · port 5432 · gym_db)           │
│                                                             │
│  Connection pool: 10 persistent + 20 overflow connections   │
│  pool_pre_ping=True — stale connections discarded           │
│                                                             │
│  7 entity tables:                                           │
│    member · member_plan · membership · staff                │
│    class · machine · machine_usage                          │
│  1 association table:  class_enrollment                     │
│                                                             │
│  Schema managed by SQLAlchemy metadata (init_db on start)  │
└─────────────────────────────────────────────────────────────┘
```

**Data flow example — Reception signs a member into a machine:**
1. `ReceptionDashboard` calls `usageAPI.startUsage(machineId, memberId)` in `api.ts`
2. Axios sends `POST /api/v1/machines/{id}/start?staff_id=<id>` to FastAPI
3. `require_role(RECEPTION, TRAINER, MANAGER)` verifies the caller's role via a DB lookup on `staff`
4. Route handler confirms the machine and member exist, checks member is not suspended
5. SQLAlchemy `text()` inserts a row into `machine_usage` with `NOW()` as `start_time`
6. JSON response returns the new `usage_id` to the frontend

## Features

### Member Management
- Register new members with personal information
- Manage membership plans (Basic, Premium, VIP)
- Track membership status (Active, Inactive, Suspended)
- View member history and usage

### Class Management
- Create and manage fitness classes
- Assign trainers to classes
- Enroll/remove members from classes
- Track attendance and check-ins

### Machine Usage Tracking
- Track member machine usage (start/end times)
- View usage statistics and analytics
- Manage machine status (Available, Maintenance, Retired)
- Generate usage reports by machine or member

### Role-Based Dashboards

#### Reception Staff
- Sign members into the gym
- Register new members
- View machine status
- Manage class enrollments

#### Trainers
- View assigned classes
- Check class rosters
- Mark attendance

#### Managers
- View comprehensive analytics
- Track machine usage statistics
- Monitor class enrollment
- Generate membership reports
- Create staff accounts

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+

### Backend Setup

```bash
cd backend
```

**Option A — Automated setup script (recommended)**
```bash
# Windows
setup.bat

# Linux / Mac
bash setup.sh
```

**Option B — Manual setup**

1. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install Python dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables
   ```bash
   cp .env.example .env   # Windows: copy .env.example .env
   # Edit .env with your PostgreSQL credentials
   ```

**Then (both options):**
```bash
python seed_data.py      # Populate demo data
uvicorn main:app --reload
```
Backend available at `http://localhost:8000` · API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
```

**Option A — Automated setup script (recommended)**
```bash
# Windows
setup.bat

# Linux / Mac
bash setup.sh
```

**Option B — Manual setup**
```bash
npm install
```

**Then (both options):**
```bash
npm run dev
```
Frontend available at `http://localhost:5173`

## API Documentation

### Staff / Auth Endpoints
- `POST /api/v1/staff/login` — Staff login
- `POST /api/v1/staff/register` — Create staff account (Manager only)
- `GET /api/v1/staff/` — List all staff
- `GET /api/v1/staff/{staff_id}` — Get staff details

### Member Endpoints
- `GET /api/v1/members/` — List all members (supports `status_filter`)
- `GET /api/v1/members/{member_id}` — Get member details
- `POST /api/v1/members/` — Create new member
- `PUT /api/v1/members/{member_id}` — Update member
- `DELETE /api/v1/members/{member_id}` — Delete member
- `PATCH /api/v1/members/{member_id}/status` — Update member status
- `GET /api/v1/members/{member_id}/current-membership/` — Get active membership
- `GET /api/v1/members/{member_id}/usage` — Get machine usage history

### Class Endpoints
- `GET /api/v1/classes/` — List classes (supports `trainer_id` filter)
- `GET /api/v1/classes/{class_id}` — Get class details
- `POST /api/v1/classes/` — Create class
- `PUT /api/v1/classes/{class_id}` — Update class
- `DELETE /api/v1/classes/{class_id}` — Delete class
- `POST /api/v1/classes/{class_id}/enroll/{member_id}` — Enroll member
- `DELETE /api/v1/classes/{class_id}/enroll/{member_id}` — Remove member
- `PUT /api/v1/classes/{class_id}/checkin/{member_id}` — Mark attendance

### Machine Endpoints
- `GET /api/v1/machines/` — List machines (supports `status_filter`, `category_filter`)
- `GET /api/v1/machines/{machine_id}` — Get machine details
- `POST /api/v1/machines/` — Add machine
- `PUT /api/v1/machines/{machine_id}` — Update machine
- `DELETE /api/v1/machines/{machine_id}` — Delete machine
- `PATCH /api/v1/machines/{machine_id}/status` — Update machine status
- `GET /api/v1/machines/{machine_id}/usage` — Get usage history for machine

### Machine Usage Endpoints
- `POST /api/v1/machines/{machine_id}/start` — Start machine session (sign in member)
- `PUT /api/v1/machines/{machine_id}/end/{usage_id}` — End machine session
- `GET /api/v1/stats/machine/{machine_id}` — Usage stats for a machine
- `GET /api/v1/stats/member/{member_id}` — Usage stats for a member

### Plan Endpoints
- `GET /api/v1/plans/` — List all plans
- `GET /api/v1/plans/{plan_id}` — Get plan details
- `POST /api/v1/plans/` — Create plan
- `PUT /api/v1/plans/{plan_id}` — Update plan
- `DELETE /api/v1/plans/{plan_id}` — Delete plan

### Membership Endpoints
- `POST /api/v1/memberships/members/{member_id}/enroll` — Enroll member in plan
- `GET /api/v1/memberships/members/{member_id}/current` — Get current membership
- `PUT /api/v1/memberships/members/{member_id}/{plan_id}/renew` — Renew membership

### Trainer Dashboard Endpoints
- `GET /api/v1/trainer/my-classes` — Classes taught by the logged-in trainer
- `GET /api/v1/trainer/classes/{class_id}/roster` — Full roster for a class

### Manager Analytics Endpoints
- `GET /api/v1/manager/dashboard/overview` — Dashboard summary stats
- `GET /api/v1/manager/analytics/machine-usage` — Machine usage analytics (supports `days`)
- `GET /api/v1/manager/analytics/class-enrollment` — Class enrollment stats
- `GET /api/v1/manager/analytics/membership-status` — Membership status breakdown
- `GET /api/v1/manager/analytics/staff-roles` — Staff role distribution
- `GET /api/v1/manager/analytics/top-members` — Most active members

See full API documentation at `http://localhost:8000/docs` (Swagger UI)

## Environment Variables

### Backend (.env)
Copy `backend/.env.example` to `backend/.env` and fill in your credentials.
```
DATABASE_URL=postgresql://user:password@localhost:5432/gym_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=gym_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DEBUG=True
API_TITLE=Gym Management System API
API_VERSION=1.0.0
```
CORS origins (`localhost:3000`, `localhost:5173`, `localhost:8000`) are hardcoded in `config.py` and do not need to be set in `.env`.

## Database Schema

### Core Tables
- **Member**: User profiles, status, membership details
- **Staff**: Employee accounts with roles (Reception, Trainer, Manager)
- **MemberPlan**: Subscription plans (Basic, Premium, VIP)
- **Membership**: Active memberships linking Members to Plans
- **Class**: Fitness classes with trainer assignment
- **Machine**: Equipment with status tracking
- **ClassEnrollment** (junction): Member-to-Class many-to-many
- **MachineUsage** (junction): Member-to-Machine usage tracking

### Relationships
- Member → Membership (1:Many)
- Membership → MemberPlan (Many:1)
- Staff → Class (1:Many)
- Class ↔ Member (Many:Many via ClassEnrollment)
- Machine ↔ Member (Many:Many via MachineUsage)

## Development Workflow

### Adding a New Feature

1. **Backend**
   - Define ORM model or modify existing in `models.py`
   - Create Pydantic schemas in `schemas/`
   - Implement API routes in `routes/`
   - Add authentication checks if needed

2. **Frontend**
   - Create API service function in `src/services/api.ts`
   - Build React component in `src/components/`
   - Integrate into dashboard page

3. **Testing**
   - Test API endpoints via Swagger UI at `/docs`
   - Verify frontend integration

## Security Considerations

- Passwords are hashed before storage
- Role-based access control on all protected endpoints
- CORS configured for frontend domain
- Input validation via Pydantic schemas
- Database connection pooling enabled

## Future Enhancements

- JWT token authentication with refresh tokens
- Email notifications for member events
- Payment integration for membership renewals
- Advanced analytics with charts/graphs
- Mobile app version
- SMS notifications
- QR code check-ins
- Equipment maintenance scheduling

## Demo Login Credentials

After running `python seed_data.py`, use these accounts:

| Role      | Email                  | Password    |
|-----------|------------------------|-------------|
| Manager   | manager@gym.com        | password123 |
| Trainer   | trainer@gym.com        | password123 |
| Reception | reception@gym.com      | password123 |

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify database credentials in `.env`
- Ensure port 8000 is available; if not: `uvicorn main:app --reload --port 8001`

### Frontend can't connect to API
- Verify backend is running on http://localhost:8000
- Check CORS settings in `backend/main.py`
- Browser console for specific errors
- If port 5173 is taken: `npm run dev -- --port 5174`

### Database errors
- Ensure PostgreSQL user has proper permissions
- Check database name matches `.env`
- Review database logs for detailed errors

## Contributing

1. Create a feature branch
2. Implement changes following project structure
3. Test thoroughly
4. Submit pull request with description

## License

This project is part of the Spring 2026 Computer Science coursework.

## Support

For issues or questions, contact the project team or instructor.
#   g m s  
 