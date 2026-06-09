// CineForge AI Single Page Application Main Logic Controller

// --- STATE MANAGEMENT ---
let currentUser = null;
let activeProject = null;
let allProjects = [];

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    checkAuthenticationState();
    
    // Automatically bind escape key to close modals
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const openModal = document.querySelector(".modal.active");
            if (openModal) closeModal(openModal.id);
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
    const restrictedViews = ["story", "screenplay", "characters", "scenes", "storyboard", "sound", "production", "export"];
    
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
        "export": "Export Center",
        "projects": "My Projects Directory"
    };
    document.getElementById("current-subview-title").innerText = headerTitleMap[subviewId] || "Studio";

    // Auto load view specifics if project loaded
    if (activeProject) {
        loadViewSpecificData(subviewId);
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
        closeModal("login-modal");
        onUserAuthenticated();
        showToast("Logged in with Google!", "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function handleLogout() {
    await authLogout();
    showLandingPage();
    showToast("Logged out successfully.", "info");
}

async function handleCreateProject(e) {
    e.preventDefault();
    const project_name = document.getElementById("proj-name").value;
    const genre = document.getElementById("proj-genre").value;
    const target_audience = document.getElementById("proj-audience").value;
    const story_idea = document.getElementById("proj-idea").value;

    const payload = { project_name, genre, target_audience, story_idea };

    try {
        const response = await api.createProject(payload);
        const newProj = response.data;
        closeModal("create-project-modal");
        
        // Reset Form
        document.getElementById("create-project-form").reset();
        
        // Set Active Project
        loadProjectIntoSession(newProj.project_id);
        
        showToast("New project initialized!", "success");
    } catch (err) {
        showToast("Failed to initialize project: " + err.message, "error");
    }
}

// --- PROJECT LOADING AND WORKSPACE MANAGEMENT ---

async function loadProjectIntoSession(projectId, redirect = true) {
    try {
        const response = await api.getProject(projectId);
        const compiled = response.data;
        
        activeProject = compiled.project;
        localStorage.setItem("cineforge_active_project_id", projectId);
        
        updateActiveProjectBar(activeProject);
        toggleRestrictedSidebarLinks(true);
        
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
        renderScreenplay(response.data);
        showToast("Screenplay generated using IBM Granite!", "success");
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
        renderProductionPlan(response.data);
        showToast("Production logistics planned!", "success");
    } catch (err) {
        showToast("Production plan failed: " + err.message, "error");
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
        // Fetch fresh project details containing all generated objects
        const response = await api.getProject(activeProject.project_id);
        const compiled = response.data;
        
        switch (viewId) {
            case "dashboard":
                renderProjectDashboardSummary(compiled);
                break;
            case "story":
                renderStoryAnalysis(compiled.story_analysis);
                renderNarrativeStructure(compiled.narrative_structure);
                break;
            case "screenplay":
                renderScreenplay(compiled.screenplay);
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
        }
    } catch (err) {
        console.error(`Error loading data for ${viewId}:`, err);
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
                <p>Click Generate to analyze your story idea.</p>
            </div>`;
        return;
    }
    
    container.className = ""; // Remove centering wrapper class if needed
    container.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div><strong>Logline:</strong> <p>${analysis.logline}</p></div>
            <div><strong>Tagline:</strong> <p style="font-style: italic; color: var(--accent-gold);">"${analysis.tagline}"</p></div>
            <div><strong>Synopsis:</strong> <p style="font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap;">${analysis.synopsis}</p></div>
            <div><strong>Genre Analysis:</strong> <p style="font-size: 0.9rem;">${analysis.genre_analysis}</p></div>
            <div><strong>Theme:</strong> <p style="font-size: 0.9rem;">${analysis.theme}</p></div>
            <div><strong>Audience Insights:</strong> <p style="font-size: 0.9rem;">${analysis.audience_insights}</p></div>
        </div>
    `;
}

function renderNarrativeStructure(structure) {
    const container = document.getElementById("output-story-structure");
    if (!structure || !structure.act_1) {
        container.innerHTML = `
            <div class="screenplay-empty">
                <i class="fa-solid fa-shapes" style="font-size: 2.5rem; margin-bottom: 10px; color: var(--color-muted);"></i>
                <p>Click Generate to create Act breakdowns.</p>
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

function renderScreenplay(screenplay) {
    const paper = document.getElementById("screenplay-paper");
    if (!screenplay || !screenplay.screenplay_text) {
        paper.innerHTML = `
            <div class="screenplay-empty">
                <i class="fa-solid fa-scroll" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>No script generated yet. Click "Generate Script" to formulate screenplay using IBM Granite AI.</p>
            </div>`;
        return;
    }
    
    // Parse plaintext into nicely aligned standard margins
    const lines = screenplay.screenplay_text.split("\n");
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
        else if (stripped === stripped.toUpperCase() && stripped.length < 25 && !stripped.includes("FADE IN") && !stripped.includes("FADE OUT")) {
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

function renderCharacters(charDoc) {
    const container = document.getElementById("characters-container");
    if (!charDoc || !charDoc.characters || charDoc.characters.length === 0) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-users" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Click Generate to design characters for this project.</p>
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

function renderScenes(sceneDoc) {
    const container = document.getElementById("scenes-container");
    if (!sceneDoc || !sceneDoc.scenes || sceneDoc.scenes.length === 0) {
        container.innerHTML = `
            <div class="info-card text-center" style="padding: 4rem;">
                <i class="fa-solid fa-list-check" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Click Breakdown Scenes to dissect the story idea.</p>
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
                <td style="font-family: var(--font-script); color: var(--accent-gold); font-size: 0.85rem;">${scene.location}</td>
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

function renderStoryboard(sbDoc) {
    const container = document.getElementById("storyboard-container");
    if (!sbDoc || !sbDoc.storyboards || sbDoc.storyboards.length === 0) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-images" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Click Generate to compile scene prompt boards.</p>
            </div>`;
        return;
    }
    
    container.innerHTML = "";
    sbDoc.storyboards.forEach(sb => {
        const card = document.createElement("div");
        card.className = "storyboard-card";
        
        // Truncate prompt for image generator
        const safePrompt = (sb.prompt || "").replace(/["']/g, "").substring(0, 150).trim();
        const primaryImageUrl = `https://image.pollinations.ai/p/${encodeURIComponent(safePrompt)}?width=600&height=400&nologo=true`;

        // Collection of premium movie-themed Unsplash images for instant fallback
        const fallbackStockImages = [
            "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80", // Film slate / Director set
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80", // Moody office / Detective light
            "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&q=80", // Film reel glowing
            "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?auto=format&fit=crop&w=600&q=80", // Dramatic silhouette / Noir
            "https://images.unsplash.com/photo-1505686994434-e3cc5abf1330?auto=format&fit=crop&w=600&q=80", // Camera lens / Cinema projector
            "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=600&q=80"  // Vintage theater hall
        ];
        const backupUrl = fallbackStockImages[(sb.scene_number - 1) % fallbackStockImages.length];

        card.innerHTML = `
            <div class="storyboard-frame" style="height: 200px; position: relative; background: #08080c; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                <!-- Spinning film reel while image is generating -->
                <div class="film-reel-loader" style="position: absolute; transform: scale(0.6);"></div>
                <img src="${primaryImageUrl}" 
                     alt="Storyboard Scene #${sb.scene_number}" 
                     style="width: 100%; height: 100%; object-fit: cover; z-index: 1; opacity: 0; transition: opacity 0.5s;"
                     onload="this.style.opacity='1'; this.previousElementSibling.remove();"
                     onerror="this.onerror=null; this.src='${backupUrl}'; this.previousElementSibling.remove(); this.style.opacity='1';">
            </div>
            <div class="storyboard-info">
                <div class="storyboard-scene-num">Scene #${sb.scene_number}</div>
                <div class="storyboard-prompt">"${sb.prompt}"</div>
                <div class="storyboard-meta-tag">
                    <span>Angle: <strong>${sb.camera_angle}</strong></span>
                </div>
                <div class="storyboard-meta-tag" style="border-top: none; padding-top: 0;">
                    <span>Lighting: <strong>${sb.lighting}</strong></span>
                </div>
                <div class="storyboard-meta-tag" style="border-top: none; padding-top: 0;">
                    <span>Mood: <strong>${sb.mood}</strong></span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderSoundDesign(soundDoc) {
    const container = document.getElementById("sound-container");
    if (!soundDoc || !soundDoc.background_music) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-volume-high" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Click Generate to orchestrate audio design using IBM Granite AI.</p>
            </div>`;
        return;
    }
    
    container.innerHTML = `
        <div class="info-card">
            <h3>Background Soundtrack / Music</h3>
            <p>${soundDoc.background_music}</p>
        </div>
        <div class="info-card">
            <h3>Ambient Environments</h3>
            <p>${soundDoc.ambience}</p>
        </div>
        <div class="info-card">
            <h3>Foley Sounds Checklist</h3>
            <p>${soundDoc.foley_effects}</p>
        </div>
        <div class="info-card">
            <h3>Vocal Dialogues Treatment</h3>
            <p>${soundDoc.dialogue_treatment}</p>
        </div>
        <div class="info-card" style="grid-column: 1 / -1;">
            <h3>Sound Cue Audio Notes</h3>
            <p style="white-space: pre-line;">${soundDoc.scene_sound_notes}</p>
        </div>
    `;
}

function renderProductionPlan(prodDoc) {
    const container = document.getElementById("production-container");
    if (!prodDoc || !prodDoc.shooting_locations) {
        container.innerHTML = `
            <div class="info-card text-center" style="grid-column: 1 / -1; padding: 4rem;">
                <i class="fa-solid fa-calendar-days" style="font-size: 3rem; margin-bottom: 15px; color: var(--color-muted);"></i>
                <p>Click Generate to compile physical logistics plan using IBM Granite AI.</p>
            </div>`;
        return;
    }
    
    container.innerHTML = `
        <div class="info-card">
            <h3>Shooting Locations Map</h3>
            <p>${prodDoc.shooting_locations}</p>
        </div>
        <div class="info-card">
            <h3>Critical Props Checklist</h3>
            <p>${prodDoc.required_props}</p>
        </div>
        <div class="info-card">
            <h3>Camera & Lighting Gear</h3>
            <p>${prodDoc.equipment}</p>
        </div>
        <div class="info-card">
            <h3>Key Crew Roles Required</h3>
            <p>${prodDoc.crew_suggestions}</p>
        </div>
        <div class="info-card" style="grid-column: 1 / -1; border-color: var(--accent-gold);">
            <h3 style="color: var(--accent-gold); border-left-color: var(--accent-gold);">Estimated Shoot Days</h3>
            <p style="font-size: 1.2rem; font-weight: 700; color: #fff;">${prodDoc.estimated_shoot_days}</p>
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
