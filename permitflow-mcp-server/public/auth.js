// auth.js - Lightweight Authentication for PermitFlow PRO
// Using Supabase Magic Links for passwordless entry

const SUPABASE_URL = 'https://your-project.supabase.co'; // Placeholders for Vibe check
const SUPABASE_KEY = 'your-public-anon-key';

// Mock Supabase Client if keys are missing to ensure "Vibe" works immediately
const auth = {
    user: JSON.parse(localStorage.getItem('permitflow_user')),
    
    async signInWithGoogle() {
        console.log("[Auth] Redirecting to Google OAuth...");
        // In a real Supabase setup:
        // const { data, error } = await supabase.auth.signInWithOAuth({ provider: 'google', options: { persistSession: true } });
        
        // Simulation for Vibe check
        return { success: true, url: "https://accounts.google.com/o/oauth2/auth" };
    },

    async login(email) {
        console.log(`[Auth] Triggering Magic Link for: ${email}`);
        localStorage.setItem('permitflow_auth_pending', email);
        return { success: true, message: "Check your email for the industrial login link." };
    },

    async verify(email) {
        const mockUser = {
            id: 'sb-' + Math.random().toString(36).slice(2, 11),
            email: email,
            signup_date: new Date().toISOString(),
            is_pro: false // Default to Beta
        };
        this.user = mockUser;
        localStorage.setItem('permitflow_user', JSON.stringify(mockUser));
        return mockUser;
    },

    logout() {
        this.user = null;
        localStorage.removeItem('permitflow_user');
        window.location.reload();
    }
};

window.PermitFlowAuth = auth;
