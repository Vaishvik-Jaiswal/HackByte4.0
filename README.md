# Modern Full-Stack Authentication System

A premium, secure authentication system featuring local registration/login and Google OAuth 2.0.

## 🚀 Tech Stack

- **Frontend**: React (Vite) + Tailwind CSS + Framer Motion + Axios
- **Backend**: Node.js + Express + PostgreSQL + Prisma ORM
- **Security**: JWT (Access & Refresh), Passport.js, bcrypt, Helmet

---

## 🛠️ Setup Instructions

### 1. Database (PostgreSQL)
Ensure you have a PostgreSQL instance running. Update the `DATABASE_URL` in `backend/.env` (use `.env.example` as a template).

### 2. Google OAuth Credentials
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- Configure OAuth consent screen.
- Create OAuth 2.0 Client IDs (Web application).
- Set Authorized redirect URI to: `http://localhost:5000/api/auth/google/callback`.

### 3. Backend Setup
```bash
cd backend
npm install
# Create .env based on .env.example and add your secrets
npx prisma migrate dev --name init
npm run dev
```

### 4. Frontend Setup
```bash
cd frontend
npm install
# Create .env based on .env.example
npm run dev
```

---

## 📁 Project Features

### Backend
- **Prisma Schema**: Organized database models with UUIDs and relations.
- **AuthService**: Decoupled business logic for auth operations.
- **JWT System**: Dual-token strategy with short-lived access tokens and long-lived refresh tokens stored in DB.
- **Passport.js**: Robust Google OAuth implementation.

### Frontend
- **Beautiful UI**: Modern glassmorphism design with responsive layouts.
- **AuthContext**: Global state management for authentication.
- **Axios Interceptors**: Automatic JWT attachment and token refresh on 401.
- **Protected Routes**: Secure navigation for private pages.

---

## 🔐 Security Highlights
- Password hashing with **bcrypt**.
- **HttpOnly** cookies potential (currently using localStorage for simplicity, but can be switched).
- **CORS** and **Helmet** protection.
- Token refresh logic to stay logged in without frequent logins.
