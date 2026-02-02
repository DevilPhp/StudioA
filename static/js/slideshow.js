// Slideshow Manager for Studio A Website
// Handles slideshow functionality and admin controls

class SlideshowManager {
    constructor() {
        this.slides = [];
        this.currentSlide = 0;
        this.duration = 5000; // 5 seconds default
        this.intervalId = null;
        this.isAdmin = false;
        this.currentLang = window.location.pathname.includes('/BG/') ? 'bg' : 'en';

        this.init();
    }

    init() {
        // Check if logged in as admin
        this.isAdmin = localStorage.getItem('adminLoggedIn') === 'true';

        // Load slides from localStorage
        this.loadSlides();

        // Render slideshow
        this.renderSlideshow();

        // Start auto-play
        this.startAutoPlay();

        // Setup controls
        this.setupControls();

        // Show admin controls if logged in
        if (this.isAdmin) {
            this.showAdminControls();
        }
    }

    loadSlides() {
        // const savedSlides = localStorage.getItem(`slideshow_${this.currentLang}`);
        const savedSlides = NaN
        const savedDuration = localStorage.getItem('slideshow_duration');

        if (savedDuration) {
            this.duration = parseInt(savedDuration);
        }

        if (savedSlides) {
            this.slides = JSON.parse(savedSlides);
        } else {
            // Default slides
            if (this.currentLang === 'EN') {
                this.slides = [
                    {
                        image: 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=1200',
                        title: 'New Treatment Available',
                        description: 'Discover our latest skin rejuvenation therapy',
                        buttonText: 'Learn More'
                    },
                    {
                        image: 'https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?w=1200',
                        title: '20% Off This Month',
                        description: 'Special discount on all laser treatments',
                        buttonText: 'Book Now',
                        buttonLink: 'booking.html'
                    },
                    {
                        image: 'https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=1200',
                        title: 'Premium Skincare Products',
                        description: 'Shop our exclusive product line',
                        buttonText: 'Shop Now',
                        buttonLink: 'services.html'
                    }
                ];
            } else {
                this.slides = [
                    {
                        image: 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=1200',
                        title: 'Нова козметична марка в салона',
                        description: 'Открийте нашите най-нови терапии за лице',
                        buttonText: 'Научете повече'
                    },
                    {
                        image: 'https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?w=1200',
                        title: '20% отстъпка този месец',
                        description: 'Специална отстъпка на всички лазерни процедури',
                        buttonText: 'Резервирай',
                        buttonLink: 'booking.html'
                    },
                    {
                        image: 'https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=1200',
                        title: 'Премиум продукти за грижа',
                        description: 'Разгледайте нашата ексклузивна продуктова линия',
                        buttonText: 'Купи сега',
                        buttonLink: 'services.html'
                    }
                ];
            }
            this.saveSlides();
        }
    }

    saveSlides() {
        localStorage.setItem(`slideshow_${this.currentLang}`, JSON.stringify(this.slides));
    }

    saveDuration() {
        localStorage.setItem('slideshow_duration', this.duration.toString());
    }

    renderSlideshow() {
        const banner = document.querySelector('.slideshow-banner');
        if (!banner) return;

        let html = '<div class="slideshow-container">';

        // Render slides
        this.slides.forEach((slide, index) => {
            html += `
                <div class="slide ${index === 0 ? 'active' : ''}" data-slide="${index}">
                    <img src="${slide.image}" alt="${slide.title}">
                    <div class="slide-content">
                        <h2>${slide.title}</h2>
                        <p>${slide.description}</p>
                        ${slide.buttonText ? `<a href="${slide.buttonLink}" class="slide-cta">${slide.buttonText}</a>` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div>';

        // Add navigation arrows
        html += `
            <button class="slide-prev" aria-label="Previous slide">❮</button>
            <button class="slide-next" aria-label="Next slide">❯</button>
        `;

        // Add dots
        html += '<div class="slideshow-controls">';
        this.slides.forEach((_, index) => {
            html += `<span class="slide-dot ${index === 0 ? 'active' : ''}" data-slide="${index}"></span>`;
        });
        html += '</div>';

        // Add admin controls if logged in
        if (this.isAdmin) {
            html += `
                <div class="admin-controls visible">
                    <button class="admin-btn" onclick="slideshowManager.openAdminPanel()">Edit Slideshow</button>
                </div>
            `;
        }

        banner.innerHTML = html;
    }

    setupControls() {
        const prevBtn = document.querySelector('.slide-prev');
        const nextBtn = document.querySelector('.slide-next');
        const dots = document.querySelectorAll('.slide-dot');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousSlide());
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextSlide());
        }

        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => this.goToSlide(index));
        });
    }

    startAutoPlay() {
        this.stopAutoPlay();
        this.intervalId = setInterval(() => this.nextSlide(), this.duration);
    }

    stopAutoPlay() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    nextSlide() {
        this.currentSlide = (this.currentSlide + 1) % this.slides.length;
        this.showSlide(this.currentSlide);
    }

    previousSlide() {
        this.currentSlide = (this.currentSlide - 1 + this.slides.length) % this.slides.length;
        this.showSlide(this.currentSlide);
    }

    goToSlide(index) {
        this.currentSlide = index;
        this.showSlide(this.currentSlide);
        this.startAutoPlay();
    }

    showSlide(index) {
        const slides = document.querySelectorAll('.slide');
        const dots = document.querySelectorAll('.slide-dot');

        slides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));

        if (slides[index]) {
            slides[index].classList.add('active');
        }
        if (dots[index]) {
            dots[index].classList.add('active');
        }
    }

    showAdminControls() {
        const controls = document.querySelector('.admin-controls');
        if (controls) {
            controls.classList.add('visible');
        }
    }

    openAdminPanel() {
        window.location.href = '../admin/slideshow.html';
    }
}

// Initialize slideshow when DOM is ready
let slideshowManager;

document.addEventListener('DOMContentLoaded', function() {
    const slideshowBanner = document.querySelector('.slideshow-banner');
    if (slideshowBanner) {
        slideshowManager = new SlideshowManager();
    }
});
