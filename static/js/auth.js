// Utility functions for authentication
const authUtils = {
    // Get CSRF token from cookie
    getCsrfToken: function() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    // Show error message
    showError: function(element, message) {
        element.classList.add('is-invalid');
        const feedback = element.nextElementSibling;
        if (feedback) {
            feedback.textContent = message;
        }
    },

    // Clear error message
    clearError: function(element) {
        element.classList.remove('is-invalid');
        const feedback = element.nextElementSibling;
        if (feedback) {
            feedback.textContent = '';
        }
    },

    // Clear all errors in a form
    clearAllErrors: function(form) {
        form.querySelectorAll('.is-invalid').forEach(el => {
            this.clearError(el);
        });
        const alerts = form.querySelectorAll('.alert');
        alerts.forEach(alert => alert.remove());
    },

    // Handle API errors
    handleApiError: function(error) {
        console.error('API Error:', error);
        if (error.response) {
            return error.response.json();
        }
        throw error;
    },

    // Check if user is authenticated
    isAuthenticated: function() {
        return document.cookie.includes('sessionid=');
    },

    // Redirect if authenticated
    redirectIfAuthenticated: function(url) {
        if (this.isAuthenticated()) {
            window.location.href = url;
        }
    },

    // Redirect if not authenticated
    redirectIfNotAuthenticated: function(url) {
        if (!this.isAuthenticated()) {
            window.location.href = url;
        }
    }
};

// Form validation
const formValidation = {
    // Validate email format
    isValidEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Validate password strength
    isStrongPassword: function(password) {
        // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
        const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/;
        return re.test(password);
    },

    // Validate username format
    isValidUsername: function(username) {
        // 3-20 characters, letters, numbers, underscores, hyphens
        const re = /^[a-zA-Z0-9_-]{3,20}$/;
        return re.test(username);
    }
};

// Export utilities
window.authUtils = authUtils;
window.formValidation = formValidation; 