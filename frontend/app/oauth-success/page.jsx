"use client";

import { useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';

export default function OAuthSuccessPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { setTokens } = useAuth();
    
    useEffect(() => {
        const accessToken = searchParams.get('access_token');
        const refreshToken = searchParams.get('refresh_token');
        
        if (accessToken && refreshToken) {
            setTokens(accessToken, refreshToken);
            router.push('/dashboard');
        } else {
            router.push('/login?error=OAuthFailed');
        }
    }, [searchParams, setTokens, router]);
    
    return (
        <div className="flex items-center justify-center min-h-screen bg-slate-950">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
    );
}
