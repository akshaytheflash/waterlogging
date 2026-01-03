const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const db = require('./db');
const path = require('path');
const multer = require('multer');

const app = express();
const PORT = 3000;
const JWT_SECRET = 'delhi_water_secret_key_2024';
const GEMINI_API_KEY = 'AIzaSyBJ834s2Ij82GCjfKn7sVDXoI4mCazfnvY';
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

// Helper to get model with fallback
async function generateContentSafe(prompt) {
    const models = ["gemma-3-27b-it", "gemini-1.5-flash", "gemini-pro"];

    for (const modelName of models) {
        try {
            const model = genAI.getGenerativeModel({ model: modelName });
            const result = await model.generateContent(prompt);
            const response = await result.response;
            return response.text();
        } catch (e) {
            console.warn(`Model ${modelName} failed, trying next...`);
        }
    }
    throw new Error("All AI models failed.");
}

// Chat helper with fallback
async function startChatSafe(history, message, systemPrompt) {
    const models = ["gemma-3-27b-it", "gemini-1.5-flash", "gemini-pro"];

    for (const modelName of models) {
        try {
            const model = genAI.getGenerativeModel({ model: modelName });
            const chat = model.startChat({
                history: history,
                generationConfig: { maxOutputTokens: 500 },
            });
            const result = await chat.sendMessage(systemPrompt + "\nUser: " + message);
            const response = await result.response;
            return response.text();
        } catch (e) {
            console.warn(`Chat Model ${modelName} failed, trying next...`);
        }
    }
    throw new Error("All AI models failed.");
}

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// Multer setup for image uploads (simulated storage in memory or local for now)
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, path.join(__dirname, '../public/uploads'));
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});
const upload = multer({ storage: storage });

// Create uploads directory if not exists
const fs = require('fs');
const uploadDir = path.join(__dirname, '../public/uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

// Middleware for JWT Verification
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (!token) return res.sendStatus(401);

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
};

// --- AUTH ROUTES ---

app.post('/api/auth/register', async (req, res) => {
    const { username, password, role, full_name } = req.body;
    try {
        const hashedPassword = await bcrypt.hash(password, 10);
        const result = await db.query(
            'INSERT INTO users (username, password_hash, role, full_name) VALUES ($1, $2, $3, $4) RETURNING id, username, role',
            [username, hashedPassword, role, full_name]
        );
        res.status(201).json(result.rows[0]);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'User already exists or database error' });
    }
});

app.post('/api/auth/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const result = await db.query('SELECT * FROM users WHERE username = $1', [username]);
        if (result.rows.length === 0) return res.status(400).json({ error: 'User not found' });

        const user = result.rows[0];
        const validPassword = await bcrypt.compare(password, user.password_hash);
        if (!validPassword) return res.status(400).json({ error: 'Invalid password' });

        const token = jwt.sign({ id: user.id, username: user.username, role: user.role }, JWT_SECRET);
        res.json({ token, user: { id: user.id, username: user.username, role: user.role, full_name: user.full_name } });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Database error' });
    }
});

// --- AUTHORITY ROUTES ---

app.get('/api/authorities', async (req, res) => {
    try {
        const result = await db.query('SELECT * FROM authorities');
        res.json(result.rows);
    } catch (err) {
        res.status(500).json({ error: 'Database error' });
    }
});

// --- REPORT ROUTES ---

app.post('/api/reports', authenticateToken, upload.single('image'), async (req, res) => {
    const { title, description, severity, lat, lng, assigned_authority_id } = req.body;
    const imageUrl = req.file ? `/uploads/${req.file.filename}` : null;
    try {
        const result = await db.query(
            'INSERT INTO reports (reporter_id, title, description, severity, status, assigned_authority_id, lat, lng, image_url) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *',
            [req.user.id, title, description, severity, 'Open', assigned_authority_id, lat, lng, imageUrl]
        );
        res.status(201).json(result.rows[0]);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Database error' });
    }
});

app.get('/api/reports', async (req, res) => {
    const { authority_id, status } = req.query;
    let query = 'SELECT r.*, u.full_name as reporter_name, a.name as authority_name FROM reports r JOIN users u ON r.reporter_id = u.id JOIN authorities a ON r.assigned_authority_id = a.id';
    let params = [];

    if (authority_id || status) {
        query += ' WHERE';
        if (authority_id) {
            params.push(authority_id);
            query += ` r.assigned_authority_id = $${params.length}`;
        }
        if (status) {
            if (params.length > 0) query += ' AND';
            params.push(status);
            query += ` r.status = $${params.length}`;
        }
    }

    query += ' ORDER BY r.created_at DESC';

    try {
        const result = await db.query(query, params);
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Database error' });
    }
});

app.put('/api/reports/:id/resolve', authenticateToken, upload.single('proof_image'), async (req, res) => {
    if (req.user.role !== 'authority') return res.status(403).json({ error: 'Only authorities can resolve reports' });

    const { id } = req.params;
    const { note } = req.body;
    const proofImageUrl = req.file ? `/uploads/${req.file.filename}` : null;

    try {
        const result = await db.query(
            'UPDATE reports SET status = $1, resolved_at = CURRENT_TIMESTAMP, resolution_proof_image = $2, resolution_note = $3 WHERE id = $4 RETURNING *',
            ['Resolved', proofImageUrl, note, id]
        );
        res.json(result.rows[0]);
    } catch (err) {
        res.status(500).json({ error: 'Database error' });
    }
});

app.post('/api/reports/:id/upvote', authenticateToken, async (req, res) => {
    const { id } = req.params;
    try {
        await db.query('INSERT INTO upvotes (report_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', [id, req.user.id]);
        res.sendStatus(201);
    } catch (err) {
        res.status(500).json({ error: 'Database error' });
    }
});

app.get('/api/reports/:id/upvotes', async (req, res) => {
    const { id } = req.params;
    try {
        const result = await db.query('SELECT COUNT(*) FROM upvotes WHERE report_id = $1', [id]);
        res.json({ count: parseInt(result.rows[0].count) });
    } catch (err) {
        res.status(500).json({ error: 'Database error' });
    }
});

app.post('/api/reports/:id/comments', authenticateToken, async (req, res) => {
    const { id } = req.params;
    const { text } = req.body;
    try {
        const result = await db.query(
            'INSERT INTO comments (report_id, user_id, comment_text) VALUES ($1, $2, $3) RETURNING *',
            [id, req.user.id, text]
        );
        res.status(201).json(result.rows[0]);
    } catch (err) {
        res.status(500).json({ error: 'Database error' });
    }
});

app.get('/api/reports/:id/comments', async (req, res) => {
    const { id } = req.params;
    try {
        const result = await db.query(
            'SELECT c.*, u.full_name FROM comments c JOIN users u ON c.user_id = u.id WHERE c.report_id = $1 ORDER BY c.created_at ASC',
            [id]
        );
        res.json(result.rows);
    } catch (err) {
        res.status(500).json({ error: 'Database error' });
    }
});

// --- HOTSPOT ROUTES ---

app.get('/api/hotspots', async (req, res) => {
    try {
        const result = await db.query('SELECT * FROM hotspots');
        res.json(result.rows);
    } catch (err) {
        res.status(500).json({ error: 'Database error' });
    }
});

// --- AI ROUTES ---

app.post('/api/ai/predict-authority', async (req, res) => {
    const { description, location } = req.body;
    const prompt = `You are a Delhi Government dispatcher. Based on this report: "${description}" at location "${location}", identify which authority should handle it:
    - MCD (Municipal Corporation of Delhi): For local colony roads, internal drains, and garbage related flooding.
    - PWD (Public Works Department): For major arterial roads, flyovers, and large storm water drains.
    - DJB (Delhi Jal Board): For sewage overflow, water pipeline bursts.
    - NDMC (New Delhi Municipal Council): For Lutyens Delhi and Central Delhi areas.
    - Cantonment Board: For military/cantonment areas.
    
    Provide ONLY the Name of the authority (one of: MCD, PWD, DJB, NDMC, Cantonment Board).`;

    try {
        let responseText = await generateContentSafe(prompt);
        responseText = responseText.trim();
        // Clean response if AI adds extra text
        const valid = ['MCD', 'PWD', 'DJB', 'NDMC', 'Cantonment Board'];
        const found = valid.find(v => responseText.toUpperCase().includes(v));
        res.json({ prediction: found || responseText });
    } catch (err) {
        console.error('AI Prediction Error:', err);
        res.status(500).json({ error: 'AI Prediction failed' });
    }
});

app.post('/api/ai/chat', async (req, res) => {
    const { message, history } = req.body;

    // Convert history format if necessary (Gemini expects role: 'user'/'model')
    // For simplicity, we restart context or keep it lightweight

    const systemPrompt = `You are the Delhi Waterlogging Monitoring & Response System Assistant. 
    Provide helpful, calm, and authoritative guidance to citizens.
    Capabilities:
    - Guide users through creating a report (provide info about title, severity, location).
    - Provide emergency contacts (Fire: 101, Police: 100/112, Ambulance: 102).
    - Give safety tips (Electrical safety, health, traffic).
    - Explain authority roles (MCD: Local drains, PWD: Major roads, DJB: Water supply/sewerage).
    Strict Guardrails:
    - Informational only.
    - No medical or legal diagnosis.
    - If someone is in immediate danger, tell them to call 112 or 101.
    Current context: Waterlogging in Delhi.`;

    try {
        const reply = await startChatSafe([], message, systemPrompt);
        res.json({ reply: reply });
    } catch (err) {
        console.error('AI Chat Error:', err);
        res.status(500).json({ error: 'Chat failed' });
    }
});

// --- RAINFALL WARNING SYSTEM (Simulated) ---

app.get('/api/rainfall-warnings', (req, res) => {
    // Hardcoded realistic data for demonstration
    const warnings = [
        { date: 'Tomorrow', risk: 'High', areas: ['North Delhi', 'Central Delhi', 'Minto Road'], advice: 'Avoid low-lying areas and underpasses.' },
        { date: 'Day after Tomorrow', risk: 'Medium', areas: ['South Delhi', 'Dwarka'], advice: 'Expect slow traffic.' }
    ];
    res.json(warnings);
});

// Export for Vercel
module.exports = app;

// Only listen if running locally
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Server running on http://localhost:${PORT}`);
    });
}
