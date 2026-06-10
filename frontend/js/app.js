// CineForge AI Single Page Application Main Logic Controller

// --- STATE MANAGEMENT ---
let currentUser = null;
let activeProject = null;
let activeProjectData = null; // Client-side cache of all project pre-production data
let allProjects = [];
let currentScreenplayScenes = [];
let lastScreenplayDoc = null;
let lastSceneBreakdown = null;
let currentStoryboardDoc = null; // Stored storyboard document
let storyboardViewMode = "grid"; // "grid" or "carousel"
let currentStoryboardSlideIndex = 0; // Active slide for Presenter Mode
let chatHistory = [];


// --- GENERAL HELPER FOR SAFE OBJECT/ARRAY TEXT FORMATTING ---
function formatValue(val) {
    if (val === undefined || val === null) {
        return "N/A";
    }
    if (typeof val === "object") {
        if (Array.isArray(val)) {
            if (val.length === 0) return "None";
            if (typeof val[0] === "object") {
                return "<ul style='margin-left: 15px; list-style-type: disc;'>" + val.map(item => {
                    const fields = Object.entries(item)
                        .map(([k, v]) => `<strong>${k.replace(/_/g, ' ').toUpperCase()}:</strong> ${formatValue(v)}`)
                        .join(" | ");
                    return `<li style='margin-bottom: 5px;'>${fields}</li>`;
                }).join("") + "</ul>";
            }
            return "<ul style='margin-left: 15px; list-style-type: disc;'>" + val.map(item => `<li style='margin-bottom: 5px;'>${formatValue(item)}</li>`).join("") + "</ul>";
        }
        return "<ul style='margin-left: 15px; list-style-type: disc;'>" + Object.entries(val).map(([k, v]) => {
            return `<li style='margin-bottom: 5px;'><strong>${k.replace(/_/g, ' ').toUpperCase()}:</strong> ${formatValue(v)}</li>`;
        }).join("") + "</ul>";
    }
    return String(val).replace(/\n/g, "<br/>");
}

/**
 * Handles image loading errors on storyboard cards to swap to a backup URL
 * and avoids infinite error loops by setting a custom data attribute.
 */
function handleStoryboardImageError(img, backupUrl) {
    if (img.getAttribute("data-failed") === "true") {
        // Backup image failed too, resolve loader cleanly
        const loader = img.parentNode.querySelector(".film-reel-loader");
        if (loader) loader.remove();
        img.style.opacity = "1";
        return;
    }
    img.setAttribute("data-failed", "true");
    img.src = backupUrl;
}

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    checkAuthenticationState();

    
    // Automatically bind key controls for modals and storyboard carousel navigation
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const openModal = document.querySelector(".modal.active");
            if (openModal) closeModal(openModal.id);
        }
        
        // Presenter mode carousel arrow key navigation
        if (storyboardViewMode === "carousel" && document.getElementById("subview-storyboard").classList.contains("active")) {
            if (e.key === "ArrowRight" || e.key === "Right") {
                storyboardNextSlide();
            } else if (e.key === "ArrowLeft" || e.key === "Left") {
                storyboardPrevSlide();
            }
        }
    });
});

/**
 * Checks if a user is logged in (from local storage) and updates the layout.
 */
function checkAuthenticationState() {
    const userStr = localStorage.getItem("cineforge_user");
    if (userStr) {
        currentUser = JSON.parse(userStr);
        onUserAuthenticated();
    } else {
        showLandingPage();
    }
}

function showLandingPage() {
    currentUser = null;
    activeProject = null;
    activeProjectData = null; // Clear cache
    document.getElementById("landing-view").style.display = "flex";
    document.getElementById("dashboard-view").style.display = "none";
}

function onUserAuthenticated() {
    document.getElementById("landing-view").style.display = "none";
    document.getElementById("dashboard-view").style.display = "flex";
    
    // Update User Profile UI
    if (currentUser) {
        document.getElementById("welcome-user-name").innerText = currentUser.name;
        document.getElementById("user-display-name").innerText = currentUser.name;
        document.getElementById("user-display-email").innerText = currentUser.email;
        
        // Init initials avatar
        const initials = currentUser.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
        document.getElementById("user-avatar-initials").innerText = initials;
    }
    
    // Refresh Projects List
    refreshProjectsList();
    
    // Restore active project if saved
    const activeProjId = localStorage.getItem("cineforge_active_project_id");
    if (activeProjId) {
        loadProjectIntoSession(activeProjId, false);
    } else {
        updateActiveProjectBar(null);
        switchSubview("dashboard");
    }
}

// --- SUB-VIEW ROUTING CONTROLLER ---
function switchSubview(subviewId) {
    // Check if subview requires an active project
    const restrictedViews = ["story", "screenplay", "characters", "scenes", "storyboard", "sound", "production", "budget", "export"];
    
    if (restrictedViews.includes(subviewId) && !activeProject) {
        showToast("Please select or create a project first!", "error");
        switchSubview("dashboard");
        return;
    }

    // Deactivate all sections and sidebar links
    const sections = document.querySelectorAll(".view-section");
    sections.forEach(sec => sec.classList.remove("active"));
    
    const sidebarLinks = document.querySelectorAll(".sidebar-link");
    sidebarLinks.forEach(link => link.classList.remove("active"));

    // Activate selected section
    const targetSection = document.getElementById(`subview-${subviewId}`);
    if (targetSection) {
        targetSection.classList.add("active");
    }

    // Highlight active sidebar link
    sidebarLinks.forEach(link => {
        const text = link.innerText.trim();
        if (text.toLowerCase().includes(subviewId === "story" ? "story analysis" : subviewId)) {
            link.classList.add("active");
        } else if (subviewId === "scenes" && text.toLowerCase().includes("scene breakdown")) {
            link.classList.add("active");
        } else if (subviewId === "production" && text.toLowerCase().includes("production plan")) {
            link.classList.add("active");
        } else if (subviewId === "sound" && text.toLowerCase().includes("sound design")) {
            link.classList.add("active");
        }
    });

    // Update Header Title
    const headerTitleMap = {
        "dashboard": "Dashboard Overview",
        "story": "Story Analysis & Acts",
        "screenplay": "Screenplay Generator",
        "characters": "Character Designer",
        "scenes": "Scene Breakdown List",
        "storyboard": "Storyboard Prompts",
        "sound": "Sound Design Blueprint",
        "production": "Production Planning",
        "budget": "Budget Planner & Cost Estimator",
        "export": "Export Center",
        "projects": "My Projects Directory"
    };
    document.getElementById("current-subview-title").innerText = headerTitleMap[subviewId] || "Studio";

    // Auto load view specifics if project loaded
    if (activeProject) {
        loadViewSpecificData(subviewId);
    }

    // Manage chatbot visibility based on active subview
    const chatbotContainer = document.getElementById("chatbot-container");
    if (chatbotContainer) {
        if (activeProject && subviewId !== "projects") {
            chatbotContainer.style.display = "block";
        } else {
            chatbotContainer.style.display = "none";
            const chatWindow = document.getElementById("chatbot-window");
            if (chatWindow) chatWindow.style.display = "none";
        }
    }
}

/**
 * Enables/Disables restricted sidebar links based on whether a project is active.
 */
function toggleRestrictedSidebarLinks(active) {
    const links = document.querySelectorAll(".sidebar-link.generation-link");
    links.forEach(link => {
        if (active) {
            link.classList.remove("disabled");
        } else {
            link.classList.add("disabled");
        }
    });

    const chatbotContainer = document.getElementById("chatbot-container");
    if (chatbotContainer) {
        if (active) {
            chatbotContainer.style.display = "block";
        } else {
            chatbotContainer.style.display = "none";
            const chatWindow = document.getElementById("chatbot-window");
            if (chatWindow) chatWindow.style.display = "none";
            resetChatbot();
        }
    }
}

// --- FORM SUBMISSIONS ---

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const isMock = document.getElementById("login-mock-toggle").checked;

    try {
        const user = await authLogin(email, password, isMock);
        currentUser = user;
        
        // Clear old active project session to prevent cross-user leakage
        activeProject = null;
        localStorage.removeItem("cineforge_active_project_id");
        
        closeModal("login-modal");
        onUserAuthenticated();
        showToast("Logged in successfully!", "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById("register-name").value;
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;
    const isMock = document.getElementById("register-mock-toggle").checked;

    try {
        const user = await authSignup(name, email, password, isMock);
        currentUser = user;
        
        // Clear old active project session to prevent cross-user leakage
        activeProject = null;
        localStorage.removeItem("cineforge_active_project_id");
        
        closeModal("register-modal");
        onUserAuthenticated();
        showToast("Account created successfully!", "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function handleGoogleSignIn() {
    const isMock = document.getElementById("login-mock-toggle").checked;
    try {
        const user = await authGoogleSignIn(isMock);
        currentUser = user;
        
        // Clear old active project session to prevent cross-user leakage
        activeProject = null;
        localStorage.removeItem("cineforge_active_project_id");
        
        closeModal("login-modal");
        onUserAuthenticated();
        showToast("Logged in with Google!", "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function handleLogout() {
    await authLogout();
    activeProject = null;
    localStorage.removeItem("cineforge_active_project_id");
    showLandingPage();
    showToast("Logged out successfully.", "info");
}

async function handleCreateProject(e) {
    e.preventDefault();
    const project_name = document.getElementById("proj-name").value;
    const genre = document.getElementById("proj-genre").value;
    const target_audience = document.getElementById("proj-audience").value;
    const story_idea = document.getElementById("proj-idea").value;
    const duration_length = document.getElementById("proj-duration").value;

    const payload = { project_name, genre, target_audience, story_idea, duration_length };

    try {
        const response = await api.createProject(payload);
        const newProj = response.data;
        closeModal("create-project-modal");
        
        // Reset Form
        document.getElementById("create-project-form").reset();
        
        // Show global generation overlay
        const overlay = document.getElementById("global-gen-overlay");
        overlay.classList.add("active");
        
        // Reset step classes
        const steps = ["step-char", "step-story", "step-scenes", "step-script", "step-assets"];
        steps.forEach(id => {
            document.getElementById(id).className = "global-gen-step";
        });
        
        // Step 1 active
        document.getElementById("step-char").className = "global-gen-step active";
        
        // Timer to simulate stage steps while waiting for backend
        const stepInterval = setInterval(() => {
            const charEl = document.getElementById("step-char");
            const storyEl = document.getElementById("step-story");
            const scenesEl = document.getElementById("step-scenes");
            const scriptEl = document.getElementById("step-script");
            const assetsEl = document.getElementById("step-assets");
            
            if (charEl.classList.contains("active")) {
                charEl.className = "global-gen-step completed";
                storyEl.className = "global-gen-step active";
            } else if (storyEl.classList.contains("active")) {
                storyEl.className = "global-gen-step completed";
                scenesEl.className = "global-gen-step active";
            } else if (scenesEl.classList.contains("active")) {
                scenesEl.className = "global-gen-step completed";
                scriptEl.className = "global-gen-step active";
            } else if (scriptEl.classList.contains("active")) {
                scriptEl.className = "global-gen-step completed";
                assetsEl.className = "global-gen-step active";
            }
        }, 3500);
        
        // Trigger all-in-one pre-production generator
        await api.generateAllPreproduction(newProj.project_id);
        
        clearInterval(stepInterval);
        
        // Mark all steps completed
        steps.forEach(id => {
            document.getElementById(id).className = "global-gen-step completed";
        });
        
        // Hold briefly to show completion
        await new Promise(resolve => setTimeout(resolve, 800));
        overlay.classList.remove("active");
        
        // Load the new project
        await loadProjectIntoSession(newProj.project_id);
        
        showToast("New project pre-production package ready!", "success");
    } catch (err) {
        document.getElementById("global-gen-overlay").classList.remove("active");
        showToast("Failed to initialize project pre-production package: " + err.message, "error");
    }
}

// --- PROJECT LOADING AND WORKSPACE MANAGEMENT ---

async function loadProjectIntoSession(projectId, redirect = true) {
    try {
        const response = await api.getProject(projectId);
        const compiled = response.data;
        
        // Safety verification: verify current user ownership
        if (!currentUser || compiled.project.user_id !== currentUser.uid) {
            throw new Error("Access denied: You do not own this project.");
        }
        
        activeProject = compiled.project;
        activeProjectData = compiled; // Store the compiled data in cache
        localStorage.setItem("cineforge_active_project_id", projectId);
        
                updateActiveProjectBar(activeProject);
        toggleRestrictedSidebarLinks(true);
        resetChatbot();
        
        // Render project state
        renderProjectDashboardSummary(compiled);
        
        if (redirect) {
            switchSubview("dashboard");
        }
        
        showToast(`Project '${activeProject.project_name}' loaded.`, "success");
    } catch (err) {
        showToast("Failed to open project: " + err.message, "error");
        // Clear broken session key
        localStorage.removeItem("cineforge_active_project_id");
        activeProject = null;
        updateActiveProjectBar(null);
        toggleRestrictedSidebarLinks(false);
    }
}

function updateActiveProjectBar(project) {
    const activeBar = document.getElementById("active-project-name");
    if (project) {
        activeBar.innerText = project.project_name;
    } else {
        activeBar.innerText = "No Project Active";
    }
}

async function refreshProjectsList() {
    try {
        const response = await api.getProjects();
        allProjects = response.data;
        renderProjectsGrid(allProjects);
    } catch (err) {
        console.error("Error refreshing projects list:", err);
    }
}

async function deleteProjectConfirm(projectId) {
    if (confirm("Are you absolutely sure you want to delete this project? All generated screenplays and blueprint assets will be permanently removed.")) {
        try {
            await api.deleteProject(projectId);
            showToast("Project deleted successfully.", "info");
            
            // If deleting the active project, clear workspace
            if (activeProject && activeProject.project_id === projectId) {
                activeProject = null;
                activeProjectData = null; // Clear cache
                localStorage.removeItem("cineforge_active_project_id");
                updateActiveProjectBar(null);
                toggleRestrictedSidebarLinks(false);
                switchSubview("dashboard");
            }
            
            refreshProjectsList();
        } catch (err) {
            showToast("Delete failed: " + err.message, "error");
        }
    }
}

// --- TRIGGERING AI GENERATORS ---

async function triggerStoryAnalysis() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-story-analysis");
    loader.classList.add("active");
    
    try {
        const response = await api.generateStoryAnalysis(activeProject.project_id);
        if (activeProjectData) activeProjectData.story_analysis = response.data;
        renderStoryAnalysis(response.data);
        showToast("Story analysis completed!", "success");
    } catch (err) {
        showToast("Analysis failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerNarrativeStructure() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-story-structure");
    loader.classList.add("active");
    
    try {
        const response = await api.generateNarrativeStructure(activeProject.project_id);
        if (activeProjectData) activeProjectData.narrative_structure = response.data;
        renderNarrativeStructure(response.data);
        showToast("Narrative structure formulated!", "success");
    } catch (err) {
        showToast("Structure failure: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerScreenplay() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-screenplay");
    loader.classList.add("active");
    
    try {
        const response = await api.generateScreenplay(activeProject.project_id);
        if (!lastSceneBreakdown) {
            const projRes = await api.getProject(activeProject.project_id);
            lastSceneBreakdown = projRes.data.scene_breakdown;
        }
        if (activeProjectData) {
            activeProjectData.screenplay = response.data;
            activeProjectData.scene_breakdown = lastSceneBreakdown;
        }
        renderScreenplay(response.data, lastSceneBreakdown);
        showToast("Screenplay generated successfully!", "success");
    } catch (err) {
        showToast("Screenplay generation failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerCharacters() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-characters");
    loader.classList.add("active");
    
    try {
        const response = await api.generateCharacters(activeProject.project_id);
        if (activeProjectData) activeProjectData.characters = response.data;
        renderCharacters(response.data);
        showToast("Characters designed successfully!", "success");
    } catch (err) {
        showToast("Character design failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerScenes() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-scenes");
    loader.classList.add("active");
    
    try {
        const response = await api.generateScenes(activeProject.project_id);
        if (activeProjectData) {
            activeProjectData.scene_breakdown = response.data;
        }
        lastSceneBreakdown = response.data;
        renderScenes(response.data);
        showToast("Scene breakdown completed!", "success");
    } catch (err) {
        showToast("Scene breakdown failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerStoryboard() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-storyboard");
    loader.classList.add("active");
    
    try {
        const response = await api.generateStoryboard(activeProject.project_id);
        if (activeProjectData) activeProjectData.storyboard = response.data;
        renderStoryboard(response.data);
        showToast("Storyboard prompts mapped!", "success");
    } catch (err) {
        showToast("Storyboard generation failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerSoundDesign() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-sound");
    loader.classList.add("active");
    
    try {
        const response = await api.generateSoundDesign(activeProject.project_id);
        if (activeProjectData) activeProjectData.sound_design = response.data;
        renderSoundDesign(response.data);
        showToast("Auditory blueprint formatted!", "success");
    } catch (err) {
        showToast("Sound design failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerProductionPlan() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-production");
    loader.classList.add("active");
    
    try {
        const response = await api.generateProductionPlan(activeProject.project_id);
        if (activeProjectData) activeProjectData.production_plan = response.data;
        renderProductionPlan(response.data);
        showToast("Production logistics planned!", "success");
    } catch (err) {
        showToast("Production plan failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function triggerBudgetPlan() {
    if (!activeProject) return;
    const loader = document.getElementById("loader-budget");
    loader.classList.add("active");
    
    try {
        const response = await api.generateBudgetPlan(activeProject.project_id);
        if (activeProjectData) activeProjectData.budget_plan = response.data;
        renderBudgetPlan(response.data);
        showToast("Budget plan estimated!", "success");
    } catch (err) {
        showToast("Budget planner failed: " + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}

async function exportProjectFile(format) {
    if (!activeProject) return;
    showToast(`Assembling blueprint and preparing your ${format.toUpperCase()} download...`, "info");
    
    try {
        await api.exportProject(activeProject.project_id, format);
        showToast(`${format.toUpperCase()} downloaded successfully!`, "success");
    } catch (err) {
        showToast("Export download failed: " + err.message, "error");
    }
}

// --- DYNAMIC DATA LOADING AND RENDERS ---

async function loadViewSpecificData(viewId) {
    try {
        if (!activeProjectData) {
            // Fetch fresh project details containing all generated objects
            const response = await api.getProject(activeProject.project_id);
            activeProjectData = response.data;
        }
        renderView(viewId, activeProjectData);
    } catch (err) {
        console.error(`Error loading data for ${viewId}:`, err);
    }
}

function renderView(viewId, compiled) {
    switch (viewId) {
        case "dashboard":
            renderProjectDashboardSummary(compiled);
            break;
        case "story":
            renderStoryAnalysis(compiled.story_analysis);
            renderNarrativeStructure(compiled.narrative_structure);
            break;
        case "screenplay":
            renderScreenplay(compiled.screenplay, compiled.scene_breakdown);
            break;
        case "characters":
            renderCharacters(compiled.characters);
            break;
        case "scenes":
            renderScenes(compiled.scene_breakdown);
            break;
        case "storyboard":
            renderStoryboard(compiled.storyboard);
            break;
        case "sound":
            renderSoundDesign(compiled.sound_design);
            break;
        case "production":
            renderProductionPlan(compiled.production_plan);
            break;
        case "budget":
            renderBudgetPlan(compiled.budget_plan);
            break;
    }
}

function renderProjectDashboardSummary(compiled) {
    const summaryCard = document.getElementById("active-project-details");
    summaryCard.style.display = "block";
    
    const proj = compiled.project;
    document.getElementById("summary-project-name").innerText = proj.project_name;
    document.getElementById("summary-project-genre").innerText = proj.genre;
    document.getElementById("summary-project-audience").innerText = proj.target_audience;
    document.getElementById("summary-project-idea").innerText = proj.story_idea;
    
    // Update checklists status
    document.getElementById("status-story").innerText = compiled.story_analysis ? "Ready" : "Missing";
    document.getElementById("status-story").className = compiled.story_analysis ? "badge" : "badge";
    document.getElementById("status-story").style.borderColor = compiled.story_analysis ? "var(--success)" : "var(--border-accent)";
    document.getElementById("status-story").style.color = compiled.story_analysis ? "var(--success)" : "var(--accent-purple)";
    
    document.getElementById("status-screenplay").innerText = compiled.screenplay ? "Ready" : "Missing";
    document.getElementById("status-screenplay").className = compiled.screenplay ? "badge" : "badge";
    document.getElementById("status-screenplay").style.borderColor = compiled.screenplay ? "var(--success)" : "var(--border-accent)";
    document.getElementById("status-screenplay").style.color = compiled.screenplay ? "var(--success)" : "var(--accent-purple)";
    
    document.getElementById("status-characters").innerText = compiled.characters ? "Ready" : "Missing";
    document.getElementById("status-characters").className = compiled.characters ? "badge" : "badge";
    document.getElementById("status-characters").style.borderColor = compiled.characters ? "var(--success)" : "var(--border-accent)";
    document.getElementById("status-characters").style.color = compiled.characters ? "var(--success)" : "var(--accent-purple)";
}

function renderStoryAnalysis(analysis) {
    const container = document.getElementById("output-story-analysis");
    if (!analysis || !analysis.genre_analysis) {
        container.innerHTML = `
            <div class="screenplay-empty">
                <i class="fa-solid fa-magnifying-glass-chart" style="font-size: 2.5rem; margin-bottom: 10px; color: var(--color-muted);"></i>
                <p>Story insights will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    container.className = ""; // Remove centering wrapper class if needed
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div><strong>Logline:</strong> <div>${formatValue(analysis.logline)}</div></div>
            <div><strong>Tagline:</strong> <div style="font-style: italic; color: var(--accent-gold);">"${formatValue(analysis.tagline)}"</div></div>
            <div><strong>Synopsis:</strong> <div style="font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap;">${formatValue(analysis.synopsis)}</div></div>
            <div><strong>Genre Analysis:</strong> <div style="font-size: 0.9rem;">${formatValue(analysis.genre_analysis)}</div></div>
            <div><strong>Theme:</strong> <div style="font-size: 0.9rem;">${formatValue(analysis.theme)}</div></div>
            <div><strong>Audience Insights:</strong> <div style="font-size: 0.9rem;">${formatValue(analysis.audience_insights)}</div></div>
        </div>
    `;
}

function renderNarrativeStructure(structure) {
    const container = document.getElementById("output-story-structure");
    if (!structure || !structure.act_1) {
        container.innerHTML = `
            <div class="screenplay-empty">
                <i class="fa-solid fa-shapes" style="font-size: 2.5rem; margin-bottom: 10px; color: var(--color-muted);"></i>
                <p>3-Act narrative structure will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    container.className = "";
    
    let html = '<div style="display: flex; flex-direction: column; gap: 1.25rem;">';
    ["act_1", "act_2", "act_3"].forEach(key => {
        const act = structure[key];
        if (act) {
            html += `
                <div style="border-left: 3px solid var(--accent-purple); padding-left: 12px;">
                    <h4 style="color: var(--accent-gold); margin-bottom: 4px;">${act.title}</h4>
                    <p style="font-size: 0.9rem; margin-bottom: 4px;"><strong>Description:</strong> ${act.description}</p>
                    <p style="font-size: 0.85rem; color: var(--color-secondary);"><strong>Conflict:</strong> ${act.conflict}</p>
                    <p style="font-size: 0.85rem; color: var(--color-secondary);"><strong>Rising Action:</strong> ${act.rising_action}</p>
                    ${act.resolution ? `<p style="font-size: 0.85rem; color: var(--color-secondary);"><strong>Resolution:</strong> ${act.resolution}</p>` : ""}
                </div>
            `;
        }
    });
    html += '</div>';
    container.innerHTML = html;
}


function onScreenplaySceneChanged() {
    const select = document.getElementById("screenplay-scene-select");
    const selectedValue = parseInt(select.value, 10);
    
    if (selectedValue === -1) {
        if (lastScreenplayDoc && lastScreenplayDoc.screenplay_text) {
            renderScreenplayText(lastScreenplayDoc.screenplay_text);
        } else {
            document.getElementById("screenplay-paper").innerHTML = `
                <div class="screenplay-empty">
                    <i class="fa-solid fa-scroll" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                    <p>The screenplay script will be displayed here once loaded.</p>
                </div>`;
        }
    } else {
        renderSelectedSceneView(selectedValue);
    }
}

function renderScreenplay(screenplay, sceneBreakdown) {
    const paper = document.getElementById("screenplay-paper");
    lastScreenplayDoc = screenplay;
    lastSceneBreakdown = sceneBreakdown;
    
    const selectWrapper = document.getElementById("screenplay-scene-select-wrapper");
    const select = document.getElementById("screenplay-scene-select");
    
    if (!sceneBreakdown || !sceneBreakdown.scenes || sceneBreakdown.scenes.length === 0) {
        selectWrapper.style.display = "none";
        paper.innerHTML = `
            <div class="screenplay-empty">
                <i class="fa-solid fa-list-check" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>No Scene Breakdown found. Please generate the <strong>Scene Breakdown</strong> first to formulate the screenplay.</p>
                <button class="btn btn-gold" onclick="switchSubview('scenes')" style="margin-top: 15px;">
                    <i class="fa-solid fa-arrow-right"></i> Go to Scene Breakdown
                </button>
            </div>`;
        return;
    }
    
    // Save current selected value if any
    const prevSelected = select.value ? parseInt(select.value, 10) : -1;
    
    // Populate select
    select.innerHTML = `<option value="-1" style="color: #111111 !important; background-color: #ffffff !important;">Show Full Script</option>`;
    sceneBreakdown.scenes.forEach((scene) => {
        select.innerHTML += `<option value="${scene.scene_number}" style="color: #111111 !important; background-color: #ffffff !important;">Scene ${scene.scene_number}: ${cleanLocationForDisplay(scene.location)}</option>`;
    });
    selectWrapper.style.display = "block";
    
    // Restore selection if it still exists
    if (prevSelected !== -1 && sceneBreakdown.scenes.some(s => parseInt(s.scene_number, 10) === prevSelected)) {
        select.value = prevSelected;
    } else {
        select.value = "-1";
    }
    
    const selectedValue = parseInt(select.value, 10);
    if (selectedValue === -1) {
        if (screenplay && screenplay.screenplay_text) {
            renderScreenplayText(screenplay.screenplay_text);
        } else {
            paper.innerHTML = `
                <div class="screenplay-empty">
                    <i class="fa-solid fa-scroll" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                    <p>The screenplay script will be displayed here once loaded.</p>
                </div>`;
        }
    } else {
        renderSelectedSceneView(selectedValue);
    }
}

function renderScreenplayText(text) {
    const paper = document.getElementById("screenplay-paper");
    if (!text) {
        paper.innerHTML = `
            <div class="screenplay-empty">
                <i class="fa-solid fa-scroll" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>The screenplay script will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    const lines = text.split("\n");
    let formattedHtml = "";
    
    lines.forEach(line => {
        const stripped = line.trim();
        if (!stripped) {
            formattedHtml += "<br/>";
            return;
        }
        
        // Match INT/EXT Scene headings
        if (stripped.startsWith("INT.") || stripped.startsWith("EXT.")) {
            formattedHtml += `<div style="font-weight: bold; margin-top: 1rem; text-transform: uppercase;">${stripped}</div>`;
        }
        // Match Character names (caps, relatively short, not scene heading)
        else if (stripped === stripped.toUpperCase() && stripped.length < 25 && !stripped.includes("FADE IN") && !stripped.includes("FADE OUT") && !stripped.includes("CUT TO")) {
            formattedHtml += `<div style="text-align: center; margin-top: 0.75rem; font-weight: bold; letter-spacing: 0.5px;">${stripped}</div>`;
        }
        // Match Parenthetical notes
        else if (stripped.startsWith("(")) {
            formattedHtml += `<div style="padding-left: 25%; padding-right: 25%; font-style: italic; font-size: 0.95em;">${stripped}</div>`;
        }
        // Match Dialogue lines (indented space)
        else if (line.startsWith("          ") || line.startsWith("\t\t")) {
            formattedHtml += `<div style="padding-left: 20%; padding-right: 20%;">${stripped}</div>`;
        }
        // Action blocks
        else {
            formattedHtml += `<div style="margin-top: 0.5rem; text-align: left;">${stripped}</div>`;
        }
    });
    
    paper.innerHTML = `<div style="padding: 2rem 0;">${formattedHtml}</div>`;
}

function renderSelectedSceneView(sceneNumber) {
    const paper = document.getElementById("screenplay-paper");
    if (!lastSceneBreakdown || !lastSceneBreakdown.scenes) return;
    
    const sceneInfo = lastSceneBreakdown.scenes.find(s => parseInt(s.scene_number, 10) === sceneNumber);
    const sceneLocation = sceneInfo ? sceneInfo.location : `Scene ${sceneNumber}`;
    const sceneObjective = sceneInfo ? sceneInfo.objective : "No objective specified.";
    const sceneCharacters = sceneInfo ? sceneInfo.characters : "N/A";
    const sceneDuration = sceneInfo ? sceneInfo.duration : "2 mins";
    
    let sceneScript = "";
    if (lastScreenplayDoc && lastScreenplayDoc.scene_scripts) {
        sceneScript = lastScreenplayDoc.scene_scripts[String(sceneNumber)] || "";
    }
    
    if (sceneScript) {
        const lines = sceneScript.split("\n");
        let formattedHtml = "";
        
        lines.forEach(line => {
            const stripped = line.trim();
            if (!stripped) {
                formattedHtml += "<br/>";
                return;
            }
            if (stripped.startsWith("INT.") || stripped.startsWith("EXT.")) {
                formattedHtml += `<div style="font-weight: bold; margin-top: 1rem; text-transform: uppercase;">${stripped}</div>`;
            } else if (stripped === stripped.toUpperCase() && stripped.length < 25 && !stripped.includes("FADE IN") && !stripped.includes("FADE OUT") && !stripped.includes("CUT TO")) {
                formattedHtml += `<div style="text-align: center; margin-top: 0.75rem; font-weight: bold; letter-spacing: 0.5px;">${stripped}</div>`;
            } else if (stripped.startsWith("(")) {
                formattedHtml += `<div style="padding-left: 25%; padding-right: 25%; font-style: italic; font-size: 0.95em;">${stripped}</div>`;
            } else if (line.startsWith("          ") || line.startsWith("\t\t")) {
                formattedHtml += `<div style="padding-left: 20%; padding-right: 20%;">${stripped}</div>`;
            } else {
                formattedHtml += `<div style="margin-top: 0.5rem; text-align: left;">${stripped}</div>`;
            }
        });
        
        paper.innerHTML = `
            <div style="border-bottom: 1px solid var(--border-accent); padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: var(--accent-gold);">Scene ${sceneNumber} Script</h4>
                    <p style="margin: 2px 0 0 0; font-size: 0.8rem; color: var(--color-muted); font-style: italic;">Objective: ${sceneObjective}</p>
                </div>
                <button class="btn btn-sm btn-gold" onclick="generateSceneScript(${sceneNumber})">
                    <i class="fa-solid fa-rotate"></i> Regenerate Scene
                </button>
            </div>
            <div style="padding: 1rem 0;">${formattedHtml}</div>
        `;
    } else {
        paper.innerHTML = `
            <div class="screenplay-empty" style="padding: 4rem 2rem;">
                <i class="fa-solid fa-clapperboard" style="font-size: 3rem; margin-bottom: 15px; color: var(--accent-gold);"></i>
                <h3>Scene ${sceneNumber}: ${cleanLocationForDisplay(sceneLocation)}</h3>
                <p style="color: var(--color-muted); max-width: 500px; margin: 10px auto; line-height: 1.6;">
                    <strong>Characters:</strong> ${sceneCharacters}<br>
                    <strong>Objective:</strong> ${sceneObjective}<br>
                    <strong>Estimated Duration:</strong> ${sceneDuration}
                </p>
                <button class="btn btn-gold" onclick="generateSceneScript(${sceneNumber})" style="margin-top: 15px;">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Generate Script for this Scene
                </button>
            </div>
        `;
    }
}

async function generateSceneScript(sceneNumber) {
    if (!activeProject) return;
    const loader = document.getElementById("loader-screenplay");
    loader.classList.add("active");
    
    try {
        const response = await api._request("/generate-screenplay", "POST", {
            project_id: activeProject.project_id,
            scene_number: sceneNumber
        });
        
        lastScreenplayDoc = response.data;
        if (activeProjectData) {
            activeProjectData.screenplay = response.data;
        }
        showToast(`Scene ${sceneNumber} screenplay script generated successfully!`, "success");
        renderScreenplay(lastScreenplayDoc, lastSceneBreakdown);
    } catch (err) {
        showToast(`Scene generation failed: ` + err.message, "error");
    } finally {
        loader.classList.remove("active");
    }
}


function renderCharacters(charDoc) {
    const container = document.getElementById("characters-container");
    if (!charDoc || !charDoc.characters || charDoc.characters.length === 0) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-users" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Character profiles will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    container.innerHTML = "";
    charDoc.characters.forEach(char => {
        const card = document.createElement("div");
        card.className = "character-card";
        card.innerHTML = `
            <h3>${char.name}</h3>
            <div class="character-meta">Age: ${char.age}</div>
            <div class="character-field"><strong>Backstory:</strong><span>${char.backstory}</span></div>
            <div class="character-field"><strong>Personality:</strong><span>${char.personality}</span></div>
            <div class="character-field"><strong>Core Goals:</strong><span>${char.goals}</span></div>
            <div class="character-field"><strong>Strengths:</strong><span>${char.strengths}</span></div>
            <div class="character-field"><strong>Weaknesses:</strong><span>${char.weaknesses}</span></div>
            <div class="character-field"><strong>Arc:</strong><span>${char.arc}</span></div>
        `;
        container.appendChild(card);
    });
}

function cleanLocationForDisplay(location) {
    if (!location) return "";
    let clean = location.replace(/^(INT\.\s*|EXT\.\s*|INT\/EXT\.\s*|INT\s+|EXT\s+)/i, "").trim();
    clean = clean.replace(/\s*-\s*(DAY|NIGHT|DUSK|DAWN|LATER|CONTINUOUS|SAME TIME)\b.*$/i, "").trim();
    return clean;
}

function renderScenes(sceneDoc) {
    const container = document.getElementById("scenes-container");
    if (!sceneDoc || !sceneDoc.scenes || sceneDoc.scenes.length === 0) {
        container.innerHTML = `
            <div class="info-card text-center" style="padding: 4rem;">
                <i class="fa-solid fa-list-check" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Scene breakdowns will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    let tableHtml = `
        <table class="scene-table">
            <thead>
                <tr>
                    <th style="width: 70px;">Scene</th>
                    <th>Location Heading</th>
                    <th>Characters</th>
                    <th>Objective / Dramatic Value</th>
                    <th style="width: 100px;">Duration</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    sceneDoc.scenes.forEach(scene => {
        tableHtml += `
            <tr>
                <td><strong>#${scene.scene_number}</strong></td>
                <td style="font-family: var(--font-body); color: var(--accent-gold); font-size: 0.9rem; text-transform: uppercase;">${cleanLocationForDisplay(scene.location)}</td>
                <td>${scene.characters}</td>
                <td>${scene.objective}</td>
                <td><span class="badge" style="margin: 0; font-size: 0.75rem;">${scene.duration}</span></td>
            </tr>
        `;
    });
    
    tableHtml += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHtml;
}

function setStoryboardViewMode(mode) {
    storyboardViewMode = mode;
    
    const btnGrid = document.getElementById("btn-sb-grid");
    const btnCarousel = document.getElementById("btn-sb-carousel");
    
    if (mode === "grid") {
        btnGrid.classList.add("active");
        btnGrid.style.background = "";
        btnGrid.style.borderColor = "";
        btnCarousel.classList.remove("active");
        btnCarousel.style.background = "transparent";
        btnCarousel.style.borderColor = "transparent";
    } else {
        btnCarousel.classList.add("active");
        btnCarousel.style.background = "";
        btnCarousel.style.borderColor = "";
        btnGrid.classList.remove("active");
        btnGrid.style.background = "transparent";
        btnGrid.style.borderColor = "transparent";
    }
    
    renderStoryboard(currentStoryboardDoc);
}

function storyboardNextSlide() {
    if (!currentStoryboardDoc || !currentStoryboardDoc.storyboards) return;
    const len = currentStoryboardDoc.storyboards.length;
    currentStoryboardSlideIndex = (currentStoryboardSlideIndex + 1) % len;
    renderStoryboard(currentStoryboardDoc);
}

function storyboardPrevSlide() {
    if (!currentStoryboardDoc || !currentStoryboardDoc.storyboards) return;
    const len = currentStoryboardDoc.storyboards.length;
    currentStoryboardSlideIndex = (currentStoryboardSlideIndex - 1 + len) % len;
    renderStoryboard(currentStoryboardDoc);
}

function setStoryboardSlide(idx) {
    if (!currentStoryboardDoc || !currentStoryboardDoc.storyboards) return;
    currentStoryboardSlideIndex = idx;
    renderStoryboard(currentStoryboardDoc);
}

function renderStoryboard(sbDoc) {
    const container = document.getElementById("storyboard-container");
    currentStoryboardDoc = sbDoc;
    
    if (!sbDoc || !sbDoc.storyboards || sbDoc.storyboards.length === 0) {
        container.className = "storyboard-grid-no-images";
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-clapperboard" style="font-size: 3rem; margin-bottom: 15px; color: var(--accent-gold);"></i>
                <p>Cinematography prompts and shot configurations will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    if (storyboardViewMode === "grid") {
        container.className = "storyboard-grid-no-images";
        container.innerHTML = "";
        sbDoc.storyboards.forEach(sb => {
            const card = document.createElement("div");
            card.className = "storyboard-card-no-image";
            
            card.innerHTML = `
                <div class="storyboard-card-header">
                    <span class="storyboard-card-title">Shot #${sb.scene_number}</span>
                    <i class="fa-solid fa-video" style="color: var(--color-muted); font-size: 0.9rem;"></i>
                </div>
                <div class="storyboard-card-body">
                    <p class="storyboard-card-prompt-text">"${sb.prompt || 'No composition instructions available.'}"</p>
                </div>
                <div class="storyboard-card-directives">
                    <div class="directive-chip-horizontal">
                        <i class="fa-solid fa-arrows-to-eye"></i>
                        <span>Angle: <strong>${sb.camera_angle || 'N/A'}</strong></span>
                    </div>
                    <div class="directive-chip-horizontal">
                        <i class="fa-solid fa-lightbulb"></i>
                        <span>Lighting: <strong>${sb.lighting || 'N/A'}</strong></span>
                    </div>
                    <div class="directive-chip-horizontal">
                        <i class="fa-solid fa-masks-theater"></i>
                        <span>Mood: <strong>${sb.mood || 'N/A'}</strong></span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } else {
        container.className = "";
        
        if (currentStoryboardSlideIndex < 0) currentStoryboardSlideIndex = 0;
        if (currentStoryboardSlideIndex >= sbDoc.storyboards.length) currentStoryboardSlideIndex = sbDoc.storyboards.length - 1;
        
        const sb = sbDoc.storyboards[currentStoryboardSlideIndex];
        
        let dotsHtml = "";
        sbDoc.storyboards.forEach((_, idx) => {
            dotsHtml += `<div class="presenter-indicator-dot ${idx === currentStoryboardSlideIndex ? 'active' : ''}" onclick="setStoryboardSlide(${idx})"></div>`;
        });
        
        container.innerHTML = `
            <div class="storyboard-presenter-container">
                <div class="presenter-card-wrapper">
                    <button class="presenter-nav-btn prev" onclick="storyboardPrevSlide()">
                        <i class="fa-solid fa-chevron-left"></i>
                    </button>
                    
                    <div class="presenter-card-main">
                        <div class="presenter-card-header">
                            <span class="presenter-card-title">SHOT ${currentStoryboardSlideIndex + 1} OF ${sbDoc.storyboards.length}</span>
                            <span class="badge" style="background-color: rgba(212, 175, 55, 0.12); color: var(--accent-gold); border-color: var(--accent-gold); font-size: 0.8rem; border-radius: 4px; padding: 3px 8px;">Scene #${sb.scene_number}</span>
                        </div>
                        <div class="presenter-card-prompt">
                            "${sb.prompt || 'No composition instructions available.'}"
                        </div>
                        <div class="presenter-directives-grid">
                            <div class="presenter-directive-item">
                                <i class="fa-solid fa-arrows-to-eye"></i>
                                <span>Camera Angle</span>
                                <strong>${sb.camera_angle || 'N/A'}</strong>
                            </div>
                            <div class="presenter-directive-item">
                                <i class="fa-solid fa-lightbulb"></i>
                                <span>Lighting Setup</span>
                                <strong>${sb.lighting || 'N/A'}</strong>
                            </div>
                            <div class="presenter-directive-item">
                                <i class="fa-solid fa-masks-theater"></i>
                                <span>Shot Atmosphere</span>
                                <strong>${sb.mood || 'N/A'}</strong>
                            </div>
                        </div>
                    </div>
                    
                    <button class="presenter-nav-btn next" onclick="storyboardNextSlide()">
                        <i class="fa-solid fa-chevron-right"></i>
                    </button>
                </div>
                
                <div class="presenter-indicators-wrapper">
                    ${dotsHtml}
                </div>
            </div>
        `;
    }
}

function renderSoundDesign(soundDoc) {
    const container = document.getElementById("sound-container");
    if (!soundDoc || !soundDoc.background_music) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-volume-high" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Sound design plan will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    container.innerHTML = `
        <div class="info-card">
            <h3>Background Soundtrack / Music</h3>
            <div>${formatValue(soundDoc.background_music)}</div>
        </div>
        <div class="info-card">
            <h3>Ambient Environments</h3>
            <div>${formatValue(soundDoc.ambience)}</div>
        </div>
        <div class="info-card">
            <h3>Foley Sounds Checklist</h3>
            <div>${formatValue(soundDoc.foley_effects)}</div>
        </div>
        <div class="info-card">
            <h3>Vocal Dialogues Treatment</h3>
            <div>${formatValue(soundDoc.dialogue_treatment)}</div>
        </div>
        <div class="info-card" style="grid-column: 1 / -1;">
            <h3>Sound Cue Audio Notes</h3>
            <div style="white-space: pre-line;">${formatValue(soundDoc.scene_sound_notes)}</div>
        </div>
    `;
}

function renderProductionPlan(prodDoc) {
    const container = document.getElementById("production-container");
    if (!prodDoc || !prodDoc.shooting_locations) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-calendar-days" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Production plan will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    container.innerHTML = `
        <div class="info-card">
            <h3>Shooting Locations Map</h3>
            <div>${formatValue(prodDoc.shooting_locations)}</div>
        </div>
        <div class="info-card">
            <h3>Critical Props Checklist</h3>
            <div>${formatValue(prodDoc.required_props)}</div>
        </div>
        <div class="info-card">
            <h3>Camera & Lighting Gear</h3>
            <div>${formatValue(prodDoc.equipment)}</div>
        </div>
        <div class="info-card">
            <h3>Key Crew Roles Required</h3>
            <div>${formatValue(prodDoc.crew_suggestions)}</div>
        </div>
        <div class="info-card" style="grid-column: 1 / -1; border-color: var(--accent-gold);">
            <h3 style="color: var(--accent-gold); border-left-color: var(--accent-gold);">Estimated Shoot Days</h3>
            <div style="font-size: 1.2rem; font-weight: 700; color: #fff;">${formatValue(prodDoc.estimated_shoot_days)}</div>
        </div>
    `;
}

function renderBudgetPlan(budgetDoc) {
    const container = document.getElementById("budget-container");
    if (!budgetDoc || !budgetDoc.pre_production) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-calculator" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Budget plan will be displayed here once loaded.</p>
            </div>`;
        return;
    }
    
    const pre = budgetDoc.pre_production || {};
    const prod = budgetDoc.production || {};
    const post = budgetDoc.post_production || {};
    
    container.innerHTML = `
        <div class="info-card" style="border-left: 4px solid var(--accent-purple);">
            <h3 style="color: var(--accent-purple); border-left: none; padding-left: 0;"><i class="fa-solid fa-compass"></i> Pre-Production Phase</h3>
            <div style="font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 10px;">${pre.cost || "N/A"}</div>
            <p style="font-size: 0.9rem; color: var(--color-secondary); line-height: 1.5;">${pre.details || "N/A"}</p>
        </div>
        <div class="info-card" style="border-left: 4px solid var(--accent-gold-hover);">
            <h3 style="color: var(--accent-gold-hover); border-left: none; padding-left: 0;"><i class="fa-solid fa-video"></i> Filming / Production Phase</h3>
            <div style="font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 10px;">${prod.cost || "N/A"}</div>
            <p style="font-size: 0.9rem; color: var(--color-secondary); line-height: 1.5;">${prod.details || "N/A"}</p>
        </div>
        <div class="info-card" style="border-left: 4px solid #FFF3B0;">
            <h3 style="color: #FFF3B0; border-left: none; padding-left: 0;"><i class="fa-solid fa-scissors"></i> Post-Production Phase</h3>
            <div style="font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 10px;">${post.cost || "N/A"}</div>
            <p style="font-size: 0.9rem; color: var(--color-secondary); line-height: 1.5;">${post.details || "N/A"}</p>
        </div>
        <div class="info-card" style="grid-column: 1 / -1; border-color: var(--accent-gold); background: rgba(230, 161, 0, 0.05);">
            <h3 style="color: var(--accent-gold); border-left-color: var(--accent-gold);"><i class="fa-solid fa-vault"></i> Estimated Total Budget</h3>
            <p style="font-size: 1.8rem; font-weight: 800; color: #fff; margin: 10px 0;">${budgetDoc.total_budget || "N/A"}</p>
        </div>
        <div class="info-card" style="grid-column: 1 / -1; border-color: var(--accent-purple); background: rgba(212, 175, 55, 0.05);">
            <h3 style="color: var(--accent-purple); border-left-color: var(--accent-purple);"><i class="fa-solid fa-lightbulb"></i> Cost-Saving Strategies</h3>
            <p style="font-size: 0.95rem; color: var(--color-secondary); line-height: 1.6; white-space: pre-line;">${budgetDoc.cost_saving_tips || "N/A"}</p>
        </div>
    `;
}

function renderProjectsGrid(projects) {
    const container = document.getElementById("projects-list-container");
    if (!projects || projects.length === 0) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-folder-open" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>No projects created yet. Start by clicking "New Project".</p>
            </div>`;
        return;
    }
    
    container.innerHTML = "";
    projects.forEach(proj => {
        const card = document.createElement("div");
        card.className = "project-card";
        
        // Format date
        const dateStr = proj.created_at ? new Date(proj.created_at).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}) : "N/A";
        
        card.innerHTML = `
            <div>
                <h3>${proj.project_name}</h3>
                <span class="project-genre">${proj.genre}</span>
                <p class="project-desc">${proj.story_idea}</p>
            </div>
            <div class="project-actions">
                <span class="project-date">Created: ${dateStr}</span>
                <div class="flex gap-1" style="margin-top: 0.5rem;">
                    <button class="btn btn-sm btn-danger" onclick="deleteProjectConfirm('${proj.project_id}')"><i class="fa-solid fa-trash"></i></button>
                    <button class="btn btn-sm btn-gold" onclick="loadProjectIntoSession('${proj.project_id}')">Open Studio <i class="fa-solid fa-folder-open"></i></button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function filterProjects() {
    const query = document.getElementById("project-search-input").value.toLowerCase();
    const filtered = allProjects.filter(p => p.project_name.toLowerCase().includes(query) || p.genre.toLowerCase().includes(query));
    renderProjectsGrid(filtered);
}

// --- MODAL UTILITIES ---

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add("active");
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove("active");
    }
}

function toggleAuthModals(closeId, openId) {
    closeModal(closeId);
    // Tiny timeout for smooth transitions
    setTimeout(() => {
        openModal(openId);
    }, 150);
}

// --- TOAST NOTIFICATIONS ---

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    
    toast.className = `toast ${type}`;
    
    let iconClass = "fa-info-circle";
    if (type === "success") iconClass = "fa-check-circle";
    if (type === "error") iconClass = "fa-exclamation-circle";
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <div>${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Slide in
    setTimeout(() => {
        toast.classList.add("show");
    }, 50);
    
    // Auto dismiss after 4 seconds
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// --- HELPER SCROLLS ---

function scrollToFeatures() {
    document.getElementById("features-section").scrollIntoView({ behavior: "smooth" });
}

// --- CHATBOT WIDGET CONTROLLERS ---

function resetChatbot() {
    chatHistory = [];
    const messagesContainer = document.getElementById("chatbot-messages");
    if (messagesContainer) {
        messagesContainer.innerHTML = `
            <div class="chat-message system">
                <div class="message-content">
                    Hello! I am your CineForge pre-production copilot. You can ask me questions about your active project, request script changes, brainstorm character motivations, or ask for budget-saving advice!
                </div>
            </div>
        `;
    }
    const badge = document.getElementById("chat-badge");
    if (badge) {
        badge.style.display = "none";
        badge.innerText = "0";
    }
}

function toggleChatbot() {
    const chatWindow = document.getElementById("chatbot-window");
    if (!chatWindow) return;
    
    if (chatWindow.style.display === "none") {
        chatWindow.style.display = "flex";
        
        // Hide badge
        const badge = document.getElementById("chat-badge");
        if (badge) badge.style.display = "none";
        
        // Scroll to bottom
        const messagesContainer = document.getElementById("chatbot-messages");
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Focus input
        const chatInput = document.getElementById("chatbot-input");
        if (chatInput) chatInput.focus();
    } else {
        chatWindow.style.display = "none";
    }
}

function clearChat() {
    if (confirm("Are you sure you want to clear the conversation history?")) {
        resetChatbot();
    }
}

function handleChatKey(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const chatInput = document.getElementById("chatbot-input");
    const messagesContainer = document.getElementById("chatbot-messages");
    if (!chatInput || !messagesContainer) return;
    
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Clear input
    chatInput.value = "";
    
    if (!activeProject) {
        showToast("No active project loaded.", "error");
        return;
    }
    
    // Append user message
    appendChatMessage("user", text);
    
    // Disable inputs during send
    chatInput.disabled = true;
    const sendBtn = document.getElementById("chatbot-send-btn");
    if (sendBtn) sendBtn.disabled = true;
    
    // Show loader
    const loaderId = appendChatLoader();
    
    try {
        const response = await api.sendChatbotMessage(activeProject.project_id, text, chatHistory);
        
        removeChatLoader(loaderId);
        chatInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        chatInput.focus();
        
        if (response && response.success && response.data && response.data.response) {
            const reply = response.data.response;
            appendChatMessage("assistant", reply);
            
            // Save to history
            chatHistory.push({ role: "user", content: text });
            chatHistory.push({ role: "assistant", content: reply });
        } else {
            appendChatMessage("assistant", "I received an unexpected response from the studio. Please try again.");
        }
    } catch (err) {
        removeChatLoader(loaderId);
        chatInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        chatInput.focus();
        
        appendChatMessage("assistant", `Error: ${err.message || "Unable to reach CineForge Copilot."}`);
        showToast("Chat message failed: " + err.message, "error");
    }
}

function appendChatMessage(role, text) {
    const messagesContainer = document.getElementById("chatbot-messages");
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${role}`;
    
    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.innerHTML = formatChatMessage(text);
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendChatLoader() {
    const messagesContainer = document.getElementById("chatbot-messages");
    if (!messagesContainer) return null;
    
    const loaderId = "loader-" + Date.now();
    const loaderDiv = document.createElement("div");
    loaderDiv.className = "chat-loader";
    loaderDiv.id = loaderId;
    loaderDiv.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    
    messagesContainer.appendChild(loaderDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return loaderId;
}

function removeChatLoader(loaderId) {
    if (!loaderId) return;
    const loaderDiv = document.getElementById(loaderId);
    if (loaderDiv) {
        loaderDiv.remove();
    }
}

function formatChatMessage(text) {
    if (!text) return "";
    
    // Escape HTML first to prevent XSS
    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    
    // Convert triple backticks blocks ```code``` to pre tags
    html = html.replace(/```([\s\S]*?)```/g, function(match, code) {
        const trimmedCode = code.trim();
        return `<pre>${trimmedCode}</pre>`;
    });
    
    // Convert double asterisks **bold** to strong
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Convert single asterisks *italic* to em
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    
    // Convert inline code `code` to code tags
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");
    
    return html;
}
