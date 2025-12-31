// IronCore Gym - Main Frontend Script

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        console.log("IronCore Gym script loaded ✅");

        initYear();
        initMobileNav();
        initSmoothScroll();
        initContactForm();
    });

    function initYear() {
        const yearEl = document.getElementById("year");
        if (yearEl) {
            yearEl.textContent = String(new Date().getFullYear());
        }
    }

    function initMobileNav() {
        const toggle = document.querySelector(".nav-toggle");
        const navLinks = document.querySelector(".nav-links");
        if (!toggle || !navLinks) return;

        toggle.addEventListener("click", function () {
            const isOpen = navLinks.classList.toggle("open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });

        // Close menu when clicking a link (mobile UX)
        navLinks.addEventListener("click", function (event) {
            const target = event.target;
            if (target instanceof HTMLAnchorElement && navLinks.classList.contains("open")) {
                navLinks.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    function initSmoothScroll() {
        const anchors = document.querySelectorAll('a[href^="#"]');
        anchors.forEach(function (anchor) {
            anchor.addEventListener("click", function (event) {
                const target = event.currentTarget;
                if (!(target instanceof HTMLAnchorElement)) return;

                const href = target.getAttribute("href");
                if (!href || href === "#") return;

                const id = href.slice(1);
                const section = document.getElementById(id);
                if (!section) return;

                event.preventDefault();
                section.scrollIntoView({ behavior: "smooth" });
            });
        });
    }

    function initContactForm() {
        const form = document.getElementById("contact-form");
        if (!form) return; // Only on contact.html

        const messageEl = document.getElementById("form-message");
        const errorEls = {
            name: document.querySelector('.field-error[data-for="name"]'),
            email: document.querySelector('.field-error[data-for="email"]'),
            phone: document.querySelector('.field-error[data-for="phone"]'),
            message: document.querySelector('.field-error[data-for="message"]')
        };

        form.addEventListener("submit", function (event) {
            const formData = new FormData(form);
            const name = String(formData.get("name") || "").trim();
            const email = String(formData.get("email") || "").trim();
            const phone = String(formData.get("phone") || "").trim();
            const message = String(formData.get("message") || "").trim();

            const errors = validateFields({ name, email, phone, message });

            // Clear previous errors
            Object.keys(errorEls).forEach(function (key) {
                const el = errorEls[key];
                if (el) el.textContent = "";
            });

            if (errors.length > 0) {
                event.preventDefault(); // Stop submission if there are validation errors
                errors.forEach(function (err) {
                    const fieldErrorEl = errorEls[err.field];
                    if (fieldErrorEl) fieldErrorEl.textContent = err.message;
                });

                if (messageEl) {
                    messageEl.textContent = "Please fix the highlighted fields and try again.";
                    messageEl.classList.remove("success");
                    messageEl.classList.add("error");
                }
                return;
            }
            
            // If valid, let the form submit normally to the Flask backend
        });
    }

    function validateFields(values) {
        /** @type {{ field: 'name' | 'email' | 'phone' | 'message'; message: string }[]} */
        const errors = [];

        if (!values.name || values.name.length < 2) {
            errors.push({ field: "name", message: "Please enter your name (at least 2 characters)." });
        }

        if (!values.email) {
            errors.push({ field: "email", message: "Please enter your email address." });
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
            errors.push({ field: "email", message: "Please enter a valid email address." });
        }

        if (!values.phone) {
            errors.push({ field: "phone", message: "Please enter your phone number." });
        } else if (values.phone.length < 7) {
            errors.push({ field: "phone", message: "Please enter a valid phone number." });
        }

        if (!values.message || values.message.length < 10) {
            errors.push({ field: "message", message: "Please enter a message (at least 10 characters)." });
        }

        return errors;
    }
})();
