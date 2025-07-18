-- Create dispute_packets storage bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('dispute_packets', 'dispute_packets', false)
ON CONFLICT (id) DO NOTHING;

-- Create storage policies for dispute_packets bucket
CREATE POLICY "Users can upload their own dispute packets" 
  ON storage.objects 
  FOR INSERT 
  TO authenticated 
  WITH CHECK (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own dispute packets" 
  ON storage.objects 
  FOR SELECT 
  TO authenticated 
  USING (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update their own dispute packets" 
  ON storage.objects 
  FOR UPDATE 
  TO authenticated 
  USING (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1])
  WITH CHECK (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own dispute packets" 
  ON storage.objects 
  FOR DELETE 
  TO authenticated 
  USING (bucket_id = 'dispute_packets' AND auth.uid()::text = (storage.foldername(name))[1]);