<<<<<<< Updated upstream:src/lib/encryption.ts
import { createClient } from '@supabase/supabase-js';

if (!import.meta.env.VITE_SUPABASE_URL || !import.meta.env.VITE_SUPABASE_ANON_KEY) {
  throw new Error('Missing Supabase environment variables - check .env file');
}

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

const CRYPTO_KEY_VAULT = 'credit_report_keys';

export async function generateCryptoKey() {
  return await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
}

export async function exportCryptoKey(key: CryptoKey) {
  return await crypto.subtle.exportKey('jwk', key);
}

export async function importCryptoKey(jwk: JsonWebKey) {
  return await crypto.subtle.importKey(
    'jwk',
    jwk,
    { name: 'AES-GCM' },
    true,
    ['encrypt', 'decrypt']
  );
}

export async function encryptData(key: CryptoKey, data: ArrayBuffer) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    data
  );
  // Prepend IV to encrypted data for storage
  const combined = new Uint8Array(iv.byteLength + encrypted.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(encrypted), iv.byteLength);
  return combined.buffer;
}

export async function decryptData(key: CryptoKey, data: ArrayBuffer) {
  const iv = data.slice(0, 12);
  const encrypted = data.slice(12);
  return await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: new Uint8Array(iv) },
    key,
    encrypted
  );
}

// Placeholder for storing key in Supabase Vault (to be implemented server-side)
export async function storeKeyInVault(keyId: string, jwk: JsonWebKey) {
  // Implement RPC or API call to store key securely
  // Example:
  // await supabase.rpc('store_key', { key_id: keyId, key_data: jwk });
=======
// Encryption utilities for credit report data

export async function generateCryptoKey() {
  return await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
}

export async function exportCryptoKey(key: CryptoKey) {
  return await crypto.subtle.exportKey('jwk', key);
}

export async function importCryptoKey(jwk: JsonWebKey) {
  return await crypto.subtle.importKey(
    'jwk',
    jwk,
    { name: 'AES-GCM' },
    true,
    ['encrypt', 'decrypt']
  );
}

export async function encryptData(key: CryptoKey, data: ArrayBuffer) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    data
  );
  // Prepend IV to encrypted data for storage
  const combined = new Uint8Array(iv.byteLength + encrypted.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(encrypted), iv.byteLength);
  return combined.buffer;
}

export async function decryptData(key: CryptoKey, data: ArrayBuffer) {
  const iv = data.slice(0, 12);
  const encrypted = data.slice(12);
  return await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: new Uint8Array(iv) },
    key,
    encrypted
  );
}

// Placeholder for storing key in Supabase Vault (to be implemented server-side)
export async function storeKeyInVault(_keyId: string, _jwk: JsonWebKey) {
  // Implement RPC or API call to store key securely
  // Example:
  // await supabase.rpc('store_key', { key_id: keyId, key_data: jwk });
  console.log('Key vault storage not yet implemented');
>>>>>>> Stashed changes:frontend/src/lib/encryption.ts
}