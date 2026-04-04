# Modern Full-Stack Auth System (FastAPI + Next.js)

This project is a high-performance, secure authentication system featuring both local (email/username) and Social OAuth (Google).

## 🚀 Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy (Async), PostgreSQL
- **Frontend**: Next.js 15 (App Router), Tailwind CSS, Framer Motion
- **Authentication**: JWT (Access + Refresh), Google OAuth 2.0 via Authlib
- **Database**: PostgreSQL with UUID support

---

## 🛠️ Setup Instructions

### Backend (Python 3.9+)

1.  Navigate to the `/backend` directory.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure your environment in `.env`.
4.  Run the application:
    ```bash
    uvicorn app.main:app --reload
    ```

### Frontend (Next.js)

1.  Navigate to the `/frontend` directory.
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Configure your environment in `.env.local`.
4.  Run the development server:
    ```bash
    npm run dev
    ```

---

## 📁 Architecture Highlights

- **Clean Architecture**: Backend uses a service-based architecture to separate business logic from API routing.
- **Async DB Access**: All database operations use async SQLAlchemy for high performance.
- **Secure JWT**: Dual-token implementation with short-lived access tokens and database-stored refresh tokens.
- **Global Auth State**: Next.js uses React Context and Axios interceptors for automatic token refresh and protected route handling.
- **Premium Design**: Modern UI with glassmorphism, smooth animations, and Inter typography.

---

## 🔒 Security Features

- Encrypted password storage with **bcrypt**.
- **OAuth 2.0** integration for secure third-party login.
- **Cross-Origin Resource Sharing (CORS)** and **Session Middleware** protection.
- Automated **JWT Refresh** mechanism to maintain session continuity.
