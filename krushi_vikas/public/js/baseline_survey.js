/**
 * Farmer Baseline Survey Interactive Stepper & Multi-Table Engine
 * Copyright (c) 2026, Krushi Vikas and contributors
 */

(function() {
  'use strict';

  let currentStep = 1;
  const totalSteps = 4;

  window.BaselineWizard = {
    init: function() {
      this.bindEvents();
      this.setupAutoCalculations();
      this.populateDefaultRows();
    },

    bindEvents: function() {
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

    populateDefaultRows: function() {
      // Step 1: Default Household Member (Self)
      this.addMemberRow({ name: '', rel: 'Self', gen: 'Male', age: '42', occ: 'Farming' });

      // Step 2: Default Crops (Soybean, Wheat)
      this.addCropRow({ season: 'Kharif', crop: 'Soybean', area: '2.5', yield: '18.0', income: '85000' });
      this.addCropRow({ season: 'Rabi', crop: 'Wheat', area: '1.5', yield: '15.0', income: '45000' });

      // Step 3: Default Livestock & Equipment
      this.addLivestockRow({ animal: 'Indigenous Cow', qty: '2', milk: '6.0', income: '36000' });
      this.addAssetRow({ asset: 'Electric Pump', qty: '1', status: 'Working / Operational' });
      this.addIncomeRow({ source: 'Crop Agriculture', amount: '130000' });
      this.addIncomeRow({ source: 'Livestock / Dairy', amount: '36000' });
    },

    setupAutoCalculations: function() {
      const totalLand = document.getElementById('total_landholding_acres');
      const irriLand = document.getElementById('irrigated_land_acres');
      const rainfedLand = document.getElementById('rainfed_land_acres');

      const calcRainfed = function() {
        const total = parseFloat(totalLand.value) || 0;
        const irri = parseFloat(irriLand.value) || 0;

        if (total > 0 && irri >= 0 && (!rainfedLand.value || rainfedLand.dataset.auto === "1")) {
          const autoRainfed = Math.max(0, total - irri);
          rainfedLand.value = autoRainfed.toFixed(1);
          rainfedLand.dataset.auto = "1";
        }
      };

      if (totalLand && irriLand) {
        totalLand.addEventListener('input', calcRainfed);
        irriLand.addEventListener('input', calcRainfed);
      }
    },

    /* --- Dynamic Row Adders --- */

    addMemberRow: function(data = {}) {
      const tbody = document.querySelector('#tableHouseholdMembers tbody');
      if (!tbody) return;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="text" class="member-name" value="${data.name || ''}" placeholder="Name"></td>
        <td>
          <select class="member-rel">
            <option value="Self" ${data.rel === 'Self' ? 'selected' : ''}>Self</option>
            <option value="Spouse" ${data.rel === 'Spouse' ? 'selected' : ''}>Spouse</option>
            <option value="Son" ${data.rel === 'Son' ? 'selected' : ''}>Son</option>
            <option value="Daughter" ${data.rel === 'Daughter' ? 'selected' : ''}>Daughter</option>
            <option value="Father" ${data.rel === 'Father' ? 'selected' : ''}>Father</option>
            <option value="Mother" ${data.rel === 'Mother' ? 'selected' : ''}>Mother</option>
            <option value="Other" ${data.rel === 'Other' ? 'selected' : ''}>Other</option>
          </select>
        </td>
        <td>
          <select class="member-gen">
            <option value="Male" ${data.gen === 'Male' ? 'selected' : ''}>Male</option>
            <option value="Female" ${data.gen === 'Female' ? 'selected' : ''}>Female</option>
            <option value="Other" ${data.gen === 'Other' ? 'selected' : ''}>Other</option>
          </select>
        </td>
        <td><input type="number" class="member-age" value="${data.age || ''}" placeholder="Age" min="1"></td>
        <td>
          <select class="member-occ">
            <option value="Farming">Farming</option>
            <option value="Agri Labour">Agri Labour</option>
            <option value="Wage Labour / Migration">Wage Labour</option>
            <option value="Housewife">Housewife</option>
            <option value="Student">Student</option>
            <option value="Service">Service</option>
          </select>
        </td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-row" onclick="this.closest('tr').remove(); window.BaselineWizard.updateMemberCount();">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
      this.updateMemberCount();
    },

    updateMemberCount: function() {
      const rows = document.querySelectorAll('#tableHouseholdMembers tbody tr');
      const countInput = document.getElementById('household_members');
      if (countInput && rows.length > 0) {
        countInput.value = rows.length;
      }
    },

    addCropRow: function(data = {}) {
      const tbody = document.querySelector('#tableCrops tbody');
      if (!tbody) return;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="crop-season">
            <option value="Kharif" ${data.season === 'Kharif' ? 'selected' : ''}>Kharif</option>
            <option value="Rabi" ${data.season === 'Rabi' ? 'selected' : ''}>Rabi</option>
            <option value="Summer" ${data.season === 'Summer' ? 'selected' : ''}>Summer</option>
            <option value="Perennial / Annual" ${data.season === 'Perennial / Annual' ? 'selected' : ''}>Perennial</option>
          </select>
        </td>
        <td><input type="text" class="crop-name" value="${data.crop || ''}" placeholder="Crop e.g. Soybean"></td>
        <td><input type="number" class="crop-area" value="${data.area || '1.0'}" step="0.1" min="0.1" placeholder="Acres"></td>
        <td><input type="number" class="crop-yield" value="${data.yield || '0'}" step="0.1" placeholder="Quintals"></td>
        <td><input type="number" class="crop-income" value="${data.income || '0'}" step="500" placeholder="₹ Gross"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-row" onclick="this.closest('tr').remove()">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    addLivestockRow: function(data = {}) {
      const tbody = document.querySelector('#tableLivestock tbody');
      if (!tbody) return;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="ls-animal">
            <option value="Indigenous Cow" ${data.animal === 'Indigenous Cow' ? 'selected' : ''}>Indigenous Cow</option>
            <option value="Crossbreed Cow" ${data.animal === 'Crossbreed Cow' ? 'selected' : ''}>Crossbreed Cow</option>
            <option value="Buffalo" ${data.animal === 'Buffalo' ? 'selected' : ''}>Buffalo</option>
            <option value="Bullock / Draught Animal" ${data.animal === 'Bullock / Draught Animal' ? 'selected' : ''}>Bullock</option>
            <option value="Goat / Sheep" ${data.animal === 'Goat / Sheep' ? 'selected' : ''}>Goat / Sheep</option>
            <option value="Poultry / Birds" ${data.animal === 'Poultry / Birds' ? 'selected' : ''}>Poultry</option>
          </select>
        </td>
        <td><input type="number" class="ls-qty" value="${data.qty || '1'}" min="1"></td>
        <td><input type="number" class="ls-milk" value="${data.milk || '0'}" step="0.5"></td>
        <td><input type="number" class="ls-income" value="${data.income || '0'}" step="1000"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-row" onclick="this.closest('tr').remove()">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    addAssetRow: function(data = {}) {
      const tbody = document.querySelector('#tableAssets tbody');
      if (!tbody) return;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="asset-name">
            <option value="Tractor" ${data.asset === 'Tractor' ? 'selected' : ''}>Tractor</option>
            <option value="Power Tiller" ${data.asset === 'Power Tiller' ? 'selected' : ''}>Power Tiller</option>
            <option value="Electric Pump" ${data.asset === 'Electric Pump' ? 'selected' : ''}>Electric Pump</option>
            <option value="Diesel / Solar Pump" ${data.asset === 'Diesel / Solar Pump' ? 'selected' : ''}>Solar / Diesel Pump</option>
            <option value="Drip Irrigation System" ${data.asset === 'Drip Irrigation System' ? 'selected' : ''}>Drip Irrigation System</option>
            <option value="Sprinkler System" ${data.asset === 'Sprinkler System' ? 'selected' : ''}>Sprinkler System</option>
            <option value="Farm Pond" ${data.asset === 'Farm Pond' ? 'selected' : ''}>Farm Pond</option>
            <option value="Spray Pump" ${data.asset === 'Spray Pump' ? 'selected' : ''}>Spray Pump</option>
          </select>
        </td>
        <td><input type="number" class="asset-qty" value="${data.qty || '1'}" min="1"></td>
        <td>
          <select class="asset-status">
            <option value="Working / Operational" ${data.status === 'Working / Operational' ? 'selected' : ''}>Working</option>
            <option value="Needs Repair" ${data.status === 'Needs Repair' ? 'selected' : ''}>Needs Repair</option>
            <option value="Non-Functional" ${data.status === 'Non-Functional' ? 'selected' : ''}>Non-Functional</option>
          </select>
        </td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-row" onclick="this.closest('tr').remove()">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    addIncomeRow: function(data = {}) {
      const tbody = document.querySelector('#tableIncomeSources tbody');
      if (!tbody) return;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="inc-source">
            <option value="Crop Agriculture" ${data.source === 'Crop Agriculture' ? 'selected' : ''}>Crop Agriculture</option>
            <option value="Horticulture / Fruits" ${data.source === 'Horticulture / Fruits' ? 'selected' : ''}>Horticulture / Fruits</option>
            <option value="Livestock / Dairy" ${data.source === 'Livestock / Dairy' ? 'selected' : ''}>Livestock / Dairy</option>
            <option value="Poultry" ${data.source === 'Poultry' ? 'selected' : ''}>Poultry</option>
            <option value="Agricultural Labour" ${data.source === 'Agricultural Labour' ? 'selected' : ''}>Agricultural Labour</option>
            <option value="Non-Farm Daily Wages" ${data.source === 'Non-Farm Daily Wages' ? 'selected' : ''}>Non-Farm Daily Wages</option>
            <option value="Rural Business / Shop" ${data.source === 'Rural Business / Shop' ? 'selected' : ''}>Rural Business / Shop</option>
            <option value="Salary / Service" ${data.source === 'Salary / Service' ? 'selected' : ''}>Salary / Service</option>
            <option value="Remittance / Family Support" ${data.source === 'Remittance / Family Support' ? 'selected' : ''}>Family Remittance</option>
          </select>
        </td>
        <td><input type="number" class="inc-amount" value="${data.amount || '0'}" step="1000"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-row" onclick="this.closest('tr').remove()">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    /* --- Stepper Navigation & Validations --- */

    goToStep: function(targetStep) {
      if (targetStep > currentStep) {
        if (!this.validateStep(currentStep)) {
          return;
        }
      }

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
        const farmer = document.getElementById('farmer_name').value.trim();
        const village = document.getElementById('village').value;
        const surveyDate = document.getElementById('survey_date').value;
        const category = document.getElementById('farmer_category').value;

        if (!farmer) markError('farmer_name', 'Farmer name is required.');
        if (!village) markError('village', 'Please select a village.');
        if (!surveyDate) {
          markError('survey_date', 'Survey date is required.');
        } else {
          const today = new Date().toISOString().split('T')[0];
          if (surveyDate > today) {
            markError('survey_date', 'Survey date cannot be in the future.');
          }
        }
        if (!category) markError('farmer_category', 'Please select landholding category.');
      }

      if (step === 2) {
        const total = parseFloat(document.getElementById('total_landholding_acres').value);
        const irri = parseFloat(document.getElementById('irrigated_land_acres').value) || 0;
        const rainfed = parseFloat(document.getElementById('rainfed_land_acres').value) || 0;

        if (isNaN(total) || total <= 0) {
          markError('total_landholding_acres', 'Total landholding is required.');
        } else if ((irri + rainfed) > (total + 0.05)) {
          markError('irrigated_land_acres', 'Sum of irrigated and rainfed land cannot exceed total landholding.');
        }
      }

      if (step === 3) {
        const practice = document.getElementById('fertilizer_practice').value;
        const scarcity = document.getElementById('summer_water_scarcity').value;

        if (!practice) markError('fertilizer_practice', 'Please select fertilizer practice.');
        if (!scarcity) markError('summer_water_scarcity', 'Please select summer water scarcity level.');
      }

      return isValid;
    },

    renderReviewSummary: function() {
      const container = document.getElementById('reviewCardsContainer');
      if (!container) return;

      const getVal = id => {
        const el = document.getElementById(id);
        if (!el) return '-';
        if (el.tagName === 'SELECT' && el.selectedIndex >= 0) {
          return el.options[el.selectedIndex].text;
        }
        return el.value.trim() || '-';
      };

      const farmer = getVal('farmer_name');
      const village = getVal('village');
      const date = getVal('survey_date');
      const officer = getVal('field_officer');
      const category = getVal('farmer_category');
      const totalLand = getVal('total_landholding_acres');
      const irrigated = getVal('irrigated_land_acres');
      const rainfed = getVal('rainfed_land_acres');
      const irrigationSrc = getVal('primary_irrigation_source');
      const fertilizer = getVal('fertilizer_practice');
      const scarcity = getVal('summer_water_scarcity');

      // Count table rows
      const memberCount = document.querySelectorAll('#tableHouseholdMembers tbody tr').length;
      const cropCount = document.querySelectorAll('#tableCrops tbody tr').length;
      const livestockCount = document.querySelectorAll('#tableLivestock tbody tr').length;
      const assetCount = document.querySelectorAll('#tableAssets tbody tr').length;
      const incomeCount = document.querySelectorAll('#tableIncomeSources tbody tr').length;

      container.innerHTML = `
        <div class="review-card">
          <div class="review-card-header">
            <h4>1. Farmer Identification & Family Members</h4>
            <button type="button" class="btn-link" onclick="window.BaselineWizard.goToStep(1)">Edit</button>
          </div>
          <div class="review-grid">
            <div class="review-item"><span class="review-label">Farmer Name</span><span class="review-val">${farmer}</span></div>
            <div class="review-item"><span class="review-label">Village</span><span class="review-val">${village}</span></div>
            <div class="review-item"><span class="review-label">Survey Date</span><span class="review-val">${date}</span></div>
            <div class="review-item"><span class="review-label">Field Officer</span><span class="review-val">${officer}</span></div>
            <div class="review-item"><span class="review-label">Category</span><span class="review-val">${category}</span></div>
            <div class="review-item"><span class="review-label">Family Members Listed</span><span class="review-val"><strong>${memberCount} members</strong></span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4>2. Land & Cropping Table</h4>
            <button type="button" class="btn-link" onclick="window.BaselineWizard.goToStep(2)">Edit</button>
          </div>
          <div class="review-grid">
            <div class="review-item"><span class="review-label">Total Land</span><span class="review-val">${totalLand} Acres</span></div>
            <div class="review-item"><span class="review-label">Irrigated / Rainfed</span><span class="review-val">${irrigated} Ac / ${rainfed} Ac</span></div>
            <div class="review-item"><span class="review-label">Irrigation Source</span><span class="review-val">${irrigationSrc}</span></div>
            <div class="review-item"><span class="review-label">Seasonal Crops Listed</span><span class="review-val"><strong>${cropCount} crops</strong></span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4>3. Livestock, Assets & Income Breakdown</h4>
            <button type="button" class="btn-link" onclick="window.BaselineWizard.goToStep(3)">Edit</button>
          </div>
          <div class="review-grid">
            <div class="review-item"><span class="review-label">Nutrient Practice</span><span class="review-val">${fertilizer}</span></div>
            <div class="review-item"><span class="review-label">Summer Water Status</span><span class="review-val">${scarcity}</span></div>
            <div class="review-item"><span class="review-label">Livestock Listed</span><span class="review-val">${livestockCount} species</span></div>
            <div class="review-item"><span class="review-label">Farm Assets Listed</span><span class="review-val">${assetCount} implements</span></div>
            <div class="review-item"><span class="review-label">Income Sources</span><span class="review-val">${incomeCount} channels</span></div>
          </div>
        </div>
      `;
    },

    submitForm: function() {
      const consentBox = document.getElementById('confirmation_consent');
      const errConsent = document.getElementById('err-confirmation_consent');

      if (!consentBox.checked) {
        if (errConsent) errConsent.textContent = 'Please confirm informed consent before submitting.';
        return;
      }

      const submitBtn = document.getElementById('submitBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Submitting...';

      const form = document.getElementById('baselineSurveyForm');
      const formData = new FormData(form);
      const payload = {};

      formData.forEach((value, key) => {
        payload[key] = value;
      });

      payload.confirmation_consent = consentBox.checked ? 1 : 0;
      payload.submit_now = true;

      // Collect Child Tables Data
      payload.household_members_table = [];
      document.querySelectorAll('#tableHouseholdMembers tbody tr').forEach(tr => {
        const name = tr.querySelector('.member-name') ? tr.querySelector('.member-name').value.trim() : '';
        if (name) {
          payload.household_members_table.push({
            member_name: name,
            relation: tr.querySelector('.member-rel') ? tr.querySelector('.member-rel').value : 'Self',
            gender: tr.querySelector('.member-gen') ? tr.querySelector('.member-gen').value : 'Male',
            age: tr.querySelector('.member-age') ? parseInt(tr.querySelector('.member-age').value || 0) : null,
            primary_occupation: tr.querySelector('.member-occ') ? tr.querySelector('.member-occ').value : 'Farming'
          });
        }
      });

      payload.crops_table = [];
      document.querySelectorAll('#tableCrops tbody tr').forEach(tr => {
        const crop = tr.querySelector('.crop-name') ? tr.querySelector('.crop-name').value.trim() : '';
        if (crop) {
          payload.crops_table.push({
            season: tr.querySelector('.crop-season') ? tr.querySelector('.crop-season').value : 'Kharif',
            crop_name: crop,
            area_acres: tr.querySelector('.crop-area') ? parseFloat(tr.querySelector('.crop-area').value || 1.0) : 1.0,
            production_quintals: tr.querySelector('.crop-yield') ? parseFloat(tr.querySelector('.crop-yield').value || 0) : 0,
            gross_income: tr.querySelector('.crop-income') ? parseFloat(tr.querySelector('.crop-income').value || 0) : 0
          });
        }
      });

      payload.livestock_table = [];
      document.querySelectorAll('#tableLivestock tbody tr').forEach(tr => {
        const animal = tr.querySelector('.ls-animal') ? tr.querySelector('.ls-animal').value : '';
        if (animal) {
          payload.livestock_table.push({
            animal_type: animal,
            quantity: tr.querySelector('.ls-qty') ? parseInt(tr.querySelector('.ls-qty').value || 1) : 1,
            daily_milk_litres: tr.querySelector('.ls-milk') ? parseFloat(tr.querySelector('.ls-milk').value || 0) : 0,
            annual_livestock_income: tr.querySelector('.ls-income') ? parseFloat(tr.querySelector('.ls-income').value || 0) : 0
          });
        }
      });

      payload.farm_assets_table = [];
      document.querySelectorAll('#tableAssets tbody tr').forEach(tr => {
        const asset = tr.querySelector('.asset-name') ? tr.querySelector('.asset-name').value : '';
        if (asset) {
          payload.farm_assets_table.push({
            asset_name: asset,
            quantity: tr.querySelector('.asset-qty') ? parseInt(tr.querySelector('.asset-qty').value || 1) : 1,
            operational_status: tr.querySelector('.asset-status') ? tr.querySelector('.asset-status').value : 'Working / Operational'
          });
        }
      });

      payload.income_sources_table = [];
      document.querySelectorAll('#tableIncomeSources tbody tr').forEach(tr => {
        const source = tr.querySelector('.inc-source') ? tr.querySelector('.inc-source').value : '';
        const amount = tr.querySelector('.inc-amount') ? parseFloat(tr.querySelector('.inc-amount').value || 0) : 0;
        if (source && amount > 0) {
          payload.income_sources_table.push({
            source_type: source,
            annual_amount: amount
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

      const csrf = getCsrfToken();
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };
      if (csrf) {
        headers['X-Frappe-CSRF-Token'] = csrf;
        payload['csrf_token'] = csrf;
      }

      fetch('/api/method/krushi_vikas.api.submit_baseline_survey', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ data: payload })
      })
      .then(res => res.json())
      .then(res => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit Baseline Survey';

        if (res.message && res.message.success) {
          form.style.display = 'none';
          const successCard = document.getElementById('successCard');
          if (successCard) {
            successCard.style.display = 'block';
            document.getElementById('successTitle').textContent = 'Baseline Survey Recorded!';
            document.getElementById('successMsg').textContent = `Baseline record ${res.message.name} for ${payload.farmer_name} with all child tables has been submitted successfully.`;
          }
        } else {
          alert('Submission Error: ' + (res.message || 'An error occurred during submission.'));
        }
      })
      .catch(err => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit Baseline Survey';
        console.error(err);
        alert('Network error while recording Baseline Survey.');
      });
    }
  };

  document.addEventListener('DOMContentLoaded', function() {
    window.BaselineWizard.init();
  });
})();
