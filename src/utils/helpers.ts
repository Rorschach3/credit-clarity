
export const fileToBase64 = async (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = error => reject(error);
  });
};

// Define a basic AI response type for helpers
interface AIAnalysisResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export const sanitizeAIResponse = (response: AIAnalysisResponse): AIAnalysisResponse => {
  // Implement sanitization logic based on AI requirements
  // Example: Remove unwanted properties or format the data
  return response;
};
