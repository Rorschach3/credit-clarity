import { parsePdfDocument } from "./pdf-parser";
import * as fs from "fs";
import OpenAI from "openai";

jest.mock("fs");
jest.mock("openai");

describe("parsePdfDocument", () => {
  it("should parse a PDF document and return account information", async () => {
    // Mock file system and OpenAI API
    const mockApiKey = "test-api-key";
    const mockFilePath = "test.pdf";
    const mockBase64Encoded = "base64-encoded-pdf-content";
    const mockExtractionResponse = {
      choices: [
        {
          message: {
            content: JSON.stringify({
              account_name: "Test Company",
              account_number: "1234567890",
              type: "Credit Card",
              balance: 1000,
              status: "Active",
              credit_limit: 5000,
              address: "123 Test St",
            }),
          },
        },
      ],
    };

    (fs.readFileSync as jest.Mock).mockReturnValue(mockBase64Encoded);
    (OpenAI.prototype.chat.completions.create as jest.Mock).mockResolvedValue(
      mockExtractionResponse
    );

    // Call the function
    const result = await parsePdfDocument(mockFilePath, mockApiKey);

    // Assertions
    expect(fs.readFileSync).toHaveBeenCalledWith(mockFilePath, "base64");
    expect(OpenAI.prototype.chat.completions.create).toHaveBeenCalled();
    expect(result).toEqual({
      account_name: "Test Company",
      account_number: "1234567890",
      type: "Credit Card",
      balance: 1000,
      status: "Active",
      credit_limit: 5000,
      address: "123 Test St",
    });
  });
});