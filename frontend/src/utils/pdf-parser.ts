import * as fs from "fs";
import OpenAI from "openai";

export async function parsePdfDocument(filePath: string, apiKey: string) {
    console.log("PDF-PARSER: parsePdfDocument - filePath:", filePath);
    console.log("PDF-PARSER: parsePdfDocument - apiKey:", apiKey);
    const mimeType = "application/pdf";

    const openai = new OpenAI({
        apiKey: apiKey,
        baseURL: "https://api.upstage.ai/v1/information-extraction"
    });

    const base64Encoded = fs.readFileSync(filePath, "base64");

    const extraction_response = await openai.chat.completions.create({
        model: "information-extract",
        messages: [{
            role: "user",
            content: [
                {
                    type: "image_url",
                    image_url: {
                        url: `data:${mimeType};base64,${base64Encoded}`,
                    },
                },
            ],
        }],
        response_format: {
            "type": "json_schema",
            "json_schema": {
                "name": "document_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "account_name": {
                            "type": "string",
                            "description": "Name of Company"
                        },
                        "account_number": {
                            "type": "string",
                            "description": "Account Number"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of Account"
                        },
                        "balance": {
                            "type": "number",
                            "description": "Balance Owed"
                        },
                        "status": {
                            "type": "string",
                            "description": "Status Details"
                        },
                        "credit_limit": {
                            "type": "number",
                            "description": "Credit Limit/Original Amount"
                        },
                        "address": {
                            "type": "string",
                            "description": "Address of Company"
                        }
                    }
                }
            }
        }
    });

    console.log("parsePdfDocument - extraction_response:", extraction_response);
    return JSON.parse(extraction_response.choices[0].message.content || '{}');
}