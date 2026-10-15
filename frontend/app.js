const API_BASE_URL = "http://127.0.0.1:5000";

const icons = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  spark: '<path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z"/><path d="m19 14 1.1 2.9L23 18l-2.9 1.1L19 22l-1.1-2.9L15 18l2.9-1.1L19 14Z"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
  badge: '<circle cx="12" cy="8" r="6"/><path d="m8.2 13-1 8 4.8-2.7 4.8 2.7-1-8"/><path d="m10 8 1.3 1.3L14 6.5"/>',
  award: '<circle cx="12" cy="8" r="6"/><path d="m8.2 13-1 8 4.8-2.7 4.8 2.7-1-8"/>',
  light: '<path d="M9 18h6M10 22h4M8 14a7 7 0 1 1 8 0c-.8.6-1 1.1-1 2H9c0-.9-.2-1.4-1-2Z"/><path d="M12 3v1M4.9 5.9l.7.7M19.1 5.9l-.7.7"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  refresh: '<path d="M20 7v5h-5"/><path d="M4.9 9A7.5 7.5 0 0 1 18 6.2L20 8M4 17v-5h5"/><path d="M19.1 15A7.5 7.5 0 0 1 6 17.8L4 16"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  project: '<path d="M3 7h7l2 2h9v10H3z"/><path d="M3 7V5h7l2 2"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
  arrow: '<path d="M7 17 17 7M7 7h10v10"/>',
  arrowLeft: '<path d="m15 18-6-6 6-6M9 12h12"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>'
};

const state = {
  students: [],
  skills: [],
  currentPage: "dashboard",
  selectedStudent: null,
  loading: true,
  error: "",
  errorType: "",
  search: "",
  requestId: 0
};

const main = document.getElementById("main-content");
const searchInput = document.getElementById("global-search");

function icon(name, extraClass = "") {
  const body = icons[name] || icons.spark;
  return `<svg class="${extraClass}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
}

document.querySelectorAll("[data-icon]").forEach((element) => {
  element.innerHTML = icon(element.dataset.icon);
});

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character]);
}

function safeLink(value) {
  if (!value) return "";
  try {
    const url = new URL(value, window.location.href);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
}

async function apiGet(path) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json" }
    });
  } catch {
    throw new Error(`Could not reach the Campus Skill Hub API at ${API_BASE_URL}. Make sure the Flask server is running and try again.`);
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`The API returned an unreadable response (${response.status}).`);
  }

  if (!response.ok || payload.success === false) {
    throw new Error(payload.message || `The API request failed (${response.status}).`);
  }
  return payload;
}

async function loadDirectory() {
  state.loading = true;
  state.error = "";
  state.errorType = "";
  state.selectedStudent = null;
  render();

  try {
    const [studentResponse, skillResponse] = await Promise.all([
      apiGet("/api/students"),
      apiGet("/api/skills")
    ]);
    if (!Array.isArray(studentResponse.students) || !Array.isArray(skillResponse.skills)) {
      throw new Error("The API response did not include the expected student and skill lists.");
    }
    state.students = studentResponse.students;
    state.skills = skillResponse.skills;
    state.loading = false;
    updateStudentCount();
    routeFromHash();
  } catch (error) {
    state.loading = false;
    state.error = error.message || "Unable to load campus data.";
    state.errorType = "directory";
    render();
  }
}

function updateStudentCount() {
  document.getElementById("student-count").textContent = state.students.length || "";
}

function routeFromHash() {
  const route = window.location.hash.replace(/^#\/?/, "");
  const studentRoute = route.match(/^student\/(\d+)$/);
  if (studentRoute) {
    showStudent(Number(studentRoute[1]));
    return;
  }
  state.requestId += 1;
  const validPages = ["dashboard", "students", "skills", "projects", "certifications", "achievements"];
  state.currentPage = validPages.includes(route) ? route : "dashboard";
  state.selectedStudent = null;
  state.error = "";
  state.errorType = "";
  state.loading = false;
  updateNavigation();
  render();
  closeMobileNav();
}

async function showStudent(studentId) {
  state.currentPage = "students";
  state.selectedStudent = null;
  state.error = "";
  state.errorType = "";
  const requestId = ++state.requestId;
  updateNavigation();
  document.getElementById("page-breadcrumb").textContent = "Student profile";
  main.innerHTML = '<div class="initial-loading"><span class="spinner"></span><span>Loading student profile...</span></div>';
  closeMobileNav();

  try {
    const payload = await apiGet(`/api/students/${studentId}`);
    if (requestId !== state.requestId) return;
    if (!payload.student) throw new Error("The API response did not include the requested student.");
    state.selectedStudent = payload.student;
    state.error = "";
    state.errorType = "";
    render();
  } catch (error) {
    if (requestId !== state.requestId) return;
    state.error = error.message || "Unable to load this student profile.";
    state.errorType = "student";
    render();
  }
}

function updateNavigation() {
  document.querySelectorAll(".nav-link").forEach((link) => {
    const isActive = link.dataset.route === state.currentPage;
    link.classList.toggle("active", isActive);
    if (isActive) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  const labels = {
    dashboard: "Overview",
    students: state.selectedStudent ? "Student profile" : "Students",
    skills: "Skills",
    projects: "Projects",
    certifications: "Certifications",
    achievements: "Achievements"
  };
  document.getElementById("page-breadcrumb").textContent = labels[state.currentPage] || "Overview";
}

function initials(name) {
return String(name || "?")
.trim()
.split(/\s+/)
.slice(0, 2)
.map((part) => part[0] || "")
.join("")
.toUpperCase();
}


function avatar(student, sizeClass = "") {
  const colors = ["", "avatar-teal", "avatar-gold", "avatar-purple", "avatar-rose"];
  const color = colors[Math.abs(Number(student.id) || 0) % colors.length];
  const image = safeLink(student.profile_photo);
  const content = image
    ? `<img src="${escapeHtml(image)}" alt="">`
    : escapeHtml(initials(student.name));
  return `<span class="avatar ${color} ${sizeClass}" aria-hidden="true">${content}</span>`;
}

function formatDate(value) {
  if (!value) return "Date not provided";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Date not provided";
  return new Intl.DateTimeFormat(undefined, { month: "short", year: "numeric" }).format(parsed);
}

function fullDate(value) {
  if (!value) return "Date not provided";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Date not provided";
  return new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric" }).format(parsed);
}

function studentPath(studentId) {
window.location.hash = `student/${studentId}`;
}

function filteredStudents() {
  const term = state.search.trim().toLowerCase();

  if (!term) return state.students;

  return state.students.filter((student) => [
    student.name,
    student.email,
    student.department,
    student.year,
    ...(student.skills || []).map((skill) =>
      typeof skill === "string" ? skill : skill.name
    ),
    ...(student.projects || []).flatMap((project) => [
      project.title,
      project.description,
      project.tech_stack
    ])
  ].some((value) =>
    String(value ?? "").toLowerCase().includes(term)
  ));
}


function pageHeading(eyebrow, title, description, extra = "") {
  return `<div class="page-heading"><div><div class="eyebrow">${escapeHtml(eyebrow)}</div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(description)}</p></div>${extra}</div>`;
}

function emptyState(title, description, iconName = "spark") {
  return `<div class="empty-state"><span class="empty-icon">${icon(iconName)}</span><strong>${escapeHtml(title)}</strong><p>${escapeHtml(description)}</p></div>`;
}

function errorState(message) {
  return `<div class="error-state"><span class="empty-icon">${icon("refresh")}</span><strong>We couldn't load this view</strong><p>${escapeHtml(message)}<br>Check that the Flask API is available, then try again.</p><button class="retry-button" type="button" data-action="retry">Try again</button></div>`;
}

function studentRow(student) {
  const skills = Array.isArray(student.skills) ? student.skills.length : 0;
  return `<div class="student-row" data-student="${escapeHtml(student.id)}" role="link" tabindex="0" aria-label="View ${escapeHtml(student.name)}'s profile">
    ${avatar(student)}
    <div class="student-main"><div class="student-name">${escapeHtml(student.name || "Unnamed student")}</div><div class="student-meta">${escapeHtml(student.department || "Department not provided")} · Year ${escapeHtml(student.year ?? "—")}</div></div>
    <div class="student-side">${skills} ${skills === 1 ? "skill" : "skills"}</div>${icon("chevron")}
  </div>`;
}

function dashboard() {
  const students = filteredStudents();
  const allProjects = state.students.flatMap((student) => (student.projects || []).map((project) => ({ ...project, student })));
  const allCertifications = state.students.flatMap((student) => student.certifications || []);
  const allAchievements = state.students.flatMap((student) => student.achievements || []);
  const skillUsage = getSkillUsage();
  const featuredSkills = skillUsage.slice(0, 5);
  const studentTotal = state.students.length;
  const dateLabel = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" }).format(new Date());

  return `<section class="welcome-panel" aria-labelledby="dashboard-title">
      <div class="welcome-copy">
        <div class="eyebrow">CAMPUS SNAPSHOT</div>
        <h1 id="dashboard-title">Good ${greeting()}, campus.</h1>
        <p>A clear view of the people, skills, and work shaping your community.</p>
        <a class="welcome-action" href="#students">Explore the directory ${icon("arrow")}</a>
      </div>
      <div class="welcome-aside">
        <span class="welcome-icon">${icon("users")}</span>
        <span class="welcome-label">Student directory</span>
        <strong>${studentTotal}</strong>
        <span class="welcome-caption">${studentTotal === 1 ? "student profile" : "student profiles"}</span>
      </div>
      <div class="welcome-date">${escapeHtml(dateLabel)}</div>
    </section>
    <section class="metric-grid" aria-label="Campus statistics">
      ${metricCard("Students", studentTotal, "In the campus directory", "users", "")}
      ${metricCard("Skills", state.skills.length, "Distinct skills represented", "spark", "green")}
      ${metricCard("Projects", allProjects.length, "Ideas brought to life", "project", "gold")}
      ${metricCard("Achievements", allCertifications.length + allAchievements.length, "Certifications & milestones", "award", "")}
    </section>
    <section class="content-grid">
      <div class="panel">
        <div class="panel-header"><div><h2 class="panel-title">Student community</h2><p class="panel-subtitle">Recently added to the directory</p></div><a class="text-link" href="#students">View all students ${icon("chevron")}</a></div>
        <div class="student-list">${students.length ? students.slice(0, 5).map(studentRow).join("") : emptyState("No matching students", "Try another search, or check back when students are added.", "users")}</div>
      </div>
      <div class="panel">
        <div class="panel-header"><div><h2 class="panel-title">Popular skills</h2><p class="panel-subtitle">Most represented in the community</p></div><a class="text-link" href="#skills">Explore skills ${icon("chevron")}</a></div>
        <div class="skill-overview">${featuredSkills.length ? featuredSkills.map((item) => `<div class="skill-line"><span class="skill-name">${escapeHtml(item.name)}</span><span class="skill-track"><span class="skill-fill" style="width:${Math.max(8, Math.round(item.count / Math.max(1, studentTotal) * 100))}%"></span></span><span class="skill-number">${item.count}</span></div>`).join("") : emptyState("No skills yet", "Student skills will appear here once they are added.", "spark")}
          ${featuredSkills.length ? `<div class="quick-stats"><div class="quick-stat"><strong>${allProjects.length}</strong><span>Projects</span></div><div class="quick-stat"><strong>${allCertifications.length}</strong><span>Certifications</span></div><div class="quick-stat"><strong>${allAchievements.length}</strong><span>Achievements</span></div></div>` : ""}
        </div>
      </div>
    </section>`;
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

function metricCard(label, value, caption, iconName, color) {
  return `<article class="metric-card"><div class="metric-top"><span>${escapeHtml(label)}</span><span class="metric-icon ${color}">${icon(iconName)}</span></div><div class="metric-value">${Number(value) || 0}</div><div class="metric-caption">${escapeHtml(caption)}</div></article>`;
}

function studentsPage() {
  const students = filteredStudents();
  const rows = students.map((student) => `<article class="directory-row" data-student="${escapeHtml(student.id)}" role="link" tabindex="0" aria-label="View ${escapeHtml(student.name)}'s profile">
    <div class="directory-student">${avatar(student)}<div class="directory-student-copy"><strong>${escapeHtml(student.name || "Unnamed student")}</strong><span>${escapeHtml(student.email || "Email not provided")}</span></div></div>
    <div class="directory-department"><span class="directory-mobile-label">Department</span><span>${escapeHtml(student.department || "Department not provided")}</span></div>
    <div class="directory-year"><span class="directory-mobile-label">Year</span><span class="tag">${escapeHtml(student.year ? `Year ${student.year}` : "Student")}</span></div>
    <div class="directory-skills"><span class="directory-mobile-label">Skills</span><span class="directory-skill-count">${(student.skills || []).length} ${(student.skills || []).length === 1 ? "skill" : "skills"}</span></div>
    <span class="directory-arrow">${icon("chevron")}</span>
  </article>`).join("");

  return `${pageHeading("CAMPUS DIRECTORY", "Students", "Meet the people behind the skills, projects, and accomplishments.")}<div class="section-toolbar"><span class="result-count">${students.length} ${students.length === 1 ? "student" : "students"}${state.search ? ` matching ?${escapeHtml(state.search)}?` : " in the directory"}</span></div>${rows ? `<section class="directory-table" aria-label="Students"><div class="directory-table-head"><span>Student</span><span>Department</span><span>Year</span><span>Skills</span><span></span></div><div class="directory-list">${rows}</div></section>` : emptyState("No students found", state.search ? "Try a different search term." : "The student directory is empty. Student records will appear here when available.", "users")}`;
}

function getSkillUsage() {
  const byName = new Map();
  for (const skill of state.skills) {
    byName.set(String(skill.name).toLowerCase(), { id: skill.id, name: skill.name, students: [] });
  }
  for (const student of state.students) {
    for (const skill of student.skills || []) {
      const key = String(skill.name || "").toLowerCase();
      if (!byName.has(key)) byName.set(key, { id: skill.id, name: skill.name || "Unnamed skill", students: [] });
      byName.get(key).students.push({ ...student, proficiency: skill.proficiency });
    }
  }
  return [...byName.values()].map((skill) => ({ ...skill, count: skill.students.length }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

function skillsPage() {
  const term = state.search.trim().toLowerCase();
  const skills = getSkillUsage().filter((skill) => {
    if (!term) return true;
    return String(skill.name).toLowerCase().includes(term) || skill.students.some((student) => String(student.name || "").toLowerCase().includes(term));
  });
  const cards = skills.map((skill) => `<article class="skill-card">
    <div class="skill-card-head"><span class="skill-card-icon">${icon("spark")}</span><span class="skill-card-name">${escapeHtml(skill.name)}</span><span class="skill-card-count">${skill.count} ${skill.count === 1 ? "student" : "students"}</span></div>
    ${skill.students.length ? `<div class="skill-members">${skill.students.map((student) => `<button class="member-pill" type="button" data-student="${escapeHtml(student.id)}" title="${escapeHtml(student.proficiency || "Proficiency not specified")}">${escapeHtml(student.name)} · ${escapeHtml(student.proficiency || "Unspecified")}</button>`).join("")}</div>` : `<div class="skill-members"><span class="member-pill">No student proficiency recorded</span></div>`}
  </article>`).join("");
  return `${pageHeading("CAPABILITIES", "Skills", "Explore the strengths represented across your student community.")}<div class="section-toolbar"><span class="result-count">${skills.length} ${skills.length === 1 ? "skill" : "skills"}${state.search ? ` matching “${escapeHtml(state.search)}”` : " in the directory"}</span></div>${cards ? `<section class="skills-grid" aria-label="Campus skills">${cards}</section>` : emptyState("No skills found", state.search ? "Try a different search term." : "Skills will appear here once they are added to the directory.", "spark")}`;
}

function collectRecords(type) {
  const fields = {
    projects: { key: "projects", title: "title", detail: "description", date: "created_at", subtitle: "tech_stack", icon: "project" },
    certifications: { key: "certifications", title: "name", detail: "issuing_organization", date: "issue_date", subtitle: "credential_url", icon: "badge" },
    achievements: { key: "achievements", title: "title", detail: "description", date: "date", subtitle: "", icon: "award" }
  }[type];
  return state.students.flatMap((student) => (student[fields.key] || []).map((record) => ({ ...record, student })));
}

function recordCard(record, type) {
  const fields = {
    projects: { title: record.title, byline: record.student.name, detail: record.description, meta: record.tech_stack, date: record.created_at, icon: "project" },
    certifications: { title: record.name, byline: record.issuing_organization, detail: "", meta: "", date: record.issue_date, icon: "badge" },
    achievements: { title: record.title, byline: record.student.name, detail: record.description, meta: "", date: record.date, icon: "award" }
  }[type];
  const searchable = `${fields.title || ""} ${fields.byline || ""} ${fields.detail || ""} ${fields.meta || ""} ${record.student.name || ""}`.toLowerCase();
  if (state.search.trim() && !searchable.includes(state.search.trim().toLowerCase())) return "";
  const link = type === "projects" ? safeLink(record.project_url) : type === "certifications" ? safeLink(record.credential_url) : "";
  const title = escapeHtml(fields.title || "Untitled");
  const titleContent = link ? `<a class="record-title" href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">${title} ${icon("arrow")}</a>` : `<h2 class="record-title">${title}</h2>`;
  const detail = fields.detail ? `<p class="record-description">${escapeHtml(fields.detail)}</p>` : "";
  const meta = fields.meta
    ? type === "certifications" ? `<span class="tag teal">${escapeHtml(fields.meta)}</span>` : `<span class="tag">${escapeHtml(fields.meta)}</span>`
    : "";
  const byline = type === "certifications" ? `<div class="record-byline">${escapeHtml(fields.byline || "Issuing organization not provided")}</div>` : "";
  return `<article class="record-card">
    <div class="record-head"><span class="record-icon ${type === "certifications" ? "teal" : type === "achievements" ? "gold" : ""}">${icon(fields.icon)}</span><div class="record-copy">${titleContent}${byline}</div></div>
    ${detail}
    ${meta ? `<div>${meta}</div>` : ""}
    <div class="record-footer"><button class="record-student" type="button" data-student="${escapeHtml(record.student.id)}">${avatar(record.student)}${escapeHtml(record.student.name || "Student")}</button><span>${escapeHtml(formatDate(fields.date))}</span></div>
  </article>`;
}

function recordsPage(type) {
  const config = {
    projects: { eyebrow: "STUDENT WORK", title: "Projects", description: "Ideas, experiments, and solutions created by students.", empty: "No projects yet", emptyText: "Student projects will show up here when available.", icon: "project" },
    certifications: { eyebrow: "CREDENTIALS", title: "Certifications", description: "Credentials earned through learning and professional development.", empty: "No certifications yet", emptyText: "Student certifications will show up here when available.", icon: "badge" },
    achievements: { eyebrow: "MILESTONES", title: "Achievements", description: "The competitions, contributions, and milestones worth celebrating.", empty: "No achievements yet", emptyText: "Student achievements will show up here when available.", icon: "award" }
  }[type];
  const all = collectRecords(type);
  const cards = all.map((record) => recordCard(record, type)).filter(Boolean).join("");
  const visibleCount = (state.search ? all.filter((record) => {
    const values = [record.title, record.name, record.description, record.issuing_organization, record.tech_stack, record.student.name];
    return values.some((value) => String(value || "").toLowerCase().includes(state.search.trim().toLowerCase()));
  }).length : all.length);
  return `${pageHeading(config.eyebrow, config.title, config.description)}<div class="section-toolbar"><span class="result-count">${visibleCount} ${visibleCount === 1 ? "record" : "records"}${state.search ? ` matching “${escapeHtml(state.search)}”` : " across all students"}</span></div>${cards ? `<section class="record-grid" aria-label="${config.title}">${cards}</section>` : emptyState(state.search ? `No matching ${type}` : config.empty, state.search ? "Try a different search term." : config.emptyText, config.icon)}`;
}

function studentProfile(student) {
  const skills = student.skills || [];
  const projects = student.projects || [];
  const certifications = student.certifications || [];
  const achievements = student.achievements || [];
  const profileStats = [
    ["Skills", skills.length],
    ["Projects", projects.length],
    ["Certifications", certifications.length],
    ["Achievements", achievements.length]
  ].map(([label, value]) => `<div class="profile-stat"><strong>${value}</strong><span>${label}</span></div>`).join("");

  const skillSection = profileSection("Skills & proficiency", skills.length,
    skills.length ? skills.map((skill) => `<div class="profile-skill"><span class="skill-card-icon">${icon("spark")}</span><span class="profile-skill-name">${escapeHtml(skill.name || "Unnamed skill")}</span><span class="tag teal">${escapeHtml(skill.proficiency || "Unspecified")}</span></div>`).join("") : `<p class="panel-subtitle">No skills have been added yet.</p>`);
  const projectSection = profileSection("Projects", projects.length,
    projects.length ? projects.map((project) => {
      const link = safeLink(project.project_url);
      return `<div class="mini-record"><span class="mini-record-icon">${icon("project")}</span><div class="mini-record-body">${link ? `<a class="mini-record-title" href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(project.title || "Untitled project")}</a>` : `<div class="mini-record-title">${escapeHtml(project.title || "Untitled project")}</div>`}<div class="mini-record-meta">${escapeHtml(project.tech_stack || project.description || "Project details not provided")}</div></div></div>`;
    }).join("") : `<p class="panel-subtitle">No projects have been added yet.</p>`);
  const certificationSection = profileSection("Certifications", certifications.length,
    certifications.length ? certifications.map((item) => {
      const link = safeLink(item.credential_url);
      const name = escapeHtml(item.name || "Untitled certification");
      return `<div class="mini-record"><span class="mini-record-icon">${icon("badge")}</span><div class="mini-record-body">${link ? `<a class="mini-record-title" href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">${name}</a>` : `<div class="mini-record-title">${name}</div>`}<div class="mini-record-meta">${escapeHtml(item.issuing_organization || "Organization not provided")} · ${escapeHtml(formatDate(item.issue_date))}</div></div></div>`;
    }).join("") : `<p class="panel-subtitle">No certifications have been added yet.</p>`);
  const achievementSection = profileSection("Achievements", achievements.length,
    achievements.length ? achievements.map((item) => `<div class="mini-record"><span class="mini-record-icon">${icon("award")}</span><div class="mini-record-body"><div class="mini-record-title">${escapeHtml(item.title || "Untitled achievement")}</div><div class="mini-record-meta">${escapeHtml(item.description || "Achievement")} · ${escapeHtml(formatDate(item.date))}</div></div></div>`).join("") : `<p class="panel-subtitle">No achievements have been added yet.</p>`);
  const bio = student.bio ? `<p class="profile-bio">${escapeHtml(student.bio)}</p>` : "";
  const phone = student.phone ? `<span class="tag muted">${escapeHtml(student.phone)}</span>` : "";

  return `<button class="profile-back" type="button" data-route="students">${icon("arrowLeft")} Back to students</button>
    <section class="profile-hero">${avatar(student)}<div class="profile-info"><h1>${escapeHtml(student.name || "Unnamed student")}</h1><div class="profile-email">${icon("mail")} ${escapeHtml(student.email || "Email not provided")}</div><div class="profile-badges"><span class="tag">${escapeHtml(student.department || "Department not provided")}</span><span class="tag gold">${escapeHtml(student.year ? `Year ${student.year}` : "Year not provided")}</span>${phone}</div></div>${bio}</section>
    <section class="profile-stats" aria-label="Student profile summary">${profileStats}</section>
    <section class="profile-section-grid" aria-label="Student details">${skillSection}${projectSection}${certificationSection}${achievementSection}</section>`;
}

function profileSection(title, count, content) {
  return `<article class="profile-section"><div class="profile-section-head"><h2>${escapeHtml(title)}</h2><span>${count} ${count === 1 ? "item" : "items"}</span></div>${content}</article>`;
}

function render() {
  if (state.loading) {
    main.innerHTML = '<div class="initial-loading"><span class="spinner"></span><span>Connecting to campus directory...</span></div>';
    return;
  }
  if (state.error) {
    main.innerHTML = errorState(state.error);
    return;
  }
  if (state.currentPage === "students" && state.selectedStudent) {
    main.innerHTML = studentProfile(state.selectedStudent);
  } else {
    const pages = {
      dashboard,
      students: studentsPage,
      skills: skillsPage,
      projects: () => recordsPage("projects"),
      certifications: () => recordsPage("certifications"),
      achievements: () => recordsPage("achievements")
    };
    main.innerHTML = (pages[state.currentPage] || dashboard)();
  }
  updateNavigation();
}

function closeMobileNav() {
  document.getElementById("sidebar").classList.remove("open");
  document.querySelector(".backdrop")?.classList.remove("visible");
  document.getElementById("menu-toggle").setAttribute("aria-expanded", "false");
}

document.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  if (!target) return;

  const studentElement = target.closest("[data-student]");
  if (studentElement && !target.closest("a")) {
    studentPath(Number(studentElement.dataset.student));
    return;
  }
  const routeElement = target.closest("[data-route]");
  if (routeElement) {
    const route = routeElement.dataset.route;
    if (route === "students" && state.selectedStudent) {
      window.location.hash = "students";
    } else {
      window.location.hash = route;
    }
    return;
  }
  if (target.closest('[data-action="retry"]')) {
    if (state.errorType === "directory") loadDirectory();
    else routeFromHash();
    return;
  }
  if (target.closest("#refresh-button")) {
    const currentHash = window.location.hash;
    loadDirectory().then(() => {
      if (currentHash.startsWith("#student/")) routeFromHash();
    });
    return;
  }
  if (target.closest("#menu-toggle")) {
    const open = document.getElementById("sidebar").classList.toggle("open");
    document.querySelector(".backdrop").classList.toggle("visible", open);
    document.getElementById("menu-toggle").setAttribute("aria-expanded", String(open));
    return;
  }
  if (target.closest(".backdrop")) closeMobileNav();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMobileNav();
  const target = event.target instanceof Element ? event.target : null;
  if (target?.matches('[data-student][role="link"]') && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    studentPath(Number(target.dataset.student));
  }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    searchInput.focus();
  }
});

searchInput.addEventListener("input", () => {
  state.search = searchInput.value;
  if (!state.loading && !state.error && !state.selectedStudent) render();
});

window.addEventListener("hashchange", routeFromHash);

const backdrop = document.createElement("div");
backdrop.className = "backdrop";
backdrop.setAttribute("aria-hidden", "true");
document.body.append(backdrop);

loadDirectory();