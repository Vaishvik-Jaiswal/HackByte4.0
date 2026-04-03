import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, Mail, Lock, User, Github, Chrome } from 'lucide-react';
import { motion } from 'framer-motion';

const Login = () => {
    const [formData, setFormData] = useState({ identifier: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(formData.identifier, formData.password);
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = () => {
        window.location.href = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'}/auth/google`;
    };

    return (
        <div className="flex items-center justify-center min-h-screen px-4 bg-slate-950 overflow-hidden relative">
            {/* Background elements */}
            <div className="absolute top-0 left-0 w-64 h-64 bg-primary-900/20 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2 shadow-primary-500/20"></div>
            <div className="absolute bottom-0 right-0 w-80 h-80 bg-blue-900/20 rounded-full blur-[120px] translate-x-1/2 translate-y-1/2 shadow-blue-500/20"></div>

            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-md glass-morphism p-8 md:p-10 rounded-2xl relative z-10"
            >
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-500/10 rounded-2xl mb-4 border border-primary-500/20 shadow-inner">
                        <LogIn className="w-8 h-8 text-primary-400" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Welcome Back</h1>
                    <p className="text-slate-400 mt-2">Please enter your details to sign in.</p>
                </div>

                {error && (
                    <motion.div 
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="bg-red-500/10 border border-red-500/20 text-red-100 p-3 rounded-lg mb-6 text-sm flex items-start gap-2"
                    >
                        <span className="shrink-0 block w-1 h-full bg-red-400 rounded-full"></span>
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="space-y-1">
                        <label className="text-sm font-medium text-slate-300 ml-1">Username or Email</label>
                        <div className="relative">
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                                <User className="w-5 h-5" />
                            </span>
                            <input 
                                type="text" 
                                name="identifier" 
                                className="w-full pl-11" 
                                placeholder="Enter username or email" 
                                value={formData.identifier}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <div className="flex items-center justify-between px-1">
                            <label className="text-sm font-medium text-slate-300">Password</label>
                            <Link to="/forgot-password" name="forgot-password" id="forgot-password" className="text-xs text-primary-400 hover:text-primary-300 transition-colors">Forgot Password?</Link>
                        </div>
                        <div className="relative">
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                                <Lock className="w-5 h-5" />
                            </span>
                            <input 
                                type="password" 
                                name="password" 
                                className="w-full pl-11" 
                                placeholder="••••••••" 
                                value={formData.password}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <button   
                        type="submit" 
                        id="login-submit"
                        className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
                        disabled={loading}
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-slate-50/30 border-t-slate-50 rounded-full animate-spin"></div>
                        ) : (
                            <>Sign In</>
                        )}
                    </button>

                    <div className="relative flex items-center justify-center py-4">
                        <div className="w-full border-t border-slate-800"></div>
                        <span className="absolute bg-[#1a2133] px-3 py-1 text-xs text-slate-500 rounded-full border border-slate-700/50">OR CONTINUE WITH</span>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                        <button 
                            type="button" 
                            id="google-login"
                            onClick={handleGoogleLogin} 
                            className="btn-secondary flex items-center justify-center gap-2"
                        >
                            <Chrome className="w-5 h-5 text-red-500" />
                            <span>Continue with Google</span>
                        </button>
                    </div>
                </form>

                <p className="text-center text-slate-400 mt-8 text-sm">
                    Don't have an account? {' '}
                    <Link to="/register" id="register-link" className="text-primary-400 font-semibold hover:text-primary-300 transition-colors underline-offset-4 hover:underline">
                        Create Account
                    </Link>
                </p>
            </motion.div>
        </div>
    );
};

export default Login;
