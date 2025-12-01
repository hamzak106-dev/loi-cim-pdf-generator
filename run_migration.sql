-- ============================================
-- Migration Script: Add CIM_TRAINING and Reviewed Features
-- Run this script directly on your PostgreSQL database
-- ============================================

-- Step 1: Add CIM_TRAINING to the formtype enum
DO $$
DECLARE
    enum_type_name text;
BEGIN
    -- Find the enum type name (could be 'formtype' or 'form_type')
    SELECT typname INTO enum_type_name
    FROM pg_type 
    WHERE typtype = 'e' 
    AND (typname = 'formtype' OR typname = 'form_type')
    LIMIT 1;
    
    -- Add CIM_TRAINING if enum type exists and value doesn't exist
    IF enum_type_name IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'CIM_TRAINING' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = enum_type_name)
        ) THEN
            EXECUTE format('ALTER TYPE %I ADD VALUE ''CIM_TRAINING''', enum_type_name);
            RAISE NOTICE 'Added CIM_TRAINING to enum type: %', enum_type_name;
        ELSE
            RAISE NOTICE 'CIM_TRAINING already exists in enum type: %', enum_type_name;
        END IF;
    ELSE
        RAISE NOTICE 'Enum type not found. Skipping enum update.';
    END IF;
END $$;

-- Step 2: Add new columns to forms table
DO $$
BEGIN
    -- Add scheduled_at column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'forms' 
        AND column_name = 'scheduled_at'
    ) THEN
        ALTER TABLE forms ADD COLUMN scheduled_at VARCHAR(100);
        RAISE NOTICE 'Added column: scheduled_at';
    ELSE
        RAISE NOTICE 'Column scheduled_at already exists';
    END IF;
    
    -- Add time column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'forms' 
        AND column_name = 'time'
    ) THEN
        ALTER TABLE forms ADD COLUMN time VARCHAR(50);
        RAISE NOTICE 'Added column: time';
    ELSE
        RAISE NOTICE 'Column time already exists';
    END IF;
    
    -- Add meeting_host column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'forms' 
        AND column_name = 'meeting_host'
    ) THEN
        ALTER TABLE forms ADD COLUMN meeting_host VARCHAR(100);
        RAISE NOTICE 'Added column: meeting_host';
    ELSE
        RAISE NOTICE 'Column meeting_host already exists';
    END IF;
    
    -- Add scheduled_count column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'forms' 
        AND column_name = 'scheduled_count'
    ) THEN
        ALTER TABLE forms ADD COLUMN scheduled_count INTEGER DEFAULT 0;
        RAISE NOTICE 'Added column: scheduled_count';
    ELSE
        RAISE NOTICE 'Column scheduled_count already exists';
    END IF;
END $$;

-- Step 3: Create form_reviewed table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'form_reviewed'
    ) THEN
        CREATE TABLE form_reviewed (
            id SERIAL PRIMARY KEY,
            form_id INTEGER NOT NULL UNIQUE,
            reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            reviewed_by VARCHAR(100),
            CONSTRAINT fk_form_reviewed_form_id FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
        );
        
        CREATE INDEX ix_form_reviewed_form_id ON form_reviewed(form_id);
        
        RAISE NOTICE 'Created table: form_reviewed';
    ELSE
        RAISE NOTICE 'Table form_reviewed already exists';
    END IF;
END $$;

-- Step 4: Add comments to columns
COMMENT ON COLUMN forms.scheduled_at IS 'Scheduled date';
COMMENT ON COLUMN forms.time IS 'Scheduled time';
COMMENT ON COLUMN forms.meeting_host IS 'Meeting host name';
COMMENT ON COLUMN forms.scheduled_count IS 'Number of times scheduled';

-- Verification queries (optional - uncomment to run)
-- SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'formtype');
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'forms' AND column_name IN ('scheduled_at', 'time', 'meeting_host', 'scheduled_count');
-- SELECT * FROM form_reviewed LIMIT 1;

RAISE NOTICE 'Migration completed successfully!';

