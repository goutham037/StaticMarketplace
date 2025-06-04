// GreenBridge Main JavaScript
// Global utilities and common functionality

// Global variables
let map;
let marker;
let selectedRice = '';
let currentLocation = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeGlobalFeatures();
});

// Initialize global features
function initializeGlobalFeatures() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize flash message auto-hide
    initializeFlashMessages();
    
    // Initialize loading states
    initializeLoadingStates();
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Smooth scrolling for anchor links
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Flash messages auto-hide
function initializeFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Auto-hide success messages after 5 seconds
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                fadeOutElement(alert);
            }, 5000);
        }
    });
}

// Loading states for buttons
function initializeLoadingStates() {
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-loading')) {
            showButtonLoading(e.target);
        }
    });
}

// Utility Functions

// Show loading state on button
function showButtonLoading(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...';
    
    // Store original text for restoration
    button.dataset.originalText = originalText;
}

// Hide loading state on button
function hideButtonLoading(button) {
    if (button.dataset.originalText) {
        button.innerHTML = button.dataset.originalText;
        button.disabled = false;
        delete button.dataset.originalText;
    }
}

// Fade out element
function fadeOutElement(element) {
    element.style.transition = 'opacity 0.5s ease-out';
    element.style.opacity = '0';
    setTimeout(() => {
        element.style.display = 'none';
    }, 500);
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} toast-notification`;
    toast.innerHTML = `
        <span>${message}</span>
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    // Add toast styles
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        fadeOutElement(toast);
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

// Format number with Indian number system
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

// Validate Indian mobile number
function validateMobileNumber(mobile) {
    const mobileRegex = /^[6-9]\d{9}$/;
    return mobileRegex.test(mobile);
}

// Get user's current location
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => {
                const location = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };
                currentLocation = location;
                resolve(location);
            },
            error => {
                let errorMessage = 'Unable to get location';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location access denied by user';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information unavailable';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out';
                        break;
                }
                reject(new Error(errorMessage));
            }
        );
    });
}

// Initialize map (Leaflet.js)
function initializeMap(containerId, options = {}) {
    const defaultOptions = {
        center: [20.5937, 78.9629], // Center of India
        zoom: 5,
        ...options
    };
    
    map = L.map(containerId).setView(defaultOptions.center, defaultOptions.zoom);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    return map;
}

// Update map location
function updateMapLocation(lat, lng, zoom = 13) {
    if (!map) return;
    
    if (marker) {
        marker.remove();
    }
    
    map.setView([lat, lng], zoom);
    marker = L.marker([lat, lng]).addTo(map);
    
    // Update current location
    currentLocation = { latitude: lat, longitude: lng };
}

// Reverse geocoding using Nominatim
async function reverseGeocode(lat, lng) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`
        );
        const data = await response.json();
        return data.display_name || 'Unknown location';
    } catch (error) {
        console.error('Reverse geocoding error:', error);
        return 'Unknown location';
    }
}

// Forward geocoding using Nominatim
async function forwardGeocode(address) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`
        );
        const data = await response.json();
        if (data.length > 0) {
            return {
                latitude: parseFloat(data[0].lat),
                longitude: parseFloat(data[0].lon),
                display_name: data[0].display_name
            };
        }
        return null;
    } catch (error) {
        console.error('Forward geocoding error:', error);
        return null;
    }
}

// Calculate distance between two points (Haversine formula)
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of Earth in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// API call wrapper with error handling
async function apiCall(url, options = {}) {
    try {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        const response = await fetch(url, defaultOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('API call error:', error);
        return { success: false, error: error.message };
    }
}

// Local storage utilities
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('LocalStorage set error:', error);
            return false;
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('LocalStorage get error:', error);
            return defaultValue;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('LocalStorage remove error:', error);
            return false;
        }
    }
};

// Language utilities
function getCurrentLanguage() {
    return document.documentElement.lang || 'en';
}

function setLanguage(lang) {
    // This would typically trigger a page reload with new language
    window.location.href = `/language/${lang}`;
}

// Form utilities
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        if (data[key]) {
            // Handle multiple values (checkboxes, etc.)
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    }
    return data;
}

function resetForm(form) {
    form.reset();
    form.classList.remove('was-validated');
    
    // Clear any error states
    const inputs = form.querySelectorAll('.form-control, .form-select');
    inputs.forEach(input => {
        input.classList.remove('is-invalid', 'is-valid');
    });
}

// Animation utilities
function animateElement(element, animationClass) {
    element.classList.add(animationClass);
    element.addEventListener('animationend', () => {
        element.classList.remove(animationClass);
    }, { once: true });
}

// Export functions for use in other modules
window.GreenBridge = {
    // Utility functions
    showToast,
    formatCurrency,
    formatNumber,
    validateMobileNumber,
    getCurrentLocation,
    calculateDistance,
    reverseGeocode,
    forwardGeocode,
    debounce,
    apiCall,
    
    // Map functions
    initializeMap,
    updateMapLocation,
    
    // Storage
    Storage,
    
    // Form utilities
    serializeForm,
    resetForm,
    
    // Loading states
    showButtonLoading,
    hideButtonLoading,
    
    // Animation
    animateElement,
    fadeOutElement,
    
    // Language
    getCurrentLanguage,
    setLanguage
};
