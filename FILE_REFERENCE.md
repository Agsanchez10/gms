# 📚 Project File Reference Guide

## Quick Navigation

**Want to...?**
- Add a new Member field → `backend/models.py` + `backend/schemas/members.py`
- Create a new API endpoint → `backend/routes/*.py`
- Add a frontend page → `frontend/src/pages/YourPage.tsx`
- Call an API → `frontend/src/services/api.ts`
- Handle login → `frontend/src/context/AuthContext.tsx`
- Change styling → `frontend/src/*.css`
- Configure database → `backend/.env`
- Set up project → `backend/setup.sh` or `frontend/setup.sh`

---

## Backend Files Overview

### Core Application Files

#### `backend/main.py` (Main Application)
- **Purpose**: FastAPI application entry point
- **Contains**: 
  - CORS middleware configuration
  - Database initialization
  - All route registrations
  - Health check endpoint
- **Use**: Run with `uvicorn main:app --reload`

#### `backend/models.py` (Database Models)
- **Purpose**: SQLAlchemy ORM models for 7 entities
- **Entities**: Member, Staff, Class, Machine, MemberPlan, Membership, MachineUsage
- **Features**: 
  - Enum types for status/roles
  - Relationships between entities
  - Automatic timestamps (created_at, updated_at)
- **Modify**: When adding/changing database fields

#### `backend/database.py` (Database Configuration)
- **Purpose**: Database connection and session management
- **Contains**:
  - Engine creation with connection pooling
  - SessionLocal factory
  - Base class for all models
  - Dependency injection helper (get_db)
- **Modify**: For database pool settings or engine options

#### `backend/config.py` (Application Settings)
- **Purpose**: Configuration management
- **Reads from**: Environment variables (.env)
- **Settings**:
  - Database URLs
  - Debug mode
  - CORS origins
  - API versioning
- **Modify**: For new environment variables

#### `backend/auth.py` (Authentication & Authorization)
- **Purpose**: Role-based access control (RBAC)
- **Functions**:
  - `hash_password()` - Secure password hashing
  - `verify_password()` - Password validation
  - `authenticate_staff()` - Login verification
  - `get_current_staff()` - Current user retrieval
  - `require_role()` - Role-based decorators
- **Modify**: For enhanced security measures

---

### Route Modules (`backend/routes/`)

#### `members.py` (Member Management)
- **Endpoints**: 7 endpoints
- **Features**: CRUD + membership tracking
- **Key Functions**:
  - List members with filtering
  - Get member details + membership history
  - Create new member (with duplicate email check)
  - Update member info or status
  - Soft delete (mark inactive)
  - Get current active membership

#### `staff.py` (Authentication)
- **Endpoints**: 4 endpoints
- **Features**: Login, registration, staff management
- **Key Functions**:
  - User login
  - Create staff account (Manager only)
  - List staff
  - Get staff details

#### `classes.py` (Class Management)
- **Endpoints**: 8 endpoints
- **Features**: CRUD + enrollment + attendance
- **Key Functions**:
  - List/create/update/delete classes
  - Enroll members (with capacity check)
  - Remove members from class
  - Mark attendance (check-in)

#### `machines.py` (Machine Management)
- **Endpoints**: 6 endpoints
- **Features**: Equipment inventory management
- **Key Functions**:
  - List machines with filtering
  - Add/update/delete machines
  - Get machine status
  - Mark as retired (soft delete)

#### `usage.py` (Machine Usage Tracking)
- **Endpoints**: 6 endpoints
- **Features**: Track member machine usage
- **Key Functions**:
  - Start machine usage (sign-in)
  - End machine usage (sign-out)
  - Get usage history by machine or member
  - Generate usage statistics

#### `plans.py` (Membership Plans)
- **Endpoints**: 5 endpoints
- **Features**: Manage subscription plans
- **Key Functions**: CRUD for plans (Basic, Premium, VIP)

#### `memberships.py` (Membership Management)
- **Endpoints**: 3 endpoints
- **Features**: Enroll members in plans
- **Key Functions**:
  - Enroll member in plan
  - Get current membership
  - Renew expired membership

#### `manager.py` (Analytics & Reports)
- **Endpoints**: 6 endpoints
- **Features**: Manager dashboard analytics
- **Key Functions**:
  - Dashboard overview stats
  - Machine usage analytics
  - Class enrollment analytics
  - Membership status
  - Staff distribution
  - Top members by usage

#### `trainer.py` (Trainer Features)
- **Endpoints**: 3 endpoints
- **Features**: Trainer-specific tools
- **Key Functions**:
  - List trainer's classes
  - Get class roster
  - Get attendance stats

---

### Schema Modules (`backend/schemas/`)

#### `members.py` (Member Schemas)
- **Classes**:
  - `MemberBase` - Common fields
  - `MemberCreate` - For creating members
  - `MemberUpdate` - For partial updates
  - `MemberResponse` - Return data
  - `MembershipResponse` - Membership details
  - `MemberPlanResponse` - Plan details
- **Purpose**: Request/response validation

#### `staff.py` (Staff Schemas)
- **Classes**:
  - `StaffBase` - Common staff fields
  - `StaffCreate` - Registration data
  - `StaffLogin` - Login credentials
  - `StaffResponse` - Staff details
  - `StaffLoginResponse` - Login success response

#### `classes.py` (Class Schemas)
- **Classes**:
  - `ClassBase` - Common fields
  - `ClassCreate` - Create class
  - `ClassUpdate` - Update class
  - `ClassResponse` - Return data
  - `ClassDetailedResponse` - With roster

#### `machines.py` (Machine Schemas)
- **Classes**:
  - `MachineBase` - Common fields
  - `MachineCreate` - Create machine
  - `MachineUpdate` - Update status/notes
  - `MachineResponse` - Return data
  - `MachineUsageStart` - Start usage
  - `MachineUsageResponse` - Usage data

#### `analytics.py` (Analytics Schemas)
- **Classes**:
  - `MachineUsageStats` - Machine statistics
  - `ClassEnrollmentStats` - Class statistics
  - `MembershipStats` - Member statistics
  - `ManagerDashboardStats` - Overview

---

### Configuration Files

#### `.env.example` (Environment Template)
- **Purpose**: Example environment variables
- **Copy to**: `.env` (add real credentials)
- **Contains**: Database URL, API settings, CORS origins

#### `requirements.txt` (Python Dependencies)
- **Purpose**: Lists all Python packages needed
- **Used by**: `pip install -r requirements.txt`
- **Packages**:
  - fastapi, uvicorn (web framework)
  - sqlalchemy, psycopg2 (database)
  - pydantic (validation)
  - python-dotenv (env config)
  - passlib, bcrypt (password hashing)

#### `seed_data.py` (Demo Data Script)
- **Purpose**: Populate database with demo data
- **Creates**:
  - 3 staff accounts (manager, trainer, reception)
  - 5 sample members
  - 3 membership plans
  - 3 fitness classes
  - 8 machines
- **Run**: `python seed_data.py` (after setup)

#### `setup.bat` & `setup.sh` (Setup Scripts)
- **Purpose**: Automated environment setup
- **Does**:
  - Creates virtual environment
  - Installs dependencies
  - Copies .env template
  - Initializes database
- **Run**: Windows `setup.bat` or Linux/Mac `bash setup.sh`

---

## Frontend Files Overview

### Pages (`frontend/src/pages/`)

#### `LoginPage.tsx` (Authentication)
- **Purpose**: Staff login interface
- **Features**:
  - Email/password input
  - Error display
  - demo credentials reference
  - Redirects to appropriate dashboard
- **Uses**: `useAuth()`, `staffAPI.login()`

#### `ReceptionDashboard.tsx` (Reception Staff View)
- **Purpose**: Member and machine management
- **Tabs**:
  - Dashboard - Overview
  - Members - List members
  - Machines - Check status
  - Classes - View classes
- **Features**: Sign in members, manage classes

#### `TrainerDashboard.tsx` (Trainer View)
- **Purpose**: Class management for trainers
- **Tabs**:
  - My Classes - Trainer's classes
  - Schedule - Class calendar
- **Features**: View rosters, manage attendance

#### `ManagerDashboard.tsx` (Manager View)
- **Purpose**: Analytics and reporting
- **Tabs**:
  - Overview - System statistics
  - Machines - Machine usage analytics
  - Classes - Class enrollment stats
  - Members - Membership statistics
- **Features**: View charts, generate reports

---

### Services (`frontend/src/services/`)

#### `api.ts` (API Client)
- **Purpose**: All API calls to backend
- **Contains**: ~50 typed API functions
- **Organized by**: memberAPI, staffAPI, classAPI, machineAPI, etc.
- **Features**:
  - Axios instance with base URL
  - Error handling
  - Full TypeScript types
- **Pattern**: Each API group (member, staff, etc.)

---

### Context (`frontend/src/context/`)

#### `AuthContext.tsx` (Authentication State)
- **Purpose**: Manage logged-in user state
- **Provides**:
  - `useAuth()` hook
  - `AuthProvider` wrapper
  - User data persistence (localStorage)
- **Features**:
  - Auto-login from localStorage
  - User object with role info
  - setUser() for updates

---

### Core Files

#### `App.tsx` (Main App Component)
- **Purpose**: Top-level component and routing
- **Features**:
  - React Router setup
  - Role-based route protection
  - Redirects based on user role
- **Routes**: Login, Dashboard (by role)

#### `main.tsx` (Entry Point)
- **Purpose**: ReactDOM rendering
- **Contains**: 
  - Root element mounting
  - AuthProvider wrapper
  - React.StrictMode

#### `App.css` (Styling)
- **Purpose**: Global and component styles
- **Includes**:
  - Navbar styling
  - Card and form styles
  - Alert and button styles
  - Utility classes

#### `index.css` (Base Styles)
- **Purpose**: CSS reset and base styling
- **Includes**:
  - Root variables
  - Typography
  - Form elements
  - Utility classes

---

### Configuration Files

#### `package.json` (Node Dependencies)
- **Purpose**: Lists all JavaScript packages
- **Scripts**:
  - `npm run dev` - Start dev server
  - `npm run build` - Create production build
- **Packages**: React, Axios, React Router, etc.

#### `vite.config.ts` (Build Configuration)
- **Purpose**: Vite bundler configuration
- **Features**:
  - React plugin
  - Dev server proxy to backend
  - Port and HTTPS settings

#### `tsconfig.json` (TypeScript Rules)
- **Purpose**: TypeScript compiler configuration
- **Enables**: Strict mode, JSX support, path mapping

#### `tsconfig.node.json` (TypeScript for Config)
- **Purpose**: TypeScript rules for config files
- **Used by**: vite.config.ts compilation

#### `setup.bat` & `setup.sh` (Setup Scripts)
- **Purpose**: Project initialization
- **Does**:
  - Checks for Node.js
  - Installs npm dependencies
  - Runs production build check
- **Run**: Windows `setup.bat` or Linux/Mac `bash setup.sh`

---

## Documentation Files

#### `README.md` (Project Guide)
- **Contains**: Architecture, features, setup, API docs
- **Best for**: Complete project understanding

#### `QUICKSTART.md` (Quick Reference)
- **Contains**: Minimal setup steps
- **Best for**: Getting running quickly

#### `PROJECT_STATUS.md` (Implementation Details)
- **Contains**: What's completed, statistics
- **Best for**: Project overview

#### `IMPLEMENTATION_COMPLETE.md` (Summary)
- **Contains**: What's done, how to test
- **Best for**: Understanding deliverables

#### `SETUP_CHECKLIST.md` (Step-by-Step)
- **Contains**: Detailed checklist
- **Best for**: Verification and testing

#### `.gitignore` (Git Configuration)
- **Purpose**: Files to ignore in version control
- **Ignores**: venv, node_modules, .env, logs, etc.

---

## File Modification Guide

### When You Need to...

**Add a new Member field:**
1. Update `backend/models.py` - Add Column
2. Update `backend/schemas/members.py` - Add to Pydantic schema
3. Update `frontend/src/pages/ReceptionDashboard.tsx` - Add form field
4. Run migration or restart app

**Create a new API endpoint:**
1. Create function in `backend/routes/your_module.py`
2. Add it to router
3. Import in `backend/main.py` and include
4. Add to `frontend/src/services/api.ts`
5. Use in frontend component

**Change styling:**
1. Modify `frontend/src/App.css` for app-wide styles
2. Modify `frontend/src/pages/YourPage.tsx` for inline styles
3. Or create new `.css` file for component

**Add a new dashboard:**
1. Create `frontend/src/pages/YourDashboard.tsx`
2. Add route in `frontend/src/App.tsx`
3. Update navigation logic
4. Add API calls via `src/services/api.ts`

**Change database config:**
1. Edit `backend/.env`
2. Restart backend server
3. Or modify `backend/config.py` logic

---

## File Dependencies Map

```
main.py
├── config.py (settings)
├── database.py (sessions)
├── auth.py (permissions)
├── routes/
│   ├── members.py (uses: models, schemas, db)
│   ├── staff.py (uses: models, schemas, auth, db)
│   ├── classes.py (uses: models, schemas, auth, db)
│   └── ... (all routes similar)
└── models.py (defines all entities)
    └── database.py (Base class)

App.tsx
├── context/AuthContext.tsx (auth state)
├── pages/
│   ├── LoginPage.tsx (staffAPI.login)
│   ├── ReceptionDashboard.tsx (memberAPI, classAPI, machineAPI)
│   ├── TrainerDashboard.tsx (trainerAPI)
│   └── ManagerDashboard.tsx (managerAPI)
└── services/api.ts (all API calls)
```

---

**Tip**: All files have comments and are well-documented. Check inside any file for detailed function documentation!
