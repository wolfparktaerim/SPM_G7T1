# Firebase Password Reset Email Template Configuration

This guide explains how to configure the Firebase password reset email template to meet the requirements of the password reset user story.

## Overview

Firebase Authentication provides built-in email templates for password reset that can be customized through the Firebase Console. The default settings already provide:

- ✅ Time-limited reset links (default: 1 hour / 60 minutes)
- ✅ One-time use links (automatically invalidated after use)
- ✅ Secure token generation
- ✅ Professional email formatting

## Configuration Steps

### Step 1: Access Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (SPM_G7T1)
3. Navigate to **Authentication** in the left sidebar
4. Click on the **Templates** tab at the top

### Step 2: Configure Password Reset Template

1. Select **Password reset** from the template list
2. You'll see options to customize:
   - **From name**: The sender name (e.g., "Smart Task Management System")
   - **Reply-to email**: Where replies should go
   - **Subject line**: Email subject
   - **Email body**: HTML template for the email

### Step 3: Customize Email Template

Here's a recommended template that meets all security requirements:

#### Subject Line:
```
Reset your password for Smart Task Management System
```

#### Email Body (HTML):

```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
    <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset Request</h1>
  </div>

  <div style="background-color: #ffffff; padding: 40px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
    <p style="color: #374151; font-size: 16px; line-height: 1.6;">Hello,</p>

    <p style="color: #374151; font-size: 16px; line-height: 1.6;">
      We received a request to reset your password for your Smart Task Management System account.
      If you made this request, click the button below to reset your password:
    </p>

    <div style="text-align: center; margin: 30px 0;">
      <a href="%LINK%" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px;">
        Reset Password
      </a>
    </div>

    <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
      <p style="color: #92400e; margin: 0; font-size: 14px; font-weight: 600;">⚠️ Important Security Information:</p>
      <ul style="color: #92400e; margin: 10px 0 0 20px; font-size: 14px; line-height: 1.6;">
        <li>This link will expire in <strong>60 minutes</strong></li>
        <li>The link can only be used <strong>one time</strong></li>
        <li>If you request a new reset link, this one will be invalidated</li>
      </ul>
    </div>

    <p style="color: #374151; font-size: 14px; line-height: 1.6;">
      If the button doesn't work, copy and paste this link into your browser:
    </p>
    <p style="color: #2563eb; font-size: 12px; word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px;">
      %LINK%
    </p>

    <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 4px;">
      <p style="color: #991b1b; margin: 0; font-size: 14px; font-weight: 600;">🔒 Didn't request this?</p>
      <p style="color: #991b1b; margin: 10px 0 0 0; font-size: 14px; line-height: 1.6;">
        If you didn't request a password reset, you can safely ignore this email.
        Your password will not be changed, and no action is required.
      </p>
    </div>

    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

    <p style="color: #6b7280; font-size: 12px; line-height: 1.6;">
      This is an automated message from Smart Task Management System. Please do not reply to this email.
    </p>

    <p style="color: #6b7280; font-size: 12px; line-height: 1.6;">
      For support, contact us at <a href="mailto:support@g7t1.com" style="color: #2563eb;">support@g7t1.com</a>
    </p>
  </div>
</div>
```

### Step 4: Configure Action Code Settings

The action code settings control the expiration time of the reset link:

1. In Firebase Console, go to **Authentication** > **Settings**
2. Scroll down to **User account actions**
3. The default expiration time is **1 hour (3600 seconds)** - This meets the 60-minute requirement ✅
4. If you need to verify or change it:
   - Click on **Edit** next to "Action links"
   - Set the expiration time to **3600 seconds** (60 minutes)
   - Save the changes

**Note**: Firebase automatically handles:
- ✅ One-time use (links are invalidated after password change)
- ✅ Secure token generation
- ✅ HTTPS enforcement
- ✅ Link validation

### Step 5: Test the Email Template

1. Use the **Send test email** button in the Firebase Console
2. Enter a test email address
3. Verify the email:
   - Arrives within 1-2 minutes
   - Has correct branding
   - Link works correctly
   - Link expires after 60 minutes
   - Link is invalidated after one use

## Password Policy Enforcement

The application enforces the following password policy when users reset their password:

### Requirements:
- ✅ Minimum 8 characters
- ✅ At least one uppercase letter (A-Z)
- ✅ At least one lowercase letter (a-z)
- ✅ At least one number (0-9)
- ✅ At least one special character (!@#$%^&*(),.?":{}|<>)

### Implementation:
- Frontend validation in `frontend/src/utils/passwordPolicy.js`
- Real-time password strength indicator during signup
- Firebase weak password detection as fallback

## Security Features Implemented

### 1. **Rate Limiting** ✅
- Users can only request a password reset once every 5 minutes
- Prevents abuse and email flooding
- Implemented in: `frontend/src/stores/auth.js`

### 2. **User Enumeration Prevention** ✅
- Same success message shown for all email addresses (existing or not)
- Generic error messages that don't reveal account existence
- Message: "If an account exists with this email, a password reset link has been sent."

### 3. **Token Tracking** ✅
- All reset requests are logged in Firebase Realtime Database
- New reset requests invalidate previous unexpired requests
- Stored in: `/passwordResetRequests/{base64Email}`

### 4. **Automatic Cleanup** ✅
- Expired reset requests are automatically cleaned up every hour
- Prevents database bloat
- Implemented in: `frontend/src/utils/passwordResetCleanup.js`

### 5. **Link Expiration** ✅
- Reset links expire after 60 minutes
- Firebase enforces this automatically
- Tracked in database with `expiresAt` timestamp

### 6. **One-Time Use** ✅
- Firebase automatically invalidates links after password change
- No additional implementation needed

## Troubleshooting

### Email not received?
1. Check spam/junk folder
2. Verify email address is correct
3. Check Firebase Console logs for delivery errors
4. Verify SMTP settings in Firebase Console

### Link expired error?
- Link is valid for 60 minutes only
- Request a new reset link (invalidates old one)

### "Too many requests" error?
- Wait 5 minutes between reset requests
- This is a security feature to prevent abuse

### Password too weak?
- Must meet all password policy requirements
- Use the password strength indicator as a guide

## Environment Variables

Ensure these Firebase environment variables are set in `.env.local`:

```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_DATABASE_URL=https://your_project.firebaseio.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

## Firebase Security Rules

Add these security rules to your Firebase Realtime Database to protect password reset data:

```json
{
  "rules": {
    "passwordResetRequests": {
      ".read": false,
      ".write": true,
      "$emailHash": {
        ".validate": "newData.hasChildren(['timestamp', 'email', 'expiresAt'])"
      }
    }
  }
}
```

## Support

For issues or questions:
- Email: support@g7t1.com
- Check Firebase Console logs
- Review application console logs in browser DevTools

---

**Last Updated**: {{ current_date }}
**Maintained By**: SPM Group 7 Team 1
