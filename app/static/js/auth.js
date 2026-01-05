// IMPORTANTE: NO exponer las credenciales aquí
// Las credenciales deben venir del servidor Flask
const SUPABASE_URL = 'https://zozdbgtykvbconmcdhux.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvemRiZ3R5a3ZiY29ubWNkaHV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2OTI1MjcsImV4cCI6MjA3MjI2ODUyN30.CVxChXgChd551-RymWwn-1DQQBDm25avTT-dlWJuTlE';

const { createClient } = supabase;
const supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Sidebar toggle functionality
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('sidebar-hidden');
    overlay.classList.toggle('hidden');
}
const logoutBtn = document.getElementById("logout-btn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    // 1️⃣ Borrar sesión local (si usas login local o token)
    localStorage.clear();
    sessionStorage.clear();

    // 2️⃣ Redirigir al login
    window.location.href = "/login";
  });
}

// Initialize menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleSidebar);
    }

    const sidebarOverlay = document.getElementById('sidebarOverlay');
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', toggleSidebar);
    }

    // Check authentication
    checkAuth();

    // Setup logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
});

// Check if user is authenticated
async function checkAuth() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    
    if (!session) {
        // Redirect to login if not authenticated
        window.location.href = '/';
        return false;
    }
    
    return true;
}

// Handle logout
async function handleLogout() {
    try {
        await supabaseClient.auth.signOut();
        window.location.href = '/';
    } catch (error) {
        console.error('Error al cerrar sesión:', error);
    }
}

// Export for use in other scripts
window.supabaseClient = supabaseClient;
window.checkAuth = checkAuth;