import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  'https://rpgaxevgnzyasysyvnqz.supabase.co',
  'sb_publishable_ex7srIMDzX41rLw1_F_HDQ_T6kBoNwC',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  },
)
