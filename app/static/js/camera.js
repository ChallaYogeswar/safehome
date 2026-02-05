let activeStreams = {};
let processingIntervals = {};

async function startCamera(cameraId) {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' },
            audio: false 
        });
        
        const video = document.getElementById(`cameraPreview${cameraId}`);
        video.srcObject = stream;
        activeStreams[cameraId] = stream;
        
        processingIntervals[cameraId] = setInterval(() => {
            processFrame(cameraId);
        }, 2000);
        
        showToast('Camera started successfully', 'success');
    } catch (error) {
        console.error('Error accessing camera:', error);
        showToast('Failed to access camera: ' + error.message, 'error');
    }
}

function stopCamera(cameraId) {
    if (activeStreams[cameraId]) {
        activeStreams[cameraId].getTracks().forEach(track => track.stop());
        delete activeStreams[cameraId];
    }
    
    if (processingIntervals[cameraId]) {
        clearInterval(processingIntervals[cameraId]);
        delete processingIntervals[cameraId];
    }
    
    const video = document.getElementById(`cameraPreview${cameraId}`);
    if (video) {
        video.srcObject = null;
    }
    
    showToast('Camera stopped', 'info');
}

async function processFrame(cameraId) {
    const video = document.getElementById(`cameraPreview${cameraId}`);
    const canvas = document.getElementById(`cameraCanvas${cameraId}`);
    
    if (!video || !canvas || !video.videoWidth) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    const frameData = canvas.toDataURL('image/jpeg', 0.8);
    
    try {
        const response = await fetch(`/camera/${cameraId}/process-frame`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ frame: frameData })
        });
        
        const data = await response.json();
        
        if (data.success && data.results) {
            handleDetectionResults(cameraId, data.results);
        }
    } catch (error) {
        console.error('Error processing frame:', error);
    }
}

function handleDetectionResults(cameraId, results) {
    if (results.motion) {
        const lastMotionEl = document.getElementById(`lastMotion${cameraId}`);
        if (lastMotionEl) {
            lastMotionEl.textContent = new Date().toLocaleString();
        }
    }
    
    if (results.objects && results.objects.length > 0) {
        console.log(`Detected objects on camera ${cameraId}:`, results.objects);
    }
    
    if (results.faces && results.faces.length > 0) {
        console.log(`Detected faces on camera ${cameraId}:`, results.faces);
    }
}

async function addCamera() {
    const name = document.getElementById('cameraName').value;
    const location = document.getElementById('cameraLocation').value;
    
    if (!name) {
        showToast('Please enter a camera name', 'error');
        return;
    }
    
    try {
        const response = await fetch('/camera/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, location })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Camera added successfully', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast('Failed to add camera: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error adding camera', 'error');
    }
}

async function deleteCamera(cameraId) {
    if (!confirm('Are you sure you want to delete this camera?')) {
        return;
    }
    
    stopCamera(cameraId);
    
    try {
        const response = await fetch(`/camera/${cameraId}/delete`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Camera deleted successfully', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('Failed to delete camera', 'error');
        }
    } catch (error) {
        showToast('Error deleting camera', 'error');
    }
}

function showToast(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => alertDiv.remove(), 5000);
}
