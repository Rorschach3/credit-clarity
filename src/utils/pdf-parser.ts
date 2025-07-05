import OpenAI from "openai";

export async function pdfParse(fileData: ArrayBuffer, apiKey: string) {
    const mimeType = "application/pdf";
    
    const openai = new OpenAI({
        apiKey: apiKey,
        baseURL: "https://api.upstage.ai/v1/information-extraction"
    });

    // Convert ArrayBuffer to base64
    const base64Encoded = btoa(
      new Uint8Array(fileData).reduce((data, byte) => data + String.fromCharCode(byte), '')
    );

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
                        "account_type": {
                            "type": "string",
                            "description": "Type of Account"
                        },
                        "account_balance": {
                            "type": "number",
                            "description": "Balance Owed"
                        },
                        "credit_bureau": {
                            "type": "string",
                            "description": "Credit Bureau Name"
                        },
                        "account_status": {
                            "type": "string",
                            "description": "Status Details"
                        },
                        "credit_limit": {
                            "type": "number",
                            "description": "Credit Limit/Original Amount"
                        },
                        "is_negative": {
                            "type": "boolean",
                            "description": "Indicates if the account is negative"
                        },
                        "date_opened": {
                            "type": "string",
                            "format": "date",
                            "description": "Date the account was opened"
                        },
                        "monthly_payment": {
                            "type": "number",
                            "description": "Monthly Payment Amount"
                        },
                        "dispute_count": {
                            "type": "integer",
                            "description": "Number of Disputes"
                        }
                    }
                }
            }
        }
    });

    return JSON.parse(extraction_response.choices[0].message.content || '{}');
}