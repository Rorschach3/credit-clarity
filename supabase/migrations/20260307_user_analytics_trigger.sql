-- Migration: Create user_analytics table and increment triggers

CREATE TABLE IF NOT EXISTS public.user_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
    total_scans INTEGER DEFAULT 0,
    total_letters INTEGER DEFAULT 0,
    total_mailings INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.user_analytics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own analytics"
    ON public.user_analytics
    FOR SELECT
    USING (auth.uid() = user_id);

-- Trigger function: upsert user_analytics row and increment total_scans on tradeline insert
CREATE OR REPLACE FUNCTION public.increment_user_scans()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_analytics (user_id, total_scans, updated_at)
    VALUES (NEW.user_id, 1, now())
    ON CONFLICT (user_id) DO UPDATE
        SET total_scans = public.user_analytics.total_scans + 1,
            updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_increment_scans ON public.tradelines;
CREATE TRIGGER trg_increment_scans
    AFTER INSERT ON public.tradelines
    FOR EACH ROW EXECUTE FUNCTION public.increment_user_scans();

-- Trigger function: upsert user_analytics row and increment total_letters when dispute status is letter_generated
CREATE OR REPLACE FUNCTION public.increment_user_letters()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'letter_generated' AND (OLD.status IS NULL OR OLD.status <> 'letter_generated') THEN
        INSERT INTO public.user_analytics (user_id, total_letters, updated_at)
        VALUES (NEW.user_id, 1, now())
        ON CONFLICT (user_id) DO UPDATE
            SET total_letters = public.user_analytics.total_letters + 1,
                updated_at = now();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_increment_letters ON public.disputes;
CREATE TRIGGER trg_increment_letters
    AFTER INSERT OR UPDATE ON public.disputes
    FOR EACH ROW EXECUTE FUNCTION public.increment_user_letters();
