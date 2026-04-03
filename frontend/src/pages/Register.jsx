import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserPlus, Mail, Lock, User, Github, Chrome } from 'lucide-react';
import { motion } from 'framer-motion';

const Register = () => {
    const [formData, setFormData] = useState({ username: '', email: '', password: '', confirmPassword: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (formData.password !== formData.confirmPassword) {
            return setError('Passwords do not match');
        }
        setLoading(true);
        try {
            await register(formData.username, formData.email, formData.password);
            navigate('/login');
        } catch (err) {
            setError(err.response?.data?.error || 'Registration failed. Email or username might already exist.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = () => {
        window.location.href = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'}/auth/google`;
    };

    return (
        <div className="flex items-center justify-center min-h-screen px-4 bg-slate-950 overflow-hidden relative py-12">
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
                        <UserPlus className="w-8 h-8 text-primary-400" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Create Account</h1>
                    <p className="text-slate-400 mt-2">Join us and start your journey today.</p>
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

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1">
                        <label className="text-sm font-medium text-slate-300 ml-1">Username</label>
                        <div className="relative">
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                                <User className="w-5 h-5" />
                            </span>
                            <input 
                                type="text" 
                                name="username" 
                                className="w-full pl-11" 
                                placeholder="vincenzod" 
                                value={formData.username}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-1">
                        <label className="text-sm font-medium text-slate-300 ml-1">Email Address</label>
                        <div className="relative">
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                                <Mail className="w-5 h-5" />
                            </span>
                            <input 
                                type="email" 
                                name="email" 
                                className="w-full pl-11" 
                                placeholder="hello@example.com" 
                                value={formData.email}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-300 ml-1">Password</label>
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
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-slate-300 ml-1">Confirm</label>
                            <div className="relative">
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                                    <Lock className="w-5 h-5" />
                                </span>
                                <input 
                                    type="password" 
                                    name="confirmPassword" 
                                    className="w-full pl-11 border-none" 
                                    placeholder="••••••••" 
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                        </div>
                    </div>

                    <button   
                        type="submit" 
                        id="register-submit"
                        className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
                        disabled={loading}
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-slate-50/30 border-t-slate-50 rounded-full animate-spin"></div>
                        ) : (
                            <>Sign Up</>
                        )}
                    </button>

                    <div className="relative flex items-center justify-center py-4">
                        <div className="w-full border-t border-slate-800"></div>
                        <span className="absolute bg-[#1a2133] px-3 py-1 text-xs text-slate-500 rounded-full border border-slate-700/50 uppercase">OR JOIN WITH GOOGLE</span>
                    </div>

                    <button 
                        type="button" 
                        id="google-register"
                        onClick={handleGoogleLogin} 
                        className="btn-secondary w-full flex items-center justify-center gap-2"
                    >
                        <Chrome className="w-5 h-5 text-red-500" />
                        <span>Continue with Google</span>
                    </button>
                </form>

                <p className="text-center text-slate-400 mt-8 text-sm">
                    Already have an account? {' '}
                    <Link to="/login" id="login-link" className="text-primary-400 font-semibold hover:text-primary-300 transition-colors underline-offset-4 hover:underline">
                        Sign In
                    </Link>
                </p>
            </motion.div>
        </div>
    );
};

export default Register;
