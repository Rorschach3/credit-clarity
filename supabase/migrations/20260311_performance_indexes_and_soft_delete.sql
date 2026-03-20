-- Phase 1: Database performance + soft delete primitives
-- Guarded with to_regclass() because some environments may have these tables
-- created outside of migrations.

-- Add soft-delete and updated_at columns
DO $$
BEGIN
  IF to_regclass('public.tradelines') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE public.tradelines ADD COLUMN IF NOT EXISTS deleted_at timestamptz';
    EXECUTE 'ALTER TABLE public.tradelines ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()';
  END IF;

  IF to_regclass('public.disputes') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE public.disputes ADD COLUMN IF NOT EXISTS deleted_at timestamptz';
  END IF;
END $$;

-- Composite indexes for common queries (partial: ignore soft-deleted rows)
DO $$
BEGIN
  IF to_regclass('public.tradelines') IS NOT NULL THEN
    EXECUTE '
      CREATE INDEX IF NOT EXISTS idx_tradelines_user_bureau_created_at
      ON public.tradelines (user_id, credit_bureau, created_at DESC)
      WHERE deleted_at IS NULL
    ';
  END IF;

  IF to_regclass('public.disputes') IS NOT NULL THEN
    EXECUTE '
      CREATE INDEX IF NOT EXISTS idx_disputes_user_status_created_at
      ON public.disputes (user_id, status, created_at DESC)
      WHERE deleted_at IS NULL
    ';
  END IF;
END $$;

-- Standard updated_at trigger function (idempotent)
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to tradelines (only if the table exists)
DO $$
BEGIN
  IF to_regclass('public.tradelines') IS NOT NULL THEN
    EXECUTE 'DROP TRIGGER IF EXISTS update_tradelines_updated_at ON public.tradelines';
    EXECUTE '
      CREATE TRIGGER update_tradelines_updated_at
      BEFORE UPDATE ON public.tradelines
      FOR EACH ROW
      EXECUTE FUNCTION public.update_updated_at_column()
    ';
  END IF;
END $$;

