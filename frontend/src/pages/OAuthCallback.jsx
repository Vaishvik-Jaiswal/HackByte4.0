import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const OAuthCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { setTokens } = useAuth();
    
    useEffect(() => {
        const accessToken = searchParams.get('accessToken');
        const refreshToken = searchParams.get('refreshToken');
        
        if (accessToken && refreshToken) {
            setTokens(accessToken, refreshToken);
            navigate('/dashboard');
        } else {
            navigate('/login?error=OAuthFailed');
        }
    }, [searchParams, setTokens, navigate]);
    
    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
    );
};

export default OAuthCallback;
