{
"taskId": "auto-generated-by-firebase",
"title": "string (required)",
"creatorId": "string (required)",
"deadline": 1735689600, // epoch timestamp (required)
"status": "ongoing", // enum: ongoing, unassigned, under_review, completed
"notes": "string (optional)",
"attachments": ["base64string1", "base64string2"], // array of base64 strings
"collaborators": ["userId1", "userId2"], // array of user IDs
"projectId": "string (optional)",
"ownerId": "string (defaults to creatorId)",
"createdAt": 1727092800, // epoch timestamp
"updatedAt": 1727109800 // epoch timestamp
}
