-- Create the missing upsert_tradeline RPC function
-- This function will insert or update tradelines based on the unique constraint
CREATE OR REPLACE FUNCTION public.upsert_tradeline(
    p_user_id UUID,
    p_creditor_name TEXT,
    p_account_number TEXT,
    p_account_balance TEXT,
    p_credit_limit TEXT,
    p_monthly_payment TEXT,
    p_account_type TEXT,
    p_account_status TEXT,
    p_credit_bureau TEXT,
    p_date_opened TEXT DEFAULT NULL,
    p_is_negative BOOLEAN DEFAULT FALSE
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    tradeline_id UUID;
    existing_id UUID;
BEGIN
    -- Check if tradeline already exists based on unique constraint
    SELECT id INTO existing_id
    FROM public.tradelines
    WHERE user_id = p_user_id
      AND account_number = p_account_number
      AND creditor_name = p_creditor_name
      AND credit_bureau = p_credit_bureau;

    IF existing_id IS NOT NULL THEN
        -- Update existing tradeline
        UPDATE public.tradelines
        SET 
            account_balance = COALESCE(NULLIF(p_account_balance, ''), account_balance),
            credit_limit = COALESCE(NULLIF(p_credit_limit, ''), credit_limit),
            monthly_payment = COALESCE(NULLIF(p_monthly_payment, ''), monthly_payment),
            account_type = COALESCE(NULLIF(p_account_type, ''), account_type),
            account_status = COALESCE(NULLIF(p_account_status, ''), account_status),
            date_opened = COALESCE(NULLIF(p_date_opened, ''), date_opened),
            is_negative = p_is_negative,
            created_at = NOW()
        WHERE id = existing_id;
        
        tradeline_id := existing_id;
        
        RAISE NOTICE 'Updated existing tradeline with ID: %', tradeline_id;
    ELSE
        -- Insert new tradeline
        INSERT INTO public.tradelines (
            user_id,
            creditor_name,
            account_number,
            account_balance,
            credit_limit,
            monthly_payment,
            account_type,
            account_status,
            credit_bureau,
            date_opened,
            is_negative,
            raw_text,
            dispute_count,
            created_at
        ) VALUES (
            p_user_id,
            COALESCE(p_creditor_name, ''),
            COALESCE(p_account_number, ''),
            COALESCE(p_account_balance, '$0'),
            COALESCE(p_credit_limit, '$0'),
            COALESCE(p_monthly_payment, '$0'),
            COALESCE(p_account_type, ''),
            COALESCE(p_account_status, ''),
            COALESCE(p_credit_bureau, ''),
            COALESCE(p_date_opened, 'xx/xx/xxxx'),
            COALESCE(p_is_negative, FALSE),
            '', -- raw_text default
            0,  -- dispute_count default
            NOW()
        )
        RETURNING id INTO tradeline_id;
        
        RAISE NOTICE 'Inserted new tradeline with ID: %', tradeline_id;
    END IF;

    RETURN tradeline_id;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.upsert_tradeline TO authenticated;

-- Add helpful comment
COMMENT ON FUNCTION public.upsert_tradeline IS 'Upserts a tradeline record. Updates existing record if found based on unique constraint (user_id, account_number, creditor_name, credit_bureau), otherwise inserts new record. Only updates non-empty fields to preserve existing data.';