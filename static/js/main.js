// Studio A Website JavaScript with Language Switching
// Main functionality and interactions

document.addEventListener('DOMContentLoaded', function() {
    // Language Switching
    const currentLang = window.location.pathname.includes('/bg/') ? 'bg' : 'en';
    const langButtons = document.querySelectorAll('.lang-btn');

    // Set active language button
    langButtons.forEach(btn => {
        if (btn.dataset.lang === currentLang) {
            btn.classList.add('active');
        }
    });

    // Language switcher functionality
    langButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetLang = this.dataset.lang;
            const currentPath = window.location.pathname;

            let newPath;
            if (currentPath.includes('/bg/')) {
                // Switch from BG to EN
                newPath = currentPath.replace('/bg/', '/en/');
            } else if (currentPath.includes('/en/')) {
                // Switch from EN to BG
                newPath = currentPath.replace('/en/', '/bg/');
            } else {
                // On root, determine where to go
                if (targetLang === 'bg') {
                    newPath = '/BG/index.html';
                } else {
                    newPath = '/en/index.html';
                }
            }

            window.location.href = newPath;
        });
    });

    // Mobile Menu Toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.textContent = navMenu.classList.contains('active') ? '✕' : '☰';
        });
    }

    // Smooth Scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    // Close mobile menu if open
                    if (navMenu && navMenu.classList.contains('active')) {
                        navMenu.classList.remove('active');
                        if (mobileMenuToggle) {
                            mobileMenuToggle.textContent = '☰';
                        }
                    }
                }
            }
        });
    });

    // Header scroll effect
    const header = document.querySelector('.header');
    let lastScroll = 0;

    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
    });

    // Form validation and submission
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            if (validateForm(data)) {
                const successMsg = currentLang === 'bg'
                    ? 'Благодарим! Вашето съобщение беше изпратено успешно.'
                    : 'Thank you! Your message has been sent successfully.';
                showNotification(successMsg, 'success');
                this.reset();
            }
        });
    }

    // Booking form
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            if (validateForm(data)) {
                const successMsg = currentLang === 'bg'
                    ? 'Благодарим! Ще се свържем с вас в рамките на 24 часа за потвърждение.'
                    : 'Thank you! We will contact you within 24 hours to confirm your appointment.';
                showNotification(successMsg, 'success');
                this.reset();
            }
        });
    }

    // Form validation function
    function validateForm(data) {
        let isValid = true;

        const nameError = currentLang === 'bg' ? 'Моля, въведете валидно име' : 'Please enter a valid name';
        const emailError = currentLang === 'bg' ? 'Моля, въведете валиден имейл адрес' : 'Please enter a valid email address';
        const phoneError = currentLang === 'bg' ? 'Моля, въведете валиден телефонен номер' : 'Please enter a valid phone number';
        const messageError = currentLang === 'bg' ? 'Моля, въведете съобщение (минимум 10 символа)' : 'Please enter a message (at least 10 characters)';

        // Name validation
        if (!data.name || data.name.trim().length < 2) {
            showNotification(nameError, 'error');
            isValid = false;
        }

        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!data.email || !emailRegex.test(data.email)) {
            showNotification(emailError, 'error');
            isValid = false;
        }

        // Phone validation
        if (!data.phone || data.phone.trim().length < 6) {
            showNotification(phoneError, 'error');
            isValid = false;
        }

        // Message validation (if exists)
        if (data.message && data.message.trim().length < 10) {
            showNotification(messageError, 'error');
            isValid = false;
        }

        return isValid;
    }

    // Notification system
    function showNotification(message, type = 'info') {
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.procedure-card, .category-card, .testimonial-card').forEach(element => {
        observer.observe(element);
    });

    // Active navigation highlighting
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu a');

    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (currentLocation === linkPath ||
            (currentLocation.includes(linkPath) && linkPath !== '/')) {
            link.classList.add('active');
        }
    });

    // Booking button functionality
    const bookingButtons = document.querySelectorAll('.booking-btn, .hero-cta');
    bookingButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.href || this.href.includes('#')) {
                e.preventDefault();
                const msg = currentLang === 'bg'
                    ? 'Системата за резервации е в процес на интеграция. Моля, обадете ни се директно.'
                    : 'Booking system integration pending. Please call us directly.';
                showNotification(msg, 'info');
            }
        });
    });
});

// External link handler
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.hostname !== window.location.hostname) {
        e.target.setAttribute('target', '_blank');
        e.target.setAttribute('rel', 'noopener noreferrer');
    }
});

// Console message
console.log('%c Studio A Website ', 'background: #b8985f; color: white; font-size: 20px; padding: 10px;');
console.log('Bilingual website - English & Bulgarian');
