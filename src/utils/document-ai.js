import express from 'express';
import { GoogleAuth } from 'google-auth-library';
import fs from 'fs';

const app = express();
app.use(express.json({ limit: '50mb' }));

const PORT = 8001;  // Use port 8001 to match your FastAPI configuration

// Load your service account
const auth = new GoogleAuth({
  keyFile: './service-account.json',
  scopes: ['https://www.googleapis.com/auth/cloud-platform'],
});

const PROCESSOR_URL =
  'https://us-documentai.googleapis.com/v1/projects/1045000590097/locations/us/processors/38ae0476f612fc35/processorVersions/pretrained-form-parser-v2.1-2023-06-26:process';

app.post('/document-ai', async (req, res) => {
  try {
    const { base64 } = req.body;
    if (!base64) {
      return res.status(400).json({ error: 'Missing base64 document' });
    }

    console.log(`📄 Processing document with ${base64.length} characters of base64 data`);

    const client = await auth.getClient();
    const accessToken = await client.getAccessToken();

    console.log('🔑 Got access token, calling Google Document AI...');

    const response = await fetch(PROCESSOR_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        inlineDocument: {
          mimeType: 'application/pdf',
          content: base64,
        },
      }),
    });

    const result = await response.json();
    
    // Log the extracted text length for debugging
    if (result.document && result.document.text) {
      console.log(`✅ Document AI extracted ${result.document.text.length} characters`);
      console.log(`📝 First 200 chars: ${result.document.text.substring(0, 200)}`);
    } else {
      console.log('⚠️ No text found in Document AI response');
      console.log('Response structure:', JSON.stringify(result, null, 2));
    }

    res.status(response.status).json(result);
  } catch (err) {
    console.error('❌ Document AI proxy error:', err);
    res.status(500).json({ error: 'Failed to process document', details: err.message });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'document-ai-proxy', port: PORT });
});

app.listen(PORT, () => {
  console.log(`🚀 Document AI Proxy Server running on http://localhost:${PORT}`);
  console.log(`📋 Health check available at http://localhost:${PORT}/health`);
});
