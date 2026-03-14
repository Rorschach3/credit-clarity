-- Migration: Create notification_log table

CREATE TABLE IF NOT EXISTS public.notification_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    notification_type TEXT CHECK (notification_type IN (
        'croa_disclosure',
        'letter_sent',
        'mailing_dispatched',
        'fcra_day1',
        'fcra_day3',
        'fcra_day25',
        'dispute_update'
    )),
    sent_at TIMESTAMPTZ DEFAULT now(),
    metadata JSONB
);

ALTER TABLE public.notification_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notification logs"
    ON public.notification_log
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own notification logs"
    ON public.notification_log
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);
