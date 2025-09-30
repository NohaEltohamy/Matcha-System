// Authentication JavaScript for Matcha AI

// Password visibility toggle
function togglePassword(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const eyeIcon = document.getElementById(`eye-${fieldId}`);
    const eyeOffIcon = document.getElementById(`eye-off-${fieldId}`);
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        eyeIcon.style.display = 'none';
        eyeOffIcon.style.display = 'block';
    } else {
        passwordField.type = 'password';
        eyeIcon.style.display = 'block';
        eyeOffIcon.style.display = 'none';
    }
}

// Password strength checker
function checkPasswordStrength(password) {
    const strengthIndicator = document.getElementById('passwordStrength');
    if (!strengthIndicator) return;
    
    let strength = 0;
    let feedback = '';
    
    // Length check
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Character variety checks
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    // Determine strength level and feedback
    if (password.length === 0) {
        feedback = '';
        strengthIndicator.className = 'password-strength';
    } else if (strength < 3) {
        feedback = 'Weak password';
        strengthIndicator.className = 'password-strength weak';
    } else if (strength < 5) {
        feedback = 'Medium password';
        strengthIndicator.className = 'password-strength medium';
    } else {
        feedback = 'Strong password';
        strengthIndicator.className = 'password-strength strong';
    }
    
    strengthIndicator.textContent = feedback;
}

// Form validation
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 8;
}

function validateForm(form) {
    const formData = new FormData(form);
    const errors = [];
    
    // Email validation
    const email = formData.get('email');
    if (!email || !validateEmail(email)) {
        errors.push('Please enter a valid email address');
    }
    
    // Password validation
    const password = formData.get('password');
    if (!password || !validatePassword(password)) {
        errors.push('Password must be at least 8 characters long');
    }
    
    // Confirm password validation (for signup)
    const confirmPassword = formData.get('confirmPassword');
    if (confirmPassword !== null && password !== confirmPassword) {
        errors.push('Passwords do not match');
    }
    
    // Terms validation (for signup)
    const terms = formData.get('terms');
    if (form.id === 'signupForm' && !terms) {
        errors.push('Please accept the Terms of Service');
    }
    
    return errors;
}

// Handle login form submission
function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const errors = validateForm(form);
    
    if (errors.length > 0) {
        showToast(errors[0], 'error');
        return;
    }
    
    const formData = new FormData(form);
    const loginData = {
        email: formData.get('email'),
        password: formData.get('password'),
        remember: formData.get('remember') === 'on'
    };
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i data-lucide="loader-2"></i> Signing In...';
    submitBtn.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        
        // Simulate successful login
        showToast('Login successful! Redirecting...', 'success');
        
        // Store user session (in real app, this would be handled by backend)
        localStorage.setItem('matcha_user', JSON.stringify({
            email: loginData.email,
            loginTime: Date.now()
        }));
        
        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = 'demo.html';
        }, 1500);
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 2000);
}

// Handle signup form submission
function handleSignup(event) {
    event.preventDefault();
    const form = event.target;
    const errors = validateForm(form);
    
    if (errors.length > 0) {
        showToast(errors[0], 'error');
        return;
    }
    
    const formData = new FormData(form);
    const signupData = {
        firstName: formData.get('firstName'),
        lastName: formData.get('lastName'),
        email: formData.get('email'),
        company: formData.get('company'),
        password: formData.get('password'),
        marketing: formData.get('marketing') === 'on'
    };
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i data-lucide="loader-2"></i> Creating Account...';
    submitBtn.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        
        // Simulate successful signup
        showToast('Account created successfully! Welcome to Matcha AI!', 'success');
        
        // Store user session
        localStorage.setItem('matcha_user', JSON.stringify({
            firstName: signupData.firstName,
            lastName: signupData.lastName,
            email: signupData.email,
            company: signupData.company,
            signupTime: Date.now()
        }));
        
        // Redirect to demo/dashboard
        setTimeout(() => {
            window.location.href = 'demo.html';
        }, 1500);
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 2000);
}

// Handle social login buttons
function handleSocialLogin(provider) {
    showToast(`${provider} login integration coming soon!`, 'info');
}

// Initialize auth functionality
document.addEventListener('DOMContentLoaded', function() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Signup form
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
        
        // Password strength checking
        const passwordField = document.getElementById('password');
        if (passwordField) {
            passwordField.addEventListener('input', function() {
                checkPasswordStrength(this.value);
            });
        }
        
        // Password confirmation validation
        const confirmPasswordField = document.getElementById('confirmPassword');
        if (confirmPasswordField) {
            confirmPasswordField.addEventListener('input', function() {
                const password = document.getElementById('password').value;
                const confirmPassword = this.value;
                
                if (confirmPassword && password !== confirmPassword) {
                    this.classList.add('error');
                } else {
                    this.classList.remove('error');
                }
            });
        }
    }
    
    // Social login buttons
    const socialButtons = document.querySelectorAll('.social-login button');
    socialButtons.forEach(button => {
        button.addEventListener('click', function() {
            const provider = this.textContent.includes('Google') ? 'Google' : 'GitHub';
            handleSocialLogin(provider);
        });
    });
    
    // Real-time form validation
    const formInputs = document.querySelectorAll('input[required]');
    formInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                this.classList.add('error');
            } else {
                this.classList.remove('error');
                
                // Specific validations
                if (this.type === 'email' && !validateEmail(this.value)) {
                    this.classList.add('error');
                }
            }
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('error') && this.value.trim() !== '') {
                this.classList.remove('error');
            }
        });
    });
    
    // Check if user is already logged in
    const userData = localStorage.getItem('matcha_user');
    if (userData && (window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('signup.html'))) {
        // User is already logged in, redirect to dashboard
        window.location.href = 'demo.html';
    }
});

// Logout function (for future use)
function logout() {
    localStorage.removeItem('matcha_user');
    showToast('Logged out successfully', 'success');
    window.location.href = 'index.html';
}

// Check authentication status (for future use)
function isAuthenticated() {
    const userData = localStorage.getItem('matcha_user');
    return userData !== null;
}

// Get current user data (for future use)
function getCurrentUser() {
    const userData = localStorage.getItem('matcha_user');
    return userData ? JSON.parse(userData) : null;
}