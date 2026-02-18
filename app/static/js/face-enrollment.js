/**
 * Face Enrollment JavaScript
 * Handles photo upload, preview, enrollment submission, and people management
 */

// ── State ────────────────────────────────────────────────────
let selectedFiles = [];
let peopleData = [];
let deleteTargetId = null;

// ── Initialization ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupDropZone();
    setupImageInput();
    setupEnrollButton();
    setupSearch();
    setupFilterRelation();
    loadPeople();
    loadFaceStats();
});

// ── Drag & Drop ──────────────────────────────────────────────
function setupDropZone() {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;

    ['dragenter', 'dragover'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer.files).filter(f => 
            f.type.startsWith('image/')
        );
        addFiles(files);
    });
}

// ── File Input ───────────────────────────────────────────────
function setupImageInput() {
    const input = document.getElementById('imageInput');
    if (!input) return;

    input.addEventListener('change', () => {
        const files = Array.from(input.files);
        addFiles(files);
        input.value = ''; // Reset for re-selection
    });
}

function addFiles(files) {
    selectedFiles = [...selectedFiles, ...files];
    renderPreviews();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderPreviews();
}

function renderPreviews() {
    const grid = document.getElementById('previewGrid');
    if (!grid) return;

    grid.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const item = document.createElement('div');
            item.className = 'preview-item';
            item.innerHTML = `
                <img src="${e.target.result}" alt="Preview ${index + 1}">
                <button class="remove-btn" onclick="removeFile(${index})" title="Remove">
                    <i class="bi bi-x"></i>
                </button>
            `;
            grid.appendChild(item);
        };
        reader.readAsDataURL(file);
    });
}

// ── Enrollment Submission ────────────────────────────────────
function setupEnrollButton() {
    const btn = document.getElementById('submitEnroll');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        const name = document.getElementById('personName').value.trim();
        const relation = document.getElementById('relation').value;
        const isResident = document.getElementById('isResident').checked;

        // Validation
        if (!name) {
            showEnrollResult('error', 'Please enter a name.');
            return;
        }

        if (selectedFiles.length < 2) {
            showEnrollResult('error', 'Please upload at least 2 photos with clear face visibility.');
            return;
        }

        // Build form data
        const formData = new FormData();
        formData.append('person_name', name);
        formData.append('relation', relation);
        formData.append('is_resident', isResident.toString());
        
        selectedFiles.forEach(file => {
            formData.append('images', file);
        });

        // Show progress
        const progress = document.getElementById('enrollmentProgress');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const submitBtn = document.getElementById('submitEnroll');

        progress.style.display = 'block';
        submitBtn.disabled = true;
        progressText.textContent = 'Uploading photos...';
        progressBar.style.width = '25%';

        try {
            progressText.textContent = 'Processing face encodings...';
            progressBar.style.width = '50%';

            const response = await fetch('/face/enroll', {
                method: 'POST',
                body: formData
            });

            progressBar.style.width = '75%';
            const data = await response.json();

            progressBar.style.width = '100%';

            if (data.success) {
                progressText.textContent = 'Syncing to cloud...';
                
                setTimeout(() => {
                    showEnrollResult('success', data.message);
                    progress.style.display = 'none';
                    
                    // Reset form
                    document.getElementById('enrollForm').reset();
                    selectedFiles = [];
                    renderPreviews();
                    
                    // Reload people
                    loadPeople();
                    loadFaceStats();
                    
                    // Close modal after brief delay
                    setTimeout(() => {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('enrollModal'));
                        if (modal) modal.hide();
                        hideEnrollResult();
                    }, 2000);
                }, 500);
            } else {
                showEnrollResult('error', data.message || 'Enrollment failed');
                progress.style.display = 'none';
            }
        } catch (error) {
            showEnrollResult('error', `Network error: ${error.message}`);
            progress.style.display = 'none';
        } finally {
            submitBtn.disabled = false;
        }
    });
}

function showEnrollResult(type, message) {
    const result = document.getElementById('enrollResult');
    if (!result) return;

    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle';

    result.style.display = 'block';
    result.innerHTML = `
        <div class="alert ${alertClass} mb-0" style="border-radius: 12px;">
            <i class="bi ${icon}"></i> ${message}
        </div>
    `;
}

function hideEnrollResult() {
    const result = document.getElementById('enrollResult');
    if (result) result.style.display = 'none';
}

// ── Load People ──────────────────────────────────────────────
async function loadPeople() {
    try {
        const response = await fetch('/face/enrolled');
        const data = await response.json();

        if (data.success) {
            peopleData = data.persons;
            renderPeople(peopleData);
        }
    } catch (error) {
        console.error('Error loading people:', error);
    }
}

function renderPeople(persons) {
    const grid = document.getElementById('peopleGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (!grid) return;

    grid.innerHTML = '';

    if (persons.length === 0) {
        if (emptyState) emptyState.style.display = 'block';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    persons.forEach(person => {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-lg-3 mb-3 person-item';
        col.dataset.name = person.name.toLowerCase();
        col.dataset.relation = person.relation;

        const initials = person.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        const relationClass = `relation-${person.relation}`;

        col.innerHTML = `
            <div class="card person-card h-100">
                <div class="card-body text-center">
                    <div class="person-avatar mx-auto mb-3">
                        ${person.profile_image ? 
                            `<img src="${person.profile_image}" alt="${person.name}" onerror="this.style.display='none'; this.parentElement.textContent='${initials}';">` :
                            initials
                        }
                    </div>
                    <h6 class="mb-1">${person.name}</h6>
                    <span class="relation-badge ${relationClass}">${person.relation}</span>
                    ${person.is_resident ? '<span class="badge bg-success ms-1" style="font-size: 0.65rem;">🔑 Resident</span>' : ''}
                    <div class="mt-2">
                        <span class="stat-mini"><i class="bi bi-fingerprint"></i> ${person.encoding_count} encodings</span>
                    </div>
                    ${person.recognition_count > 0 ? 
                        `<div><span class="stat-mini"><i class="bi bi-eye"></i> Recognized ${person.recognition_count}x</span></div>` : ''
                    }
                    ${person.last_recognized ? 
                        `<div><span class="stat-mini"><i class="bi bi-clock"></i> Last: ${formatTime(person.last_recognized)}</span></div>` : ''
                    }
                    <div class="mt-3">
                        <button class="btn btn-outline-danger btn-sm" onclick="confirmDelete(${person.id}, '${person.name.replace(/'/g, "\\'")}')" style="border-radius: 10px;">
                            <i class="bi bi-trash"></i> Remove
                        </button>
                    </div>
                </div>
            </div>
        `;

        grid.appendChild(col);
    });
}

// ── Face Stats ───────────────────────────────────────────────
async function loadFaceStats() {
    try {
        const response = await fetch('/face/stats');
        const data = await response.json();

        if (data.success) {
            const s = data.stats;
            document.getElementById('statTotal').textContent = s.enrolled_persons;
            document.getElementById('statEncodings').textContent = s.total_encodings;
            
            // Calculate resident vs guest from people data
            const residents = peopleData.filter(p => p.is_resident).length;
            const guests = peopleData.length - residents;
            document.getElementById('statResidents').textContent = residents;
            document.getElementById('statGuests').textContent = guests;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ── Search & Filter ──────────────────────────────────────────
function setupSearch() {
    const input = document.getElementById('searchPeople');
    if (!input) return;

    input.addEventListener('input', () => {
        const query = input.value.toLowerCase();
        filterPeopleDisplay(query, document.getElementById('filterRelation')?.value || '');
    });
}

function setupFilterRelation() {
    const select = document.getElementById('filterRelation');
    if (!select) return;

    select.addEventListener('change', () => {
        const query = document.getElementById('searchPeople')?.value?.toLowerCase() || '';
        filterPeopleDisplay(query, select.value);
    });
}

function filterPeopleDisplay(searchQuery, relationFilter) {
    const filtered = peopleData.filter(p => {
        const matchesSearch = !searchQuery || p.name.toLowerCase().includes(searchQuery);
        const matchesRelation = !relationFilter || p.relation === relationFilter;
        return matchesSearch && matchesRelation;
    });
    renderPeople(filtered);
}

// ── Delete Person ────────────────────────────────────────────
function confirmDelete(personId, personName) {
    deleteTargetId = personId;
    document.getElementById('deleteName').textContent = personName;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

document.addEventListener('DOMContentLoaded', () => {
    const confirmBtn = document.getElementById('confirmDelete');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async () => {
            if (!deleteTargetId) return;

            try {
                const response = await fetch(`/face/enrolled/${deleteTargetId}`, {
                    method: 'DELETE'
                });
                const data = await response.json();

                if (data.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                    if (modal) modal.hide();
                    loadPeople();
                    loadFaceStats();
                    showPageToast('success', data.message);
                } else {
                    showPageToast('error', data.message);
                }
            } catch (error) {
                showPageToast('error', `Delete failed: ${error.message}`);
            }

            deleteTargetId = null;
        });
    }
});

// ── Utilities ────────────────────────────────────────────────
function formatTime(isoString) {
    if (!isoString) return 'Never';
    const d = new Date(isoString);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return d.toLocaleDateString();
}

function showPageToast(type, message) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle';
    const toast = document.createElement('div');
    toast.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);';
    toast.innerHTML = `<i class="bi ${icon}"></i> ${message} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
