-- 1. Team Members
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discord_user_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    display_name TEXT,
    role TEXT NOT NULL DEFAULT 'intern',
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Modules
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    client_name TEXT,
    deadline TIMESTAMPTZ,
    status TEXT DEFAULT 'active',
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    module_id UUID REFERENCES modules(id) ON DELETE SET NULL,
    assignee_id TEXT,
    creator_id TEXT NOT NULL,
    status TEXT DEFAULT 'todo',
    priority TEXT DEFAULT 'medium',
    estimated_hours FLOAT,
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    slipped BOOLEAN DEFAULT FALSE,
    slip_count INTEGER DEFAULT 0
);

CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_module ON tasks(module_id);

-- 4. Task Updates
CREATE TABLE IF NOT EXISTS task_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    update_text TEXT NOT NULL,
    update_type TEXT DEFAULT 'progress',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Standups
CREATE TABLE IF NOT EXISTS standups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    yesterday TEXT,
    today TEXT,
    blockers TEXT,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

CREATE INDEX idx_standups_date ON standups(date);

-- 6. Blockers
CREATE TABLE IF NOT EXISTS blockers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id TEXT NOT NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    blocking_person_id TEXT,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    resolution_note TEXT,
    hours_open FLOAT
);

-- 7. Slip Reasons
CREATE TABLE IF NOT EXISTS slip_reasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    original_due_date TIMESTAMPTZ,
    new_due_date TIMESTAMPTZ,
    reason_category TEXT,
    reason_text TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Context Log (Jarvis's Memory)
CREATE TABLE IF NOT EXISTS context_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    user_id TEXT,
    task_id UUID,
    module_id UUID,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_context_log_created ON context_log(created_at DESC);
CREATE INDEX idx_context_log_user ON context_log(user_id, created_at DESC);
CREATE INDEX idx_context_log_type ON context_log(event_type, created_at DESC);

-- 9. Jarvis Snapshots
CREATE TABLE IF NOT EXISTS jarvis_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_type TEXT NOT NULL,
    reference_id TEXT,
    week_start DATE,
    content TEXT NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Demo Features
CREATE TABLE IF NOT EXISTS demo_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    module_id UUID REFERENCES modules(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'not_ready',
    status_note TEXT,
    last_updated_by TEXT,
    last_updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Manual Context
CREATE TABLE IF NOT EXISTS manual_context (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    added_by TEXT NOT NULL,
    context_type TEXT,
    content TEXT NOT NULL
);

-- Phase 5
CREATE TABLE IF NOT EXISTS jarvis_snapshots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    summary TEXT NOT NULL
);
