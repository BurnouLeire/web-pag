// app/static/js/auth.js

// 1. Inicializar el cliente globalmente
const { createClient } = supabase;
// Estas variables window.SUPABASE_... se definen en el HTML antes de cargar este script
window.supabaseClient = createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY);

async function checkAuth() {
    const { data: { session } } = await window.supabaseClient.auth.getSession();
    const isLoginPage = window.location.pathname === '/'; // Ajusta si tu ruta de login es distinta

    if (!session && !isLoginPage) {
        window.location.href = '/';
    } else if (session && isLoginPage) {
        window.location.href = '/dashboard';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    // Lógica para el botón de cerrar sesión
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            await window.supabaseClient.auth.signOut();
            localStorage.clear();
            window.location.href = "/";
        });
    }
});