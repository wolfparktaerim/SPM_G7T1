// src/stores/auth.js

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  sendPasswordResetEmail,
  onAuthStateChanged,
} from 'firebase/auth'
import { ref as dbRef, get } from 'firebase/database'
import { auth, database } from '@/firebase/firebaseConfig'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(true)
  const error = ref(null)
  const success = ref(null)
  const initialized = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  // Initialize auth state listener
  const initializeAuth = () => {
    return new Promise((resolve) => {
      const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
        if (firebaseUser) {
          try {
            // Fetch user data from Realtime Database
            const userRef = dbRef(database, `users/${firebaseUser.uid}`)
            const snapshot = await get(userRef)

            if (snapshot.exists()) {
              // Use data from Realtime Database
              const userData = snapshot.val()
              user.value = {
                uid: firebaseUser.uid,
                email: firebaseUser.email,
                // Data from Realtime Database
                name: userData.name || '',
                role: userData.role || '',
                department: userData.department || '',
                title: userData.title || '',
                displayName:
                  userData.displayName || userData.name || firebaseUser.email?.split('@')[0],
                photoURL: userData.photoURL || firebaseUser.photoURL || '',
                createdAt: userData.createdAt || Date.now(),
                lastLoginAt: userData.lastLoginAt || Date.now(),
                updatedAt: userData.updatedAt || null,
              }
            } else {
              // Fallback if no data in Realtime Database
              user.value = {
                uid: firebaseUser.uid,
                email: firebaseUser.email,
                displayName: firebaseUser.displayName || firebaseUser.email?.split('@')[0],
                photoURL: firebaseUser.photoURL || '',
                name: '',
                role: '',
                department: '',
                title: '',
                createdAt: firebaseUser.metadata.creationTime
                  ? new Date(firebaseUser.metadata.creationTime).getTime()
                  : Date.now(),
                lastLoginAt: firebaseUser.metadata.lastSignInTime
                  ? new Date(firebaseUser.metadata.lastSignInTime).getTime()
                  : Date.now(),
              }
            }
            console.log('User data loaded:', user.value)
          } catch (error) {
            console.error('Error fetching user data from Realtime Database:', error)
            // Fallback to basic Firebase Auth data
            user.value = {
              uid: firebaseUser.uid,
              email: firebaseUser.email,
              displayName: firebaseUser.displayName || firebaseUser.email?.split('@')[0],
              photoURL: firebaseUser.photoURL || '',
              name: '',
              role: '',
              department: '',
              title: '',
              createdAt: firebaseUser.metadata.creationTime
                ? new Date(firebaseUser.metadata.creationTime).getTime()
                : Date.now(),
              lastLoginAt: firebaseUser.metadata.lastSignInTime
                ? new Date(firebaseUser.metadata.lastSignInTime).getTime()
                : Date.now(),
            }
          }
        } else {
          user.value = null
        }

        loading.value = false
        if (!initialized.value) {
          initialized.value = true
          resolve()
        }
      })

      return unsubscribe
    })
  }

  // Sign in with email and password
  const signInWithEmail = async (email, password) => {
    try {
      error.value = null
      success.value = null
      loading.value = true
      await signInWithEmailAndPassword(auth, email, password)
    } catch (err) {
      error.value = getFirebaseErrorMessage(err.code) || 'Sign in failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Sign up with email and password
  const signUpWithEmail = async (email, password) => {
    try {
      error.value = null
      success.value = null
      loading.value = true

      const userCredential = await createUserWithEmailAndPassword(auth, email, password)
      return userCredential // Return the credential so we can access the user immediately
    } catch (err) {
      error.value = getFirebaseErrorMessage(err.code) || 'Sign up failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Sign in with Google
  const signInWithGoogle = async () => {
    try {
      error.value = null
      success.value = null
      loading.value = true
      const provider = new GoogleAuthProvider()
      await signInWithPopup(auth, provider)
    } catch (err) {
      error.value = getFirebaseErrorMessage(err.code) || 'Google sign in failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Send password reset email
  const sendPasswordReset = async (email) => {
    try {
      error.value = null
      success.value = null
      loading.value = true

      await sendPasswordResetEmail(auth, email, {
        url: window.location.origin + '/authentication', // Redirect back to auth page after reset
        handleCodeInApp: false,
      })

      success.value = 'Password reset email sent! Please check your inbox and spam folder.'
    } catch (err) {
      error.value = getFirebaseErrorMessage(err.code) || 'Failed to send password reset email'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Sign out
  const signOutUser = async () => {
    try {
      error.value = null
      success.value = null
      await signOut(auth)
    } catch (err) {
      error.value = getFirebaseErrorMessage(err.code) || 'Sign out failed'
      throw err
    }
  }

  // Clear messages
  const clearError = () => {
    error.value = null
  }

  const clearSuccess = () => {
    success.value = null
  }

  const clearMessages = () => {
    error.value = null
    success.value = null
  }

  // Helper function to convert Firebase error codes to user-friendly messages
  const getFirebaseErrorMessage = (errorCode) => {
    switch (errorCode) {
      case 'auth/user-not-found':
        return 'No account found with this email address.'
      case 'auth/wrong-password':
        return 'Incorrect password. Please try again.'
      case 'auth/invalid-email':
        return 'Invalid email address format.'
      case 'auth/user-disabled':
        return 'This account has been disabled.'
      case 'auth/email-already-in-use':
        return 'An account with this email already exists.'
      case 'auth/weak-password':
        return 'Password is too weak. Please choose a stronger password.'
      case 'auth/operation-not-allowed':
        return 'This sign-in method is not enabled.'
      case 'auth/invalid-credential':
        return 'Invalid email or password. Please check your credentials.'
      case 'auth/too-many-requests':
        return 'Too many failed attempts. Please try again later.'
      case 'auth/network-request-failed':
        return 'Network error. Please check your internet connection.'
      case 'auth/popup-closed-by-user':
        return 'Sign-in popup was closed. Please try again.'
      case 'auth/cancelled-popup-request':
        return 'Sign-in was cancelled. Please try again.'
      case 'auth/popup-blocked':
        return 'Popup was blocked by your browser. Please allow popups and try again.'
      case 'auth/missing-email':
        return 'Please enter your email address.'
      case 'auth/invalid-action-code':
        return 'The password reset link is invalid or has expired.'
      case 'auth/expired-action-code':
        return 'The password reset link has expired. Please request a new one.'
      default:
        return 'An unexpected error occurred. Please try again.'
    }
  }

  return {
    user,
    loading,
    error,
    success,
    initialized,
    isAuthenticated,
    initializeAuth,
    signInWithEmail,
    signUpWithEmail,
    signInWithGoogle,
    sendPasswordReset,
    signOutUser,
    clearError,
    clearSuccess,
    clearMessages,
  }
})
