// API Integration Client for CineForge AI Backend

const API_BASE_URL = "http://localhost:5001";

class CineForgeAPI {
    constructor() {
        this.baseUrl = API_BASE_URL;
    }

    /**
     * Retrieves the authorization token (Firebase ID token or mock token).
     */
    _getToken() {
        // First check mock auth token
        const mockToken = localStorage.getItem("cineforge_mock_token");
        if (mockToken) return mockToken;

        // Otherwise check real Firebase Auth
        if (window.firebase && firebase.auth().currentUser) {
            return localStorage.getItem("cineforge_fb_token") || "";
        }
        return "";
    }

    /**
     * General fetch request wrapper.
     */
    async _request(endpoint, method = "GET", body = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = this._getToken();
        
        const headers = {
            "Content-Type": "application/json"
        };
        
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const config = {
            method,
            headers
        };

        if (body && (method === "POST" || method === "PUT" || method === "DELETE")) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error(`API Request Error on ${endpoint}:`, error);
            throw error;
        }
    }

    // --- Authentication Syncs ---
    async signup(uid, name, email) {
        return this._request("/signup", "POST", { uid, name, email });
    }

    async login() {
        return this._request("/login", "POST");
    }

    async getProfile() {
        return this._request("/profile", "GET");
    }

    // --- Projects CRUD ---
    async createProject(projectData) {
        return this._request("/create-project", "POST", projectData);
    }

    async getProjects() {
        return this._request("/projects", "GET");
    }

    async getProject(projectId) {
        return this._request("/project/" + projectId, "GET");
    }

    async deleteProject(projectId) {
        return this._request("/project/" + projectId, "DELETE");
    }

    // --- AI Generator Modules ---
    async generateStoryAnalysis(projectId) {
        return this._request("/generate-story-analysis", "POST", { project_id: projectId });
    }

    async generateNarrativeStructure(projectId) {
        return this._request("/generate-structure", "POST", { project_id: projectId });
    }

    async generateScreenplay(projectId) {
        return this._request("/generate-screenplay", "POST", { project_id: projectId });
    }

    async generateCharacters(projectId) {
        return this._request("/generate-characters", "POST", { project_id: projectId });
    }

    async generateScenes(projectId) {
        return this._request("/generate-scenes", "POST", { project_id: projectId });
    }

    async generateStoryboard(projectId) {
        return this._request("/generate-storyboard", "POST", { project_id: projectId });
    }

    async generateSoundDesign(projectId) {
        return this._request("/generate-sound-design", "POST", { project_id: projectId });
    }

    async generateProductionPlan(projectId) {
        return this._request("/generate-production-plan", "POST", { project_id: projectId });
    }

    // --- Document Exports ---
    async exportProject(projectId, format) {
        const url = `${this.baseUrl}/export-project`;
        const token = this._getToken();
        
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": token ? `Bearer ${token}` : ""
                },
                body: JSON.stringify({ project_id: projectId, format })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.message || "Failed to download blueprint booklet");
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = downloadUrl;
            
            // Set download attribute filename
            link.download = `cineforge_${projectId}_blueprint.${format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);
            
            return { status: "success" };
        } catch (error) {
            console.error(`Export Error on ${format}:`, error);
            throw error;
        }
    }
}

// Instantiate API wrapper globally
const api = new CineForgeAPI();
