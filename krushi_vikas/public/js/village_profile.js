/**
 * Village Profile Wizard Interactive Controller
 * Copyright (c) 2026, Krushi Vikas and contributors
 */

(function() {
  'use strict';

  let currentStep = 1;
  const totalSteps = 4;

  function getCsrfToken() {
    if (window.csrf_token && window.csrf_token !== 'None' && window.csrf_token !== '') {
      return window.csrf_token;
    }
    if (window.frappe && window.frappe.csrf_token && window.frappe.csrf_token !== 'None' && window.frappe.csrf_token !== '') {
      return window.frappe.csrf_token;
    }
    const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
    if (match && match[1] && match[1] !== 'None') {
      return decodeURIComponent(match[1]);
    }
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content && meta.content !== 'None') {
      return meta.content;
    }
    return '';
  }

  function escapeHtml(text) {
    if (!text) return '-';
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  window.VillageWizard = {
    init: function() {
      this.setupAutoCalculations();
      this.updateStepperUI();
    },

    setupAutoCalculations: function() {
      const totalGeo = document.getElementById('total_geographical_area_ha');
      const cultLand = document.getElementById('cultivable_land_ha');
      const irriLand = document.getElementById('irrigated_area_ha');
      const rainfedLand = document.getElementById('rainfed_area_ha');
      const wasteLand = document.getElementById('forest_wasteland_ha');

      const calcLand = function() {
        const total = parseFloat(totalGeo ? totalGeo.value : 0) || 0;
        const cult = parseFloat(cultLand ? cultLand.value : 0) || 0;
        const irri = parseFloat(irriLand ? irriLand.value : 0) || 0;

        if (cult > 0 && irri >= 0 && rainfedLand && (!rainfedLand.value || rainfedLand.dataset.auto === "1")) {
          const autoRainfed = Math.max(0, cult - irri);
          rainfedLand.value = autoRainfed.toFixed(1);
          rainfedLand.dataset.auto = "1";
        }

        if (total > 0 && cult > 0 && wasteLand && (!wasteLand.value || wasteLand.dataset.auto === "1")) {
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
      if (targetStep < 1 || targetStep > totalSteps) return;

      // If progressing forward, validate current step
      if (targetStep > currentStep) {
        if (!this.validateStep(currentStep)) {
          return;
        }
      }

      currentStep = targetStep;
      this.updateStepperUI();

      if (currentStep === 4) {
        this.renderReviewSummary();
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    updateStepperUI: function() {
      for (let i = 1; i <= totalSteps; i++) {
        const panel = document.getElementById(`stepPanel${i}`);
        const navItem = document.getElementById(`stepNavItem${i}`);
        const badge = document.getElementById(`stepBadge${i}`);

        if (panel) {
          if (i === currentStep) {
            panel.classList.add('active');
          } else {
            panel.classList.remove('active');
          }
        }

        if (navItem && badge) {
          navItem.classList.remove('active', 'completed');
          if (i === currentStep) {
            navItem.classList.add('active');
            badge.innerHTML = i;
          } else if (i < currentStep) {
            navItem.classList.add('completed');
            badge.innerHTML = '<i class="fa-solid fa-check"></i>';
          } else {
            badge.innerHTML = i;
          }
        }
      }
    },

    validateStep: function(step) {
      let isValid = true;
      let firstInvalidEl = null;

      const markInvalid = function(id, msg) {
        const el = document.getElementById(id);
        if (el) {
          el.style.borderColor = '#ef4444';
          el.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.15)';
          if (!firstInvalidEl) firstInvalidEl = el;
          isValid = false;
        }
      };

      // Reset styles
      document.querySelectorAll('.form-control, .form-select').forEach(el => {
        el.style.borderColor = '';
        el.style.boxShadow = '';
      });

      if (step === 1) {
        const vName = document.getElementById('village_name');
        const taluka = document.getElementById('block_taluka');
        const district = document.getElementById('district');
        const pop = document.getElementById('total_population');
        const hh = document.getElementById('total_households');

        if (!vName || !vName.value.trim()) markInvalid('village_name');
        if (!taluka || !taluka.value.trim()) markInvalid('block_taluka');
        if (!district || !district.value.trim()) markInvalid('district');
        if (!pop || !pop.value.trim() || parseInt(pop.value, 10) <= 0) markInvalid('total_population');
        if (!hh || !hh.value.trim() || parseInt(hh.value, 10) <= 0) markInvalid('total_households');

      } else if (step === 2) {
        const totalGeo = document.getElementById('total_geographical_area_ha');
        const cultLand = document.getElementById('cultivable_land_ha');

        if (!totalGeo || !totalGeo.value.trim() || parseFloat(totalGeo.value) <= 0) markInvalid('total_geographical_area_ha');
        if (!cultLand || !cultLand.value.trim() || parseFloat(cultLand.value) <= 0) markInvalid('cultivable_land_ha');
      }

      if (!isValid) {
        if (firstInvalidEl) {
          firstInvalidEl.focus();
          firstInvalidEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        alert('Please fill in all required fields highlighted in red before proceeding.');
      }

      return isValid;
    },

    renderReviewSummary: function() {
      const container = document.getElementById('villageReviewGrid');
      if (!container) return;

      const getVal = (id, fallback = '-') => {
        const el = document.getElementById(id);
        if (!el) return fallback;
        if (el.tagName === 'SELECT' && el.selectedIndex >= 0) {
          return el.options[el.selectedIndex].text || fallback;
        }
        return el.value.trim() || fallback;
      };

      const getChecked = (id, label) => {
        const el = document.getElementById(id);
        return el && el.checked ? label : null;
      };

      const amenities = [
        getChecked('has_primary_school', 'Primary School'),
        getChecked('has_secondary_school', 'Secondary School'),
        getChecked('has_primary_health_center', 'PHC Health Center'),
        getChecked('has_veterinary_clinic', 'Veterinary Clinic'),
        getChecked('has_milk_chilling_center', 'Milk Chilling Center'),
        getChecked('has_custom_hiring_center', 'Custom Hiring Center'),
        getChecked('has_bank_csc', 'Bank / CSC'),
        getChecked('all_weather_road_connectivity', 'Tar Road Connected')
      ].filter(Boolean);

      container.innerHTML = `
        <div class="review-card">
          <div class="review-card-header">
            <h4><i class="fa-solid fa-location-dot" style="color:#2563eb;"></i> 1. Location & Demographics</h4>
            <button type="button" class="btn-review-edit" onclick="window.VillageWizard.goToStep(1)">Edit</button>
          </div>
          <div class="review-item-list">
            <div class="review-row"><span class="review-lbl">Village Name:</span><span class="review-val">${escapeHtml(getVal('village_name'))} (${escapeHtml(getVal('gram_panchayat'))})</span></div>
            <div class="review-row"><span class="review-lbl">Taluka / District:</span><span class="review-val">${escapeHtml(getVal('block_taluka'))}, ${escapeHtml(getVal('district'))}</span></div>
            <div class="review-row"><span class="review-lbl">Pincode / GPS:</span><span class="review-val">${escapeHtml(getVal('pincode'))} | ${escapeHtml(getVal('geo_coordinates'))}</span></div>
            <div class="review-row"><span class="review-lbl">Total Population:</span><span class="review-val">${escapeHtml(getVal('total_population'))} (${escapeHtml(getVal('male_population'))} M / ${escapeHtml(getVal('female_population'))} F)</span></div>
            <div class="review-row"><span class="review-lbl">Total Households:</span><span class="review-val">${escapeHtml(getVal('total_households'))} (SC: ${escapeHtml(getVal('sc_households'))}, ST: ${escapeHtml(getVal('st_households'))})</span></div>
            <div class="review-row"><span class="review-lbl">BPL / Women Headed:</span><span class="review-val">${escapeHtml(getVal('bpl_households'))} BPL / ${escapeHtml(getVal('female_headed_households'))} Women-headed</span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4><i class="fa-solid fa-wheat-awn" style="color:#2563eb;"></i> 2. Land & Agriculture</h4>
            <button type="button" class="btn-review-edit" onclick="window.VillageWizard.goToStep(2)">Edit</button>
          </div>
          <div class="review-item-list">
            <div class="review-row"><span class="review-lbl">Total Geographical Area:</span><span class="review-val">${escapeHtml(getVal('total_geographical_area_ha'))} Ha</span></div>
            <div class="review-row"><span class="review-lbl">Cultivable Land:</span><span class="review-val">${escapeHtml(getVal('cultivable_land_ha'))} Ha</span></div>
            <div class="review-row"><span class="review-lbl">Irrigated / Rainfed:</span><span class="review-val">${escapeHtml(getVal('irrigated_area_ha'))} Ha / ${escapeHtml(getVal('rainfed_area_ha'))} Ha</span></div>
            <div class="review-row"><span class="review-lbl">Dominant Soil Type:</span><span class="review-val">${escapeHtml(getVal('soil_type'))}</span></div>
            <div class="review-row"><span class="review-lbl">Major Kharif Crops:</span><span class="review-val">${escapeHtml(getVal('major_crops_kharif'))}</span></div>
            <div class="review-row"><span class="review-lbl">Major Rabi Crops:</span><span class="review-val">${escapeHtml(getVal('major_crops_rabi'))}</span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4><i class="fa-solid fa-droplet" style="color:#2563eb;"></i> 3. Water & Infrastructure</h4>
            <button type="button" class="btn-review-edit" onclick="window.VillageWizard.goToStep(3)">Edit</button>
          </div>
          <div class="review-item-list">
            <div class="review-row"><span class="review-lbl">Watershed Basin:</span><span class="review-val">${escapeHtml(getVal('watershed_name'))}</span></div>
            <div class="review-row"><span class="review-lbl">Drinking Water Source:</span><span class="review-val">${escapeHtml(getVal('primary_drinking_water_source'))}</span></div>
            <div class="review-row"><span class="review-lbl">Summer Water Scarcity:</span><span class="review-val">${escapeHtml(getVal('summer_water_scarcity_status'))}</span></div>
            <div class="review-row"><span class="review-lbl">Water Structures:</span><span class="review-val">${escapeHtml(getVal('open_wells_count'))} Wells, ${escapeHtml(getVal('borewells_count'))} Borewells, ${escapeHtml(getVal('check_dams_count'))} Dams</span></div>
            <div class="review-row"><span class="review-lbl">SHGs & FPOs:</span><span class="review-val">${escapeHtml(getVal('total_shgs_count'))} SHGs | ${escapeHtml(getVal('active_fpos_count'))} FPOs</span></div>
            <div class="review-row"><span class="review-lbl">Facilities Available:</span><span class="review-val">${amenities.length > 0 ? amenities.join(', ') : 'None selected'}</span></div>
          </div>
        </div>
      `;
    },

    submitForm: function() {
      const consentBox = document.getElementById('confirmation_consent');
      if (consentBox && !consentBox.checked) {
        alert('Please accept the verification statement before submitting.');
        consentBox.focus();
        return;
      }

      const submitBtn = document.getElementById('submitBtn');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registering Profile...';
      }

      const form = document.getElementById('villageProfileForm');
      const formData = new FormData(form);
      const payload = {};

      formData.forEach((val, key) => {
        payload[key] = val;
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
      const csrf = getCsrfToken();
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };
      if (csrf) {
        headers['X-Frappe-CSRF-Token'] = csrf;
        payload['csrf_token'] = csrf;
      }

      fetch('/api/method/krushi_vikas.api.submit_village_profile', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ data: payload })
      })
      .then(res => res.json())
      .then(res => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-check"></i> Save & Register Village Profile';
        }

        if (res.message && res.message.success) {
          form.style.display = 'none';
          const successScreen = document.getElementById('successScreen');
          if (successScreen) {
            successScreen.style.display = 'block';
            document.getElementById('successTitle').textContent = 'Village Profile Registered!';
            document.getElementById('successMsg').textContent = `Profile for ${res.message.village_name} (${res.message.name}) has been saved and verified successfully.`;
            document.getElementById('successRefPill').textContent = `Profile ID: ${res.message.name}`;
          }
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          const err = res.exc || res._server_messages || res.message || 'Submission failed.';
          alert('Submission Error: ' + JSON.stringify(err));
        }
      })
      .catch(err => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-check"></i> Save & Register Village Profile';
        }
        console.error(err);
        alert('Network error while registering Village Profile: ' + err.message);
      });
    }
  };

  document.addEventListener('DOMContentLoaded', function() {
    window.VillageWizard.init();
  });
})();
