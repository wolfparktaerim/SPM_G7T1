{
"subTaskId": "auto-generated-by-firebase",
"title": "string (required)",
"creatorId": "string (required)",
"deadline": 1735689600, // epoch timestamp (required)
"status": "ongoing", // enum: ongoing, unassigned, under_review, completed
"notes": "string (optional)",
"attachments": ["base64string1"], // array of base64 strings
"collaborators": ["userId1"], // array of user IDs
"taskId": "string (required)", // parent task reference
"ownerId": "string (defaults to creatorId)",
"createdAt": 1727092800, // epoch timestamp
"updatedAt": 1727109800 // epoch timestamp
}
