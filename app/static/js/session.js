// Treat an expired session as authentication failure, never as an empty contract list.
const originalFetch = window.fetch;
let returningToLogin = false;
window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    if (response.status === 401 && !returningToLogin && location.pathname !== '/login') {
        const url = new URL(typeof args[0] === 'string' ? args[0] : args[0].url, location.origin);
        if (url.origin === location.origin && url.pathname.startsWith('/api/') || url.origin === location.origin && url.pathname.startsWith('/admin/api/')) {
            returningToLogin = true;
            localStorage.removeItem('token');
            location.assign('/login?next=' + encodeURIComponent(location.pathname + location.search + location.hash));
        }
    }
    return response;
};
