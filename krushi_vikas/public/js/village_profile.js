/**
 * Village Profile Wizard Interactive Controller
 * Copyright (c) 2026, Krushi Vikas and contributors
 */

(function() {
  'use strict';

  let currentStep = 1;
  const totalSteps = 4;

  window.VillageWizard = {
    init: function() {
      this.bindEvents();
      this.setupAutoCalculations();
    },

    bindEvents: function() {
      // Clear errors on input
      document.querySelectorAll('input, select, textarea').forEach(el => {
        el.addEventListener('input', function() {
          const errEl = document.getElementById('err-' + this.id);
          if (errEl) {
            errEl.textContent = '';
            el.classList.remove('is-invalid');
          }
        });
      });
    },

    setupAutoCalculations: function() {
      const totalGeo = document.getElementById('total_geographical_area_ha');
      const cultLand = document.getElementById('cultivable_land_ha');
      const irriLand = document.getElementById('irrigated_area_ha');
      const rainfedLand = document.getElementById('rainfed_area_ha');
      const wasteLand = document.getElementById('forest_wasteland_ha');

      const calcLand = function() {
        const total = parseFloat(totalGeo.value) || 0;
        const cult = parseFloat(cultLand.value) || 0;
        const irri = parseFloat(irriLand.value) || 0;

        if (cult > 0 && irri >= 0 && (!rainfedLand.value || rainfedLand.dataset.auto === "1")) {
          const autoRainfed = Math.max(0, cult - irri);
          rainfedLand.value = autoRainfed.toFixed(1);
          rainfedLand.dataset.auto = "1";
        }

        if (total > 0 && cult > 0 && (!wasteLand.value || wasteLand.dataset.auto === "1")) {
          const autoWaste = Math.max(0, total - cult);
          wasteLand.value = autoWaste.toFixed(1);
          wasteLand.dataset.auto = "1";
        }
      };

      if (totalGeo && cultLand && irriLand) {
        totalGeo.addEventListener('input', calcLand);
        cultLand.addEventListener('input', calcLand);
        irriLand.addEventListener('input', calcLand);
      }
    },

    goToStep: function(targetStep) {
      if (targetStep > currentStep) {
        if (!this.validateStep(currentStep)) {
          return;
        }
      }

      // Hide all steps
      for (let i = 1; i <= totalSteps; i++) {
        const stepEl = document.getElementById('step-' + i);
        const navEl = document.getElementById('nav-step-' + i);
        if (stepEl) stepEl.classList.remove('active');
        if (navEl) {
          navEl.classList.remove('active');
          if (i < targetStep) {
            navEl.classList.add('completed');
          } else {
            navEl.classList.remove('completed');
          }
        }
      }

      currentStep = targetStep;
      const targetEl = document.getElementById('step-' + currentStep);
      const targetNav = document.getElementById('nav-step-' + currentStep);
      if (targetEl) targetEl.classList.add('active');
      if (targetNav) targetNav.classList.add('active');

      if (currentStep === 4) {
        this.renderReviewSummary();
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    validateStep: function(step) {
      let isValid = true;

      const markError = (id, message) => {
        const input = document.getElementById(id);
        const err = document.getElementById('err-' + id);
        if (input) input.classList.add('is-invalid');
        if (err) err.textContent = message;
        isValid = false;
      };

      if (step === 1) {
        const village = document.getElementById('village_name').value.trim();
        const gp = document.getElementById('gram_panchayat').value.trim();
        const taluka = document.getElementById('block_taluka').value;
        const district = document.getElementById('district').value;
        const surveyDate = document.getElementById('date_of_survey').value;
        const pop = parseInt(document.getElementById('total_population').value, 10);
        const households = parseInt(document.getElementById('total_households').value, 10);

        if (!village) markError('village_name', 'Village name is required.');
        if (!gp) markError('gram_panchayat', 'Gram Panchayat is required.');
        if (!taluka) markError('block_taluka', 'Please select a Block / Taluka.');
        if (!district) markError('district', 'Please select a District.');
        if (!surveyDate) {
          markError('date_of_survey', 'Survey date is required.');
        } else {
          const today = new Date().toISOString().split('T')[0];
          if (surveyDate > today) {
            markError('date_of_survey', 'Survey date cannot be in the future.');
          }
        }

        if (isNaN(pop) || pop <= 0) {
          markError('total_population', 'Please enter a valid total population.');
        }
        if (isNaN(households) || households <= 0) {
          markError('total_households', 'Please enter a valid total household count.');
        }
      }

      if (step === 2) {
        const totalGeo = parseFloat(document.getElementById('total_geographical_area_ha').value);
        const cult = parseFloat(document.getElementById('cultivable_land_ha').value);

        if (isNaN(totalGeo) || totalGeo <= 0) {
          markError('total_geographical_area_ha', 'Total geographical area is required.');
        }
        if (isNaN(cult) || cult <= 0) {
          markError('cultivable_land_ha', 'Cultivable land area is required.');
        } else if (totalGeo > 0 && cult > totalGeo) {
          markError('cultivable_land_ha', 'Cultivable land cannot exceed total geographical area.');
        }
      }

      if (step === 3) {
        const scarcity = document.getElementById('summer_water_scarcity_status').value;
        if (!scarcity) {
          markError('summer_water_scarcity_status', 'Please select summer water scarcity status.');
        }
      }

      return isValid;
    },

    renderReviewSummary: function() {
      const container = document.getElementById('reviewCardsContainer');
      if (!container) return;

      const getVal = id => {
        const el = document.getElementById(id);
        if (!el) return '-';
        if (el.type === 'checkbox') return el.checked ? 'Yes' : 'No';
        if (el.tagName === 'SELECT' && el.selectedIndex >= 0) {
          return el.options[el.selectedIndex].text;
        }
        return el.value.trim() || '-';
      };

      const village = getVal('village_name');
      const gp = getVal('gram_panchayat');
      const taluka = getVal('block_taluka');
      const district = getVal('district');
      const pop = getVal('total_population');
      const households = getVal('total_households');
      const date = getVal('date_of_survey');
      const totalGeo = getVal('total_geographical_area_ha');
      const cultivable = getVal('cultivable_land_ha');
      const irrigated = getVal('irrigated_area_ha');
      const rainfed = getVal('rainfed_area_ha');
      const soil = getVal('soil_type');
      const scarcity = getVal('summer_water_scarcity_status');
      const watershed = getVal('watershed_name');
      const shgs = getVal('total_shgs_count');
      const fpos = getVal('active_fpos_count');

      container.innerHTML = `
        <div class="review-card">
          <div class="review-card-header">
            <h4>1. Location & Demographics</h4>
            <button type="button" class="btn-link" onclick="window.VillageWizard.goToStep(1)">Edit</button>
          </div>
          <div class="review-grid">
            <div class="review-item"><span class="review-label">Village / GP</span><span class="review-val">${village} (${gp})</span></div>
            <div class="review-item"><span class="review-label">Taluka / District</span><span class="review-val">${taluka}, ${district}</span></div>
            <div class="review-item"><span class="review-label">Total Population</span><span class="review-val">${pop}</span></div>
            <div class="review-item"><span class="review-label">Total Households</span><span class="review-val">${households}</span></div>
            <div class="review-item"><span class="review-label">Survey Date</span><span class="review-val">${date}</span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4>2. Land & Agriculture</h4>
            <button type="button" class="btn-link" onclick="window.VillageWizard.goToStep(2)">Edit</button>
          </div>
          <div class="review-grid">
            <div class="review-item"><span class="review-label">Total Geographical Area</span><span class="review-val">${totalGeo} Ha</span></div>
            <div class="review-item"><span class="review-label">Cultivable Land</span><span class="review-val">${cultivable} Ha</span></div>
            <div class="review-item"><span class="review-label">Irrigated / Rainfed</span><span class="review-val">${irrigated} Ha / ${rainfed} Ha</span></div>
            <div class="review-item"><span class="review-label">Dominant Soil Type</span><span class="review-val">${soil}</span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4>3. Water & Infrastructure</h4>
            <button type="button" class="btn-link" onclick="window.VillageWizard.goToStep(3)">Edit</button>
          </div>
          <div class="review-grid">
            <div class="review-item"><span class="review-label">Watershed Basin</span><span class="review-val">${watershed}</span></div>
            <div class="review-item"><span class="review-label">Summer Water Scarcity</span><span class="review-val">${scarcity}</span></div>
            <div class="review-item"><span class="review-label">Women SHGs Count</span><span class="review-val">${shgs}</span></div>
            <div class="review-item"><span class="review-label">Active FPOs</span><span class="review-val">${fpos}</span></div>
          </div>
        </div>
      `;
    },

    submitForm: function() {
      const submitBtn = document.getElementById('submitBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Submitting...';

      const form = document.getElementById('villageProfileForm');
      const formData = new FormData(form);
      const payload = {};

      formData.forEach((value, key) => {
        payload[key] = value;
      });

      // Handle checkboxes explicitly
      const checkboxes = [
        'has_primary_school', 'has_secondary_school', 'has_primary_health_center',
        'has_veterinary_clinic', 'has_milk_chilling_center', 'has_custom_hiring_center',
        'has_bank_csc', 'all_weather_road_connectivity'
      ];
      checkboxes.forEach(cb => {
        const el = document.getElementById(cb);
        payload[cb] = el && el.checked ? 1 : 0;
      });

      payload.submit_now = true;

      fetch('/api/method/krushi_vikas.api.submit_village_profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': window.frappe ? window.frappe.csrf_token : ''
        },
        body: JSON.stringify({ data: payload })
      })
      .then(res => res.json())
      .then(res => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Save & Create Village Profile';

        if (res.message && res.message.success) {
          form.style.display = 'none';
          const successCard = document.getElementById('successCard');
          if (successCard) {
            successCard.style.display = 'block';
            document.getElementById('successTitle').textContent = 'Village Profile Created!';
            document.getElementById('successMsg').textContent = `Profile for ${res.message.village_name} (${res.message.name}) has been saved and registered successfully.`;
          }
        } else {
          alert('Submission Error: ' + (res.message || 'An error occurred during submission.'));
        }
      })
      .catch(err => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Save & Create Village Profile';
        console.error(err);
        alert('Network error while creating Village Profile.');
      });
    }
  };

  document.addEventListener('DOMContentLoaded', function() {
    window.VillageWizard.init();
  });
})();
