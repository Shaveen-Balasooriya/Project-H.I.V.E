const API_BASE = '/api/honeypot';

export async function checkPort(port) {
    const res = await fetch(`${API_BASE}/port-check/${port}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function getTypes() {
    const res = await fetch(`${API_BASE}/types`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function getTypeAuthDetails(type) {
    const res = await fetch(`${API_BASE}/types/${type}/auth-details`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function createHoneypot(data) {
    const res = await fetch(`${API_BASE}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Failed to create honeypot');
    return res.json();
}

// ...add more as needed (start, stop, delete, etc.)...
