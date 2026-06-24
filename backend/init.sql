-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Insert admin user if not exists
INSERT INTO users (email, full_name, hashed_password, role, enabled)
VALUES (
    'admin@example.com',
    'System Admin',
    '$2b$12$8rnysAFNlr/uk8eug52TEO9ySaalBMvM9U8W07ocLZXoS1gwC1.ra',
    'ADMIN',
    true
)
ON CONFLICT (email) DO NOTHING;