import { createClient } from '@supabase/supabase-js';
import { createPagesServerClient } from '@supabase/auth-helpers-nextjs';
import { NextApiRequest, NextApiResponse } from 'next';
import { v4 as uuidv4 } from 'uuid';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl!, supabaseKey!);

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
  },
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'POST') {
    try {
      const { file } = req.body;

      if (!file) {
        return res.status(400).json({ message: 'No file uploaded' });
      }

      const fileBuffer = Buffer.from(file.split(',')[1], 'base64');
      const fileSizeInBytes = fileBuffer.byteLength;
      const filename = `credit-report-${uuidv4()}.pdf`;
      const uploadDate = new Date();

      const supabase = createPagesServerClient({ req, res });
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();

      if (sessionError) {
        console.error('Supabase Session Error:', sessionError);
        return res.status(500).json({ message: 'Failed to get user session' });
      }

      const userId = session?.user?.id;

      if (!userId) {
        return res.status(401).json({ message: 'Unauthorized: User not logged in' });
      }

      const maxFileSizeInBytes = 10 * 1024 * 1024; // 10MB

      if (fileSizeInBytes > maxFileSizeInBytes) {
        return res.status(400).json({ message: 'File size exceeds 10MB' });
      }

      // Upload file to Supabase Storage
      const { data, error: uploadError } = await supabase.storage
        .from('credit-reports')
        .upload(`${userId}/${filename}`, fileBuffer, {
          contentType: 'application/pdf',
        });

      if (uploadError) {
        console.error('Supabase Storage Error:', uploadError);
        return res.status(500).json({ message: 'Failed to upload file to storage' });
      }

      const storagePath = data.path;

      // Save file metadata to Supabase database
      // 1. Insert into encrypted_report_content
      const { data: encryptionResult, error: contentError } = await supabase
        .from('encrypted_report_content')
        .insert([
          {
            encrypted_data: fileBuffer,
          },
        ])
        .select('content_id')
        .single()

      if (contentError) {
        console.error('Supabase Database Error (encrypted_report_content):', contentError);
        return res.status(500).json({ message: 'Failed to save encrypted file content to database' });
      }

      // 2. Insert into credit_reports
      const { error: reportError } = await supabase
        .from('credit_reports')
        .insert([
          {
+92 |             // Log userId and storage_path for debugging
+93 |             user_id: userId,
+94 |             content_id: encryptionResult?.content_id,
+95 |             storage_path: `${userId}/${filename}`, // Ensure storage path is correctly formatted
+96 |           },
+97 |         ]);
+98 |       console.log("Inserting credit report with user_id:", userId, "and storage_path:", `${userId}/${filename}`);

      if (reportError) {
        console.error('Supabase Database Error (credit_reports):', reportError);
        return res.status(500).json({ message: 'Failed to save file metadata to database' });
      }

      return res.status(200).json({ message: 'File uploaded successfully' });
    } catch (error: unknown) {
      console.error('Upload Error:', error);
      return res.status(500).json({ message: error instanceof Error ? error.message : 'Failed to upload file' });
    }
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).json({ message: `Method ${req.method} Not Allowed` });
  }
}