const { Pool } = require('pg');

const connectionString = 'postgresql://postgres.amkocqxmizilimqjegdp:eVVlVePWcPHZVDtq@aws-1-ap-south-1.pooler.supabase.com:6543/postgres';

const pool = new Pool({
    connectionString: connectionString,
});

module.exports = {
    query: (text, params) => pool.query(text, params),
};
