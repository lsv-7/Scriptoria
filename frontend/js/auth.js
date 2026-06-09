// Firebase Authentication and Session Syncs

// Default Firebase Configuration (replace with your real credentials)
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// State flag indicating if Firebase client SDK is initialized
let firebaseInitialized = false;

function initFirebase() {
    if (firebaseConfig.apiKey !== "YOUR_API_KEY") {
        try {
            firebase.initializeApp(firebaseConfig);
            firebaseInitialized = true;
            console.log(">>> Firebase Client SDK initialized successfully.");
            
            // Set up state change listener
            firebase.auth().onAuthStateChanged(async (user) => {
                if (user) {
                    const token = await user.getIdToken();
                    localStorage.setItem("cineforge_fb_token", token);
                    localStorage.setItem("cineforge_user", JSON.stringify({
                        uid: user.uid,
                        name: user.displayName || "Filmmaker",
                        email: user.email
                    }));
                    
                    // Trigger sync with flask backend
                    try {
                        await api.login();
                        onUserAuthenticated();
                    } catch (err) {
                        showToast("Failed to sync session with server", "error");
                    }
                } else {
                    localStorage.removeItem("cineforge_fb_token");
                }
            });
        } catch (e) {
            console.error("Firebase SDK init error:", e);
            firebaseInitialized = false;
        }
    } else {
        console.warn("Firebase client configuration not updated. Running in local/demo mode by default.");
    }
}

/**
 * Handles signing up a new user.
 */
async function authSignup(name, email, password, useMock) {
    if (useMock) {
        // Mock Register: Generate a mock UID
        const mockUid = "mock_" + Math.random().toString(36).substring(2, 11);
        const user = { uid: mockUid, name, email };
        
        // Save mock session locally
        localStorage.setItem("cineforge_mock_token", "mock_token_" + mockUid);
        localStorage.setItem("cineforge_user", JSON.stringify(user));
        
        // Sync with backend mock-mode
        await api.signup(mockUid, name, email);
        return user;
    }

    if (!firebaseInitialized) {
        throw new Error("Firebase is not configured. Please check 'Enable Demo Mode' checkbox to log in instantly!");
    }

    try {
        const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        // Update display name
        await user.updateProfile({ displayName: name });
        
        // Save session
        const token = await user.getIdToken();
        localStorage.setItem("cineforge_fb_token", token);
        
        // Sync to backend Firestore users collection
        await api.signup(user.uid, name, email);
        
        const userData = { uid: user.uid, name, email };
        localStorage.setItem("cineforge_user", JSON.stringify(userData));
        return userData;
    } catch (error) {
        console.error("Firebase signup error:", error);
        throw error;
    }
}

/**
 * Handles logging in a user.
 */
async function authLogin(email, password, useMock) {
    if (useMock) {
        // Mock Login: Generate uid from email or reuse existing
        const cleanEmail = email.trim().toLowerCase();
        let uid = "mock_user_123";
        if (cleanEmail) {
            uid = "mock_" + btoa(cleanEmail).substring(0, 10).replace(/[^a-zA-Z0-9]/g, "");
        }
        const user = {
            uid: uid,
            name: "Local Filmmaker",
            email: email || "filmmaker@cineforge.local"
        };
        
        // Save mock session
        localStorage.setItem("cineforge_mock_token", "mock_token_" + uid);
        localStorage.setItem("cineforge_user", JSON.stringify(user));
        
        // Sync to flask
        await api.login();
        return user;
    }

    if (!firebaseInitialized) {
        throw new Error("Firebase is not configured. Please check 'Enable Demo Mode' checkbox to log in instantly!");
    }

    try {
        const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
        const user = userCredential.user;
        const token = await user.getIdToken();
        localStorage.setItem("cineforge_fb_token", token);
        
        const userData = {
            uid: user.uid,
            name: user.displayName || "Filmmaker",
            email: user.email
        };
        localStorage.setItem("cineforge_user", JSON.stringify(userData));
        return userData;
    } catch (error) {
        console.error("Firebase login error:", error);
        throw error;
    }
}

/**
 * Sign in using Google Social Authentication.
 */
async function authGoogleSignIn(useMock) {
    if (useMock) {
        return authLogin("google.user@cineforge.local", "", true);
    }

    if (!firebaseInitialized) {
        throw new Error("Firebase is not configured. Enable demo mode to log in.");
    }

    try {
        const provider = new firebase.auth.GoogleAuthProvider();
        const userCredential = await firebase.auth().signInWithPopup(provider);
        const user = userCredential.user;
        const token = await user.getIdToken();
        localStorage.setItem("cineforge_fb_token", token);
        
        const userData = {
            uid: user.uid,
            name: user.displayName || "Filmmaker",
            email: user.email
        };
        localStorage.setItem("cineforge_user", JSON.stringify(userData));
        
        // Sync
        await api.login();
        return userData;
    } catch (error) {
        console.error("Google sign in error:", error);
        throw error;
    }
}

/**
 * Clear session data and sign out.
 */
async function authLogout() {
    localStorage.removeItem("cineforge_mock_token");
    localStorage.removeItem("cineforge_fb_token");
    localStorage.removeItem("cineforge_user");
    localStorage.removeItem("cineforge_active_project_id");
    
    if (firebaseInitialized) {
        try {
            await firebase.auth().signOut();
        } catch (e) {
            console.error("Firebase sign out error:", e);
        }
    }
}

// Initialize on load
initFirebase();
