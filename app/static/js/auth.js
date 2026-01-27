// app/static/js/auth.js

// 1. Inicializar el cliente globalmente
const { createClient } = supabase;
window.supabaseClient = createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY);

// --- CONFIGURACIÓN DEL TEMPORIZADOR ---
const TIEMPO_LIMITE = 900000; // 15 minutos de inactividad
let temporizadorInactividad;

// Función reutilizable para cerrar sesión
async function realizarLogout() {
    console.log("Cerrando sesión por inactividad o petición del usuario...");
    await window.supabaseClient.auth.signOut();
    localStorage.clear();
    window.location.href = "/";
}

async function cargarDatosUsuario(session) {
    if (!session || !session.user) return;

    // UUID de autenticación (auth.users)
    const authUuid = session.user.id;
    // Correo de autenticación
    const userEmail = session.user.email;
    
    // Elementos del DOM
    const card = document.getElementById('user-profile-card');
    const nameEl = document.getElementById('user-email'); // Aquí mostraremos el Nombre
    const initialsEl = document.getElementById('user-initials');

    if (card && nameEl && initialsEl) {
        
        // Valores por defecto (si falla la consulta, mostramos el correo)
        let textoAMostrar = userEmail;
        let inicial = userEmail.charAt(0).toUpperCase();

        try {
            // --- CONSULTA A LA TABLA usuarios_detalles ---
            // Buscamos donde la columna 'user_id' coincide con el UID de autenticación
            const { data, error } = await window.supabaseClient
                .from('usuarios_detalles')
                .select('nombre, apellido')
                .eq('user_id', authUuid) // <--- USAMOS user_id COMO FORÁNEA
                .maybeSingle(); 

            if (error) {
                console.warn("Error al buscar detalles del usuario:", error.message);
                // No hacemos nada más, se quedará mostrando el correo
            } else if (data) {
                // Si encontramos datos, concatenamos Nombre y Apellido
                const nombreCompleto = `${data.nombre || ''} ${data.apellido || ''}`.trim();
                
                if (nombreCompleto.length > 0) {
                    textoAMostrar = nombreCompleto;
                    // Si hay nombre, usamos su inicial. Si no, mantenemos la del correo.
                    if (data.nombre) {
                        inicial = data.nombre.charAt(0).toUpperCase();
                    }
                }
            } else {
                console.log("Usuario autenticado, pero sin registro en 'usuarios_detalles'.");
            }

        } catch (err) {
            console.error("Error inesperado en cargarDatosUsuario:", err);
        }

        // 1. Actualizar el DOM
        nameEl.textContent = textoAMostrar;
        initialsEl.textContent = inicial;
        
        // 2. Mostrar la tarjeta
        card.classList.remove('hidden');
    }
}

function resetearTemporizador() {
    // Solo activamos el timer si NO estamos en login
    const path = window.location.pathname;
    if (path !== '/' && path !== '/login') {
        clearTimeout(temporizadorInactividad);
        // Reiniciamos el conteo para logout automático
        temporizadorInactividad = setTimeout(realizarLogout, TIEMPO_LIMITE);
    }
}

// ----------------------------------------------

async function checkAuth() {
    // Verificar sesión actual
    const { data: { session } } = await window.supabaseClient.auth.getSession();
    
    const path = window.location.pathname;
    const isLoginPage = path === '/' || path === '/login';
    
    const loadingScreen = document.getElementById('loading-screen');
    // const mainContent = document.getElementById('main-content'); // Opcional si usas wrapper

    // Función auxiliar para quitar pantalla de carga
    const mostrarWeb = () => {
        if(loadingScreen) loadingScreen.style.display = 'none';
        // if(mainContent) mainContent.style.display = 'block';
    };

    if (!session) {
        // --- NO HAY SESIÓN ---
        if (!isLoginPage) {
            // Si intenta entrar a dashboard sin sesión -> Login
            window.location.href = '/';
        } else {
            // Está en login -> Mostrar formulario
            mostrarWeb();
        }
    } else {
        // --- SÍ HAY SESIÓN ---
        if (isLoginPage) {
            // Si intenta entrar a login con sesión -> Dashboard
            window.location.href = '/dashboard';
        } else {
            // Está dentro del sistema -> Cargar datos y activar timers
            mostrarWeb();
            resetearTemporizador();
            cargarDatosUsuario(session); 
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    // Botón manual de cerrar sesión
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await realizarLogout();
        });
    }

    // --- RESETEAR TIMER AL DETECTAR ACTIVIDAD ---
    document.onmousemove = resetearTemporizador;
    document.onkeypress = resetearTemporizador;
    document.onclick = resetearTemporizador;
    document.onscroll = resetearTemporizador;
});