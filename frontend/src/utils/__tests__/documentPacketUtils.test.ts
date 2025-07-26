import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { 
  fetchUserDocuments, 
  downloadDocumentBlobs, 
  hasRequiredDocuments, 
  getMissingDocuments,
  getDocumentTitle,
  convertImageToPdfPage,
  addPdfPages
} from '../documentPacketUtils';

// Mock Supabase client
const mockSupabase = {
  auth: {
    getSession: jest.fn(),
  },
  from: jest.fn(() => ({
    select: jest.fn(() => ({
      eq: jest.fn(() => ({
        execute: jest.fn(),
      })),
    })),
  })),
  storage: {
    from: jest.fn(() => ({
      download: jest.fn(),
    })),
  },
};

jest.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

// Mock pdf-lib
jest.mock('pdf-lib', () => ({
  PDFDocument: {
    load: jest.fn(() => ({
      getPages: jest.fn(() => [
        { copyTo: jest.fn() },
        { copyTo: jest.fn() },
      ]),
    })),
  },
}));

describe('Document Packet Utils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getDocumentTitle', () => {
    it('should return correct titles for document types', () => {
      expect(getDocumentTitle('photo_id')).toBe('Government-Issued Photo ID');
      expect(getDocumentTitle('ssn_card')).toBe('Social Security Card');
      expect(getDocumentTitle('utility_bill')).toBe('Utility Bill / Proof of Address');
      expect(getDocumentTitle('unknown_type')).toBe('Document');
    });
  });

  describe('hasRequiredDocuments', () => {
    it('should return true when all required documents are present', () => {
      const documents = [
        { document_type: 'photo_id', id: '1', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
        { document_type: 'ssn_card', id: '2', user_id: 'user1', file_name: 'ssn.jpg', file_path: '/path/2', created_at: '2023-01-01' },
        { document_type: 'utility_bill', id: '3', user_id: 'user1', file_name: 'bill.jpg', file_path: '/path/3', created_at: '2023-01-01' },
      ];

      expect(hasRequiredDocuments(documents)).toBe(true);
    });

    it('should return false when some required documents are missing', () => {
      const documents = [
        { document_type: 'photo_id', id: '1', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
        { document_type: 'ssn_card', id: '2', user_id: 'user1', file_name: 'ssn.jpg', file_path: '/path/2', created_at: '2023-01-01' },
      ];

      expect(hasRequiredDocuments(documents)).toBe(false);
    });

    it('should return false when no documents are provided', () => {
      expect(hasRequiredDocuments([])).toBe(false);
    });
  });

  describe('getMissingDocuments', () => {
    it('should return missing document types', () => {
      const documents = [
        { document_type: 'photo_id', id: '1', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
      ];

      const missing = getMissingDocuments(documents);
      expect(missing).toContain('Social Security Card');
      expect(missing).toContain('Utility Bill / Proof of Address');
      expect(missing).not.toContain('Government-Issued Photo ID');
    });

    it('should return all required documents when none are provided', () => {
      const missing = getMissingDocuments([]);
      expect(missing).toHaveLength(3);
      expect(missing).toContain('Government-Issued Photo ID');
      expect(missing).toContain('Social Security Card');
      expect(missing).toContain('Utility Bill / Proof of Address');
    });

    it('should return empty array when all documents are present', () => {
      const documents = [
        { document_type: 'photo_id', id: '1', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
        { document_type: 'ssn_card', id: '2', user_id: 'user1', file_name: 'ssn.jpg', file_path: '/path/2', created_at: '2023-01-01' },
        { document_type: 'utility_bill', id: '3', user_id: 'user1', file_name: 'bill.jpg', file_path: '/path/3', created_at: '2023-01-01' },
      ];

      const missing = getMissingDocuments(documents);
      expect(missing).toHaveLength(0);
    });
  });

  describe('fetchUserDocuments', () => {
    it('should fetch user documents successfully', async () => {
      const mockDocuments = [
        { id: '1', document_type: 'photo_id', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
        { id: '2', document_type: 'ssn_card', user_id: 'user1', file_name: 'ssn.jpg', file_path: '/path/2', created_at: '2023-01-01' },
      ];

      const mockSession = {
        session: { user: { id: 'user1' } },
      };

      mockSupabase.auth.getSession.mockResolvedValue({
        data: mockSession,
        error: null,
      });

      mockSupabase.from.mockReturnValue({
        select: jest.fn(() => ({
          eq: jest.fn(() => ({
            execute: jest.fn().mockResolvedValue({
              data: mockDocuments,
              error: null,
            }),
          })),
        })),
      });

      const result = await fetchUserDocuments('user1');
      
      expect(result).toEqual(mockDocuments);
      expect(mockSupabase.from).toHaveBeenCalledWith('user_documents');
    });

    it('should throw error when no active session', async () => {
      mockSupabase.auth.getSession.mockResolvedValue({
        data: { session: null },
        error: null,
      });

      await expect(fetchUserDocuments('user1')).rejects.toThrow('No active session');
    });

    it('should throw error when database query fails', async () => {
      const mockSession = {
        session: { user: { id: 'user1' } },
      };

      mockSupabase.auth.getSession.mockResolvedValue({
        data: mockSession,
        error: null,
      });

      mockSupabase.from.mockReturnValue({
        select: jest.fn(() => ({
          eq: jest.fn(() => ({
            execute: jest.fn().mockResolvedValue({
              data: null,
              error: { message: 'Database error' },
            }),
          })),
        })),
      });

      await expect(fetchUserDocuments('user1')).rejects.toThrow('Database error');
    });
  });

  describe('downloadDocumentBlobs', () => {
    it('should download document blobs successfully', async () => {
      const mockDocuments = [
        { id: '1', document_type: 'photo_id', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
      ];

      const mockBlob = new Blob(['image data'], { type: 'image/jpeg' });

      mockSupabase.storage.from.mockReturnValue({
        download: jest.fn().mockResolvedValue({
          data: mockBlob,
          error: null,
        }),
      });

      const mockUpdateProgress = jest.fn();
      const result = await downloadDocumentBlobs(mockDocuments, mockUpdateProgress);

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        document: mockDocuments[0],
        blob: mockBlob,
        type: 'image',
      });
      expect(mockUpdateProgress).toHaveBeenCalled();
    });

    it('should handle download errors gracefully', async () => {
      const mockDocuments = [
        { id: '1', document_type: 'photo_id', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
        { id: '2', document_type: 'ssn_card', user_id: 'user1', file_name: 'ssn.jpg', file_path: '/path/2', created_at: '2023-01-01' },
      ];

      const mockBlob = new Blob(['image data'], { type: 'image/jpeg' });

      mockSupabase.storage.from.mockReturnValue({
        download: jest.fn()
          .mockResolvedValueOnce({
            data: mockBlob,
            error: null,
          })
          .mockResolvedValueOnce({
            data: null,
            error: { message: 'Download failed' },
          }),
      });

      const mockUpdateProgress = jest.fn();
      const result = await downloadDocumentBlobs(mockDocuments, mockUpdateProgress);

      expect(result).toHaveLength(1); // Only successful download
      expect(result[0]).toEqual({
        document: mockDocuments[0],
        blob: mockBlob,
        type: 'image',
      });
    });

    it('should identify file types correctly', async () => {
      const mockDocuments = [
        { id: '1', document_type: 'photo_id', user_id: 'user1', file_name: 'id.jpg', file_path: '/path/1', created_at: '2023-01-01' },
        { id: '2', document_type: 'ssn_card', user_id: 'user1', file_name: 'ssn.pdf', file_path: '/path/2', created_at: '2023-01-01' },
      ];

      const mockImageBlob = new Blob(['image data'], { type: 'image/jpeg' });
      const mockPdfBlob = new Blob(['pdf data'], { type: 'application/pdf' });

      mockSupabase.storage.from.mockReturnValue({
        download: jest.fn()
          .mockResolvedValueOnce({
            data: mockImageBlob,
            error: null,
          })
          .mockResolvedValueOnce({
            data: mockPdfBlob,
            error: null,
          }),
      });

      const mockUpdateProgress = jest.fn();
      const result = await downloadDocumentBlobs(mockDocuments, mockUpdateProgress);

      expect(result).toHaveLength(2);
      expect(result[0].type).toBe('image');
      expect(result[1].type).toBe('pdf');
    });

    it('should handle empty document list', async () => {
      const mockUpdateProgress = jest.fn();
      const result = await downloadDocumentBlobs([], mockUpdateProgress);

      expect(result).toHaveLength(0);
      expect(mockUpdateProgress).not.toHaveBeenCalled();
    });
  });

  describe('convertImageToPdfPage', () => {
    it('should convert image to PDF page successfully', async () => {
      const mockBlob = new Blob(['image data'], { type: 'image/jpeg' });
      const mockPdfDoc = {
        addPage: jest.fn(() => ({
          getSize: jest.fn(() => ({ width: 612, height: 792 })),
          drawImage: jest.fn(),
        })),
        embedJpg: jest.fn(() => Promise.resolve({})),
        embedPng: jest.fn(() => Promise.resolve({})),
      };

      // Mock FileReader
      const mockFileReader = {
        readAsArrayBuffer: jest.fn(),
        result: new ArrayBuffer(8),
        onload: null,
        onerror: null,
      };

      // @ts-ignore
      global.FileReader = jest.fn(() => mockFileReader);

      // Simulate successful file read
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({} as any);
        }
      }, 0);

      await convertImageToPdfPage(mockBlob, mockPdfDoc as any, 'Test Image');

      expect(mockPdfDoc.addPage).toHaveBeenCalled();
      expect(mockFileReader.readAsArrayBuffer).toHaveBeenCalledWith(mockBlob);
    });

    it('should handle file read errors', async () => {
      const mockBlob = new Blob(['image data'], { type: 'image/jpeg' });
      const mockPdfDoc = {
        addPage: jest.fn(),
        embedJpg: jest.fn(),
        embedPng: jest.fn(),
      };

      // Mock FileReader with error
      const mockFileReader = {
        readAsArrayBuffer: jest.fn(),
        result: null,
        onload: null,
        onerror: null,
      };

      // @ts-ignore
      global.FileReader = jest.fn(() => mockFileReader);

      // Simulate file read error
      setTimeout(() => {
        if (mockFileReader.onerror) {
          mockFileReader.onerror({} as any);
        }
      }, 0);

      await expect(convertImageToPdfPage(mockBlob, mockPdfDoc as any, 'Test Image'))
        .rejects.toThrow('Failed to read image file');
    });
  });

  describe('addPdfPages', () => {
    it('should add PDF pages successfully', async () => {
      const mockBlob = new Blob(['pdf data'], { type: 'application/pdf' });
      const mockMainPdf = {
        copyPages: jest.fn(() => Promise.resolve([{}, {}])),
        addPage: jest.fn(),
      };

      const mockSourcePdf = {
        getPages: jest.fn(() => [{}, {}]),
      };

      const { PDFDocument } = require('pdf-lib');
      PDFDocument.load = jest.fn(() => Promise.resolve(mockSourcePdf));

      // Mock FileReader
      const mockFileReader = {
        readAsArrayBuffer: jest.fn(),
        result: new ArrayBuffer(8),
        onload: null,
        onerror: null,
      };

      // @ts-ignore
      global.FileReader = jest.fn(() => mockFileReader);

      // Simulate successful file read
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({} as any);
        }
      }, 0);

      await addPdfPages(mockBlob, mockMainPdf as any, 'Test PDF');

      expect(PDFDocument.load).toHaveBeenCalled();
      expect(mockMainPdf.copyPages).toHaveBeenCalledWith(mockSourcePdf, [0, 1]);
    });

    it('should handle PDF loading errors', async () => {
      const mockBlob = new Blob(['invalid pdf data'], { type: 'application/pdf' });
      const mockMainPdf = {
        copyPages: jest.fn(),
        addPage: jest.fn(),
      };

      const { PDFDocument } = require('pdf-lib');
      PDFDocument.load = jest.fn(() => Promise.reject(new Error('Invalid PDF')));

      // Mock FileReader
      const mockFileReader = {
        readAsArrayBuffer: jest.fn(),
        result: new ArrayBuffer(8),
        onload: null,
        onerror: null,
      };

      // @ts-ignore
      global.FileReader = jest.fn(() => mockFileReader);

      // Simulate successful file read
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({} as any);
        }
      }, 0);

      await expect(addPdfPages(mockBlob, mockMainPdf as any, 'Test PDF'))
        .rejects.toThrow('Invalid PDF');
    });
  });
});