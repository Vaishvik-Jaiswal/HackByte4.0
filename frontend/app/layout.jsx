import "./globals.css";
import { AuthProvider } from "../context/AuthContext";

export const metadata = {
  title: "Modern Auth",
  description: "Secure Next.js + FastAPI authentication system",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-50 antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
