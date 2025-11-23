// Connect to Python backend
window.addEventListener('pywebviewready', function() {
    console.log('PyWebView Ready');
    // Load saved settings
    pywebview.api.get_config().then(function(config) {
        // Update UI elements
        smoothInput.value = config.smoothening_medium;
        smoothVal.textContent = config.smoothening_medium;
        
        clickInput.value = config.click_threshold;
        clickVal.textContent = config.click_threshold;
        
        scrollToggle.checked = config.scroll_enabled;
        rightClickToggle.checked = config.right_click_enabled;
    });

    // Check for updates
    pywebview.api.check_updates().then(function(result) {
        if (result.update_available) {
            const link = document.getElementById('updateLink');
            link.textContent = "Update Available (" + result.latest_version + ")";
            link.style.color = "#ff4757"; // Red/Attention color
            link.onclick = function() {
                pywebview.api.open_url(result.download_url);
            };
        }
    });
});

const powerBtn = document.getElementById('powerBtn');
const statusBadge = document.getElementById('statusBadge');
const powerText = document.getElementById('powerText');

let isActive = false;

// Listen for Stop Event from Python (Fist Gesture)
window.addEventListener('stop_mouse_event', function() {
    if (isActive) {
        isActive = false;
        updatePowerState();
    }
});

powerBtn.addEventListener('click', function() {
    isActive = !isActive;
    updatePowerState();
    
    // Call Python
    if (isActive) {
        pywebview.api.start_mouse();
    } else {
        pywebview.api.stop_mouse();
    }
});

function updatePowerState() {
    if (isActive) {
        powerBtn.classList.add('active');
        statusBadge.classList.add('active');
        statusBadge.textContent = "ONLINE";
        powerText.textContent = "Click to Stop (or make a Fist)";
    } else {
        powerBtn.classList.remove('active');
        statusBadge.classList.remove('active');
        statusBadge.textContent = "OFFLINE";
        powerText.textContent = "Click to Start";
    }
}

// Sliders
const smoothInput = document.getElementById('smoothInput');
const smoothVal = document.getElementById('smoothVal');

smoothInput.addEventListener('input', function(e) {
    const val = e.target.value;
    smoothVal.textContent = val;
    pywebview.api.update_config('smoothening_medium', parseInt(val)); 
});

const clickInput = document.getElementById('clickInput');
const clickVal = document.getElementById('clickVal');

clickInput.addEventListener('input', function(e) {
    const val = e.target.value;
    clickVal.textContent = val;
    pywebview.api.update_config('click_threshold', parseInt(val));
});

// Toggles
const scrollToggle = document.getElementById('scrollToggle');
scrollToggle.addEventListener('change', function(e) {
    pywebview.api.update_config('scroll_enabled', e.target.checked);
});

const rightClickToggle = document.getElementById('rightClickToggle');
rightClickToggle.addEventListener('change', function(e) {
    pywebview.api.update_config('right_click_enabled', e.target.checked);
});
