/**
 * Baseline Survey Wizard Interactive Controller
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

  window.BaselineWizard = {
    init: function() {
      this.populateDefaultRows();
      this.updateStepperUI();
    },

    populateDefaultRows: function() {
      // Step 1: Default Household Members
      this.addHouseholdMemberRow({ name: "Ramesh Tukaram Patil", relation: "Self", gender: "Male", age: 45, education: "Secondary [9-10]", occupation: "Agriculture" });
      this.addHouseholdMemberRow({ name: "Sunita Ramesh Patil", relation: "Spouse", gender: "Female", age: 40, education: "Primary [1-5]", occupation: "Livestock / Dairy" });
      this.addHouseholdMemberRow({ name: "Amol Ramesh Patil", relation: "Son", gender: "Male", age: 18, education: "Higher Secondary [11-12]", occupation: "Student" });

      // Step 2: Default Crops
      this.addCropRow({ season: "Kharif", name: "Cotton (Bt)", irri: 2.0, dry: 0.0, yield: 18, cost: 28000, income: 72000 });
      this.addCropRow({ season: "Kharif", name: "Soybean (JS-335)", irri: 0.0, dry: 2.5, yield: 15, cost: 16000, income: 54000 });

      // Step 2: Default Irrigation Source & Equipment
      this.addIrrigationSourceRow({ source: "Open Well", qty: 1, depth: 45, months: 8 });
      this.addConservationWorkRow({ structure: "Farm Bunding (Matichya Bandhi)", status: "Yes", length: "400 meters", dept: "Agriculture Dept" });

      // Step 3: Default Livestock, Assets, Loans
      this.addLivestockRow({ animal: "Crossbreed Cow", qty: 2, milk: 12, income: 85000 });
      this.addLivestockRow({ animal: "Bullock (Pair)", qty: 2, milk: 0, income: 0 });

      this.addAssetRow({ asset: "Electric Submersible Pump (5 HP)", qty: 1, status: "Working / Operational" });
      this.addAssetRow({ asset: "Battery Knapsack Sprayer", qty: 2, status: "Working / Operational" });

      this.addLoanRow({ source: "PACS / Primary Agri Society", amount: 45000, purpose: "Crop Inputs (Seeds & Fertilizer)", outstanding: 20000 });
    },

    toggleMigrationFields: function(val) {
      const row = document.getElementById('migrationFieldsRow');
      if (row) {
        row.style.display = (val === 'Yes') ? 'grid' : 'none';
      }
    },

    toggleShgFields: function(val) {
      document.querySelectorAll('.shg-dep').forEach(el => {
        el.style.display = (val === 'Yes') ? (el.classList.contains('form-grid-2') ? 'grid' : 'flex') : 'none';
      });
    },

    // 1. Household Members Row
    addHouseholdMemberRow: function(data = {}) {
      const tbody = document.querySelector('#tableHouseholdMembers tbody');
      if (!tbody) return;

      const tr = document.createElement('tr');
      tr.className = 'member-row';
      tr.innerHTML = `
        <td><input type="text" class="form-control m-name" value="${escapeHtml(data.name || '')}" placeholder="Member name" required></td>
        <td>
          <select class="form-select m-rel">
            <option value="Self" ${data.relation === 'Self' ? 'selected' : ''}>Self</option>
            <option value="Spouse" ${data.relation === 'Spouse' ? 'selected' : ''}>Spouse</option>
            <option value="Son" ${data.relation === 'Son' ? 'selected' : ''}>Son</option>
            <option value="Daughter" ${data.relation === 'Daughter' ? 'selected' : ''}>Daughter</option>
            <option value="Father" ${data.relation === 'Father' ? 'selected' : ''}>Father</option>
            <option value="Mother" ${data.relation === 'Mother' ? 'selected' : ''}>Mother</option>
            <option value="Brother" ${data.relation === 'Brother' ? 'selected' : ''}>Brother</option>
            <option value="Other" ${data.relation === 'Other' ? 'selected' : ''}>Other</option>
          </select>
        </td>
        <td>
          <select class="form-select m-gen">
            <option value="Male" ${data.gender === 'Male' ? 'selected' : ''}>Male</option>
            <option value="Female" ${data.gender === 'Female' ? 'selected' : ''}>Female</option>
            <option value="Other" ${data.gender === 'Other' ? 'selected' : ''}>Other</option>
          </select>
        </td>
        <td><input type="number" class="form-control m-age" value="${data.age || ''}" placeholder="Age" min="0" max="110"></td>
        <td>
          <select class="form-select m-edu">
            <option value="Illiterate" ${data.education === 'Illiterate' ? 'selected' : ''}>Illiterate</option>
            <option value="Primary [1-5]" ${data.education === 'Primary [1-5]' ? 'selected' : ''}>Primary [1-5]</option>
            <option value="Upper Primary [6-8]" ${data.education === 'Upper Primary [6-8]' ? 'selected' : ''}>Upper Primary [6-8]</option>
            <option value="Secondary [9-10]" ${data.education === 'Secondary [9-10]' ? 'selected' : ''}>Secondary [9-10]</option>
            <option value="Higher Secondary [11-12]" ${data.education === 'Higher Secondary [11-12]' ? 'selected' : ''}>Higher Secondary [11-12]</option>
            <option value="Graduate / PG" ${data.education === 'Graduate / PG' ? 'selected' : ''}>Graduate / PG</option>
          </select>
        </td>
        <td>
          <select class="form-select m-occ">
            <option value="Agriculture" ${data.occupation === 'Agriculture' ? 'selected' : ''}>Agriculture</option>
            <option value="Agri Labour" ${data.occupation === 'Agri Labour' ? 'selected' : ''}>Agri Labour</option>
            <option value="Livestock / Dairy" ${data.occupation === 'Livestock / Dairy' ? 'selected' : ''}>Livestock / Dairy</option>
            <option value="Enterprise / Shop" ${data.occupation === 'Enterprise / Shop' ? 'selected' : ''}>Enterprise / Shop</option>
            <option value="Salaried Employee" ${data.occupation === 'Salaried Employee' ? 'selected' : ''}>Salaried Employee</option>
            <option value="Student" ${data.occupation === 'Student' ? 'selected' : ''}>Student</option>
            <option value="Dependent" ${data.occupation === 'Dependent' ? 'selected' : ''}>Dependent</option>
          </select>
        </td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-table-row" onclick="this.closest('tr').remove()" title="Delete row">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    // 2. Crop Production Row
    addCropRow: function(data = {}) {
      const tbody = document.querySelector('#tableCrops tbody');
      if (!tbody) return;

      const self = this;
      const tr = document.createElement('tr');
      tr.className = 'crop-row';
      tr.innerHTML = `
        <td>
          <select class="form-select c-season">
            <option value="Kharif" ${data.season === 'Kharif' ? 'selected' : ''}>Kharif</option>
            <option value="Rabi" ${data.season === 'Rabi' ? 'selected' : ''}>Rabi</option>
            <option value="Summer" ${data.season === 'Summer' ? 'selected' : ''}>Summer</option>
          </select>
        </td>
        <td><input type="text" class="form-control c-name" value="${escapeHtml(data.name || '')}" placeholder="e.g. Cotton (Bt)" required></td>
        <td><input type="number" class="form-control c-irri" value="${data.irri !== undefined ? data.irri : 0}" step="0.1" min="0"></td>
        <td><input type="number" class="form-control c-dry" value="${data.dry !== undefined ? data.dry : 0}" step="0.1" min="0"></td>
        <td><input type="number" class="form-control c-yield" value="${data.yield !== undefined ? data.yield : 0}" step="0.5" min="0"></td>
        <td><input type="number" class="form-control c-cost" value="${data.cost !== undefined ? data.cost : 0}" step="500" min="0"></td>
        <td><input type="number" class="form-control c-income" value="${data.income !== undefined ? data.income : 0}" step="500" min="0" oninput="window.BaselineWizard.recalcCropTotals()"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-table-row" onclick="this.closest('tr').remove(); window.BaselineWizard.recalcCropTotals();" title="Delete row">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
      this.recalcCropTotals();
    },

    recalcCropTotals: function() {
      let totalInc = 0;
      document.querySelectorAll('#tableCrops .c-income').forEach(el => {
        totalInc += parseFloat(el.value) || 0;
      });
      const disp = document.getElementById('totalCropIncome');
      if (disp) {
        disp.textContent = '₹' + totalInc.toLocaleString('en-IN');
      }
    },

    // 3. Irrigation Source Row
    addIrrigationSourceRow: function(data = {}) {
      const tbody = document.querySelector('#tableIrrigationSources tbody');
      if (!tbody) return;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="form-select ir-name">
            <option value="Open Well" ${data.source === 'Open Well' ? 'selected' : ''}>Open Well</option>
            <option value="Borewell" ${data.source === 'Borewell' ? 'selected' : ''}>Borewell</option>
            <option value="Farm Pond" ${data.source === 'Farm Pond' ? 'selected' : ''}>Farm Pond</option>
            <option value="Canal" ${data.source === 'Canal' ? 'selected' : ''}>Canal</option>
            <option value="River / Stream" ${data.source === 'River / Stream' ? 'selected' : ''}>River / Stream</option>
          </select>
        </td>
        <td><input type="number" class="form-control ir-qty" value="${data.qty || 1}" min="1"></td>
        <td><input type="number" class="form-control ir-depth" value="${data.depth || 40}" min="0" placeholder="Feet"></td>
        <td><input type="number" class="form-control ir-months" value="${data.months || 8}" min="1" max="12" placeholder="Months"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-table-row" onclick="this.closest('tr').remove()">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    // 4. Conservation Work Row
    addConservationWorkRow: function(data = {}) {
      const tbody = document.querySelector('#tableConservationWorks tbody');
      if (!tbody) return;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="form-select cw-type">
            <option value="Farm Bunding (Matichya Bandhi)" ${data.structure === 'Farm Bunding (Matichya Bandhi)' ? 'selected' : ''}>Farm Bunding (Matichya Bandhi)</option>
            <option value="Continuous Contour Trenches (CCT)" ${data.structure === 'Continuous Contour Trenches (CCT)' ? 'selected' : ''}>Continuous Contour Trenches (CCT)</option>
            <option value="Farm Pond (Shet Tale)" ${data.structure === 'Farm Pond (Shet Tale)' ? 'selected' : ''}>Farm Pond (Shet Tale)</option>
            <option value="Loose Boulder Structure" ${data.structure === 'Loose Boulder Structure' ? 'selected' : ''}>Loose Boulder Structure</option>
            <option value="Deep CCT" ${data.structure === 'Deep CCT' ? 'selected' : ''}>Deep CCT</option>
          </select>
        </td>
        <td>
          <select class="form-select cw-status">
            <option value="Yes" ${data.status === 'Yes' ? 'selected' : ''}>Yes</option>
            <option value="No" ${data.status === 'No' ? 'selected' : ''}>No</option>
          </select>
        </td>
        <td><input type="text" class="form-control cw-len" value="${data.length || '300 meters'}" placeholder="e.g. 300 m"></td>
        <td><input type="text" class="form-control cw-dept" value="${data.dept || 'Agriculture Dept'}" placeholder="e.g. Agri Dept"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-table-row" onclick="this.closest('tr').remove()">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    // 5. Livestock Row
    addLivestockRow: function(data = {}) {
      const tbody = document.querySelector('#tableLivestock tbody');
      if (!tbody) return;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="form-select ls-animal">
            <option value="Crossbreed Cow" ${data.animal === 'Crossbreed Cow' ? 'selected' : ''}>Crossbreed Cow</option>
            <option value="Indigenous Cow (Desi)" ${data.animal === 'Indigenous Cow (Desi)' ? 'selected' : ''}>Indigenous Cow (Desi)</option>
            <option value="Buffalo" ${data.animal === 'Buffalo' ? 'selected' : ''}>Buffalo</option>
            <option value="Bullock (Pair)" ${data.animal === 'Bullock (Pair)' ? 'selected' : ''}>Bullock (Pair)</option>
            <option value="Goat / Sheep" ${data.animal === 'Goat / Sheep' ? 'selected' : ''}>Goat / Sheep</option>
            <option value="Poultry Birds" ${data.animal === 'Poultry Birds' ? 'selected' : ''}>Poultry Birds</option>
          </select>
        </td>
        <td><input type="number" class="form-control ls-qty" value="${data.qty || 1}" min="1"></td>
        <td><input type="number" class="form-control ls-milk" value="${data.milk || 0}" step="0.5" min="0"></td>
        <td><input type="number" class="form-control ls-income" value="${data.income || 0}" step="1000" min="0"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-table-row" onclick="this.closest('tr').remove()">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    // 6. Asset Row
    addAssetRow: function(data = {}) {
      const tbody = document.querySelector('#tableAssets tbody');
      if (!tbody) return;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="text" class="form-control as-name" value="${escapeHtml(data.asset || '')}" placeholder="e.g. Tractor / Spray Pump"></td>
        <td><input type="number" class="form-control as-qty" value="${data.qty || 1}" min="1"></td>
        <td>
          <select class="form-select as-status">
            <option value="Working / Operational" ${data.status === 'Working / Operational' ? 'selected' : ''}>Working / Operational</option>
            <option value="Repair Needed" ${data.status === 'Repair Needed' ? 'selected' : ''}>Repair Needed</option>
            <option value="Scrap" ${data.status === 'Scrap' ? 'selected' : ''}>Scrap</option>
          </select>
        </td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-table-row" onclick="this.closest('tr').remove()">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    // 7. Loan Row
    addLoanRow: function(data = {}) {
      const tbody = document.querySelector('#tableLoans tbody');
      if (!tbody) return;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <select class="form-select ln-source">
            <option value="PACS / Primary Agri Society" ${data.source === 'PACS / Primary Agri Society' ? 'selected' : ''}>PACS / Primary Agri Society</option>
            <option value="Commercial / Nationalized Bank" ${data.source === 'Commercial / Nationalized Bank' ? 'selected' : ''}>Commercial Bank</option>
            <option value="SHG Group Loan" ${data.source === 'SHG Group Loan' ? 'selected' : ''}>SHG Group Loan</option>
            <option value="Private Moneylender" ${data.source === 'Private Moneylender' ? 'selected' : ''}>Private Moneylender</option>
            <option value="Relatives / Friends" ${data.source === 'Relatives / Friends' ? 'selected' : ''}>Relatives / Friends</option>
          </select>
        </td>
        <td><input type="number" class="form-control ln-amt" value="${data.amount || 0}" step="1000" min="0"></td>
        <td><input type="text" class="form-control ln-purp" value="${escapeHtml(data.purpose || 'Crop Inputs')}" placeholder="e.g. Crop cultivation"></td>
        <td><input type="number" class="form-control ln-out" value="${data.outstanding || 0}" step="1000" min="0"></td>
        <td style="text-align: center;">
          <button type="button" class="btn-del-table-row" onclick="this.closest('tr').remove()">
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    },

    goToStep: function(targetStep) {
      if (targetStep < 1 || targetStep > totalSteps) return;

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

      const markInvalid = function(id) {
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
        const fName = document.getElementById('farmer_name');
        const phone = document.getElementById('contact_number');
        const village = document.getElementById('village');

        if (!fName || !fName.value.trim()) markInvalid('farmer_name');
        if (!phone || !phone.value.trim() || phone.value.trim().length < 10) markInvalid('contact_number');
        if (!village || !village.value.trim()) markInvalid('village');

      } else if (step === 2) {
        const land = document.getElementById('total_landholding_acres');
        if (!land || !land.value.trim() || parseFloat(land.value) < 0) markInvalid('total_landholding_acres');
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
      const container = document.getElementById('baselineReviewGrid');
      if (!container) return;

      const getVal = (id, fallback = '-') => {
        const el = document.getElementById(id);
        if (!el) return fallback;
        if (el.tagName === 'SELECT' && el.selectedIndex >= 0) {
          return el.options[el.selectedIndex].text || fallback;
        }
        return el.value.trim() || fallback;
      };

      const memberCount = document.querySelectorAll('#tableHouseholdMembers tbody tr').length;
      const cropCount = document.querySelectorAll('#tableCrops tbody tr').length;
      const livestockCount = document.querySelectorAll('#tableLivestock tbody tr').length;

      container.innerHTML = `
        <div class="review-card">
          <div class="review-card-header">
            <h4><i class="fa-solid fa-id-card" style="color:#2563eb;"></i> 1. Farmer Identification</h4>
            <button type="button" class="btn-review-edit" onclick="window.BaselineWizard.goToStep(1)">Edit</button>
          </div>
          <div class="review-item-list">
            <div class="review-row"><span class="review-lbl">Farmer Full Name:</span><span class="review-val">${escapeHtml(getVal('farmer_name'))}</span></div>
            <div class="review-row"><span class="review-lbl">Contact / Mobile:</span><span class="review-val">${escapeHtml(getVal('contact_number'))}</span></div>
            <div class="review-row"><span class="review-lbl">Village / Location:</span><span class="review-val">${escapeHtml(getVal('village'))}</span></div>
            <div class="review-row"><span class="review-lbl">Family Head Age / Category:</span><span class="review-val">${escapeHtml(getVal('age'))} yrs | ${escapeHtml(getVal('category'))}</span></div>
            <div class="review-row"><span class="review-lbl">House Type / BPL Status:</span><span class="review-val">${escapeHtml(getVal('house_type'))} | ${escapeHtml(getVal('is_bpl'))}</span></div>
            <div class="review-row"><span class="review-lbl">Household Members:</span><span class="review-val">${memberCount} members recorded</span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4><i class="fa-solid fa-wheat-awn" style="color:#2563eb;"></i> 2. Land & Crops</h4>
            <button type="button" class="btn-review-edit" onclick="window.BaselineWizard.goToStep(2)">Edit</button>
          </div>
          <div class="review-item-list">
            <div class="review-row"><span class="review-lbl">Total Landholding:</span><span class="review-val">${escapeHtml(getVal('total_landholding_acres'))} Acres</span></div>
            <div class="review-row"><span class="review-lbl">Irrigated / Rainfed:</span><span class="review-val">${escapeHtml(getVal('irrigated_land_acres'))} Ac / ${escapeHtml(getVal('rainfed_land_acres'))} Ac</span></div>
            <div class="review-row"><span class="review-lbl">Soil Testing Done:</span><span class="review-val">${escapeHtml(getVal('conducts_soil_testing'))}</span></div>
            <div class="review-row"><span class="review-lbl">Organic Farming:</span><span class="review-val">${escapeHtml(getVal('practices_organic_farming'))}</span></div>
            <div class="review-row"><span class="review-lbl">Crops Logged:</span><span class="review-val">${cropCount} crop records</span></div>
          </div>
        </div>

        <div class="review-card">
          <div class="review-card-header">
            <h4><i class="fa-solid fa-droplet" style="color:#2563eb;"></i> 3. Water & Financials</h4>
            <button type="button" class="btn-review-edit" onclick="window.BaselineWizard.goToStep(3)">Edit</button>
          </div>
          <div class="review-item-list">
            <div class="review-row"><span class="review-lbl">Drinking Water Source:</span><span class="review-val">${escapeHtml(getVal('drinking_water_source'))}</span></div>
            <div class="review-row"><span class="review-lbl">Year-Round Availability:</span><span class="review-val">${escapeHtml(getVal('drinking_water_year_round'))}</span></div>
            <div class="review-row"><span class="review-lbl">Owns Livestock:</span><span class="review-val">${escapeHtml(getVal('owns_livestock'))} (${livestockCount} animal types)</span></div>
            <div class="review-row"><span class="review-lbl">Milk Sale Channel:</span><span class="review-val">${escapeHtml(getVal('milk_sale_channel'))}</span></div>
            <div class="review-row"><span class="review-lbl">Water Budgeting:</span><span class="review-val">${escapeHtml(getVal('water_budgeting_practices'))}</span></div>
          </div>
        </div>
      `;
    },

    submitForm: function() {
      const consentBox = document.getElementById('confirmation_consent');
      if (consentBox && !consentBox.checked) {
        alert('Please acknowledge and check the Informed Consent statement before submitting.');
        consentBox.focus();
        return;
      }

      const submitBtn = document.getElementById('submitBtn');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting Survey...';
      }

      const form = document.getElementById('baselineSurveyForm');
      const formData = new FormData(form);
      const payload = {};

      formData.forEach((val, key) => {
        payload[key] = val;
      });

      payload.confirmation_consent = consentBox.checked ? 1 : 0;
      payload.submit_now = true;

      // 1. Household Members Table
      payload.household_members_table = [];
      document.querySelectorAll('#tableHouseholdMembers tbody tr').forEach(tr => {
        const name = tr.querySelector('.m-name') ? tr.querySelector('.m-name').value.trim() : '';
        if (name) {
          payload.household_members_table.push({
            member_name: name,
            relation: tr.querySelector('.m-rel') ? tr.querySelector('.m-rel').value : 'Self',
            gender: tr.querySelector('.m-gen') ? tr.querySelector('.m-gen').value : 'Male',
            age: tr.querySelector('.m-age') ? parseInt(tr.querySelector('.m-age').value || 0, 10) : null,
            education: tr.querySelector('.m-edu') ? tr.querySelector('.m-edu').value : 'Secondary [9-10]',
            occupation: tr.querySelector('.m-occ') ? tr.querySelector('.m-occ').value : 'Agriculture'
          });
        }
      });

      // 2. Crops Table
      payload.crops_table = [];
      document.querySelectorAll('#tableCrops tbody tr').forEach(tr => {
        const cname = tr.querySelector('.c-name') ? tr.querySelector('.c-name').value.trim() : '';
        if (cname) {
          payload.crops_table.push({
            season: tr.querySelector('.c-season') ? tr.querySelector('.c-season').value : 'Kharif',
            crop_name: cname,
            area_irrigated_acres: tr.querySelector('.c-irri') ? parseFloat(tr.querySelector('.c-irri').value || 0) : 0,
            area_dryland_acres: tr.querySelector('.c-dry') ? parseFloat(tr.querySelector('.c-dry').value || 0) : 0,
            yield_quintals: tr.querySelector('.c-yield') ? parseFloat(tr.querySelector('.c-yield').value || 0) : 0,
            cost_of_production: tr.querySelector('.c-cost') ? parseFloat(tr.querySelector('.c-cost').value || 0) : 0,
            total_income: tr.querySelector('.c-income') ? parseFloat(tr.querySelector('.c-income').value || 0) : 0
          });
        }
      });

      // 3. Irrigation Sources
      payload.irrigation_sources_table = [];
      document.querySelectorAll('#tableIrrigationSources tbody tr').forEach(tr => {
        const sname = tr.querySelector('.ir-name') ? tr.querySelector('.ir-name').value : '';
        if (sname) {
          payload.irrigation_sources_table.push({
            source_name: sname,
            quantity: tr.querySelector('.ir-qty') ? parseInt(tr.querySelector('.ir-qty').value || 1, 10) : 1,
            depth_feet: tr.querySelector('.ir-depth') ? parseFloat(tr.querySelector('.ir-depth').value || 0) : 0,
            water_availability_months: tr.querySelector('.ir-months') ? parseInt(tr.querySelector('.ir-months').value || 8, 10) : 8
          });
        }
      });

      // 4. Farm Conservation Works
      payload.farm_conservation_works_table = [];
      document.querySelectorAll('#tableConservationWorks tbody tr').forEach(tr => {
        const stype = tr.querySelector('.cw-type') ? tr.querySelector('.cw-type').value : '';
        if (stype) {
          payload.farm_conservation_works_table.push({
            structure_type: stype,
            status: tr.querySelector('.cw-status') ? tr.querySelector('.cw-status').value : 'Yes',
            length_or_count: tr.querySelector('.cw-len') ? tr.querySelector('.cw-len').value : '200 m',
            implementing_dept: tr.querySelector('.cw-dept') ? tr.querySelector('.cw-dept').value : 'Agriculture Dept',
            is_maintained: 'Yes'
          });
        }
      });

      // 5. Livestock Table
      payload.livestock_table = [];
      document.querySelectorAll('#tableLivestock tbody tr').forEach(tr => {
        const animal = tr.querySelector('.ls-animal') ? tr.querySelector('.ls-animal').value : '';
        if (animal) {
          payload.livestock_table.push({
            animal_type: animal,
            quantity: tr.querySelector('.ls-qty') ? parseInt(tr.querySelector('.ls-qty').value || 1, 10) : 1,
            daily_milk_litres: tr.querySelector('.ls-milk') ? parseFloat(tr.querySelector('.ls-milk').value || 0) : 0,
            annual_income: tr.querySelector('.ls-income') ? parseFloat(tr.querySelector('.ls-income').value || 0) : 0
          });
        }
      });

      // 6. Farm Assets Table
      payload.family_assets_table = [];
      document.querySelectorAll('#tableAssets tbody tr').forEach(tr => {
        const aname = tr.querySelector('.as-name') ? tr.querySelector('.as-name').value.trim() : '';
        if (aname) {
          payload.family_assets_table.push({
            asset_name: aname,
            quantity: tr.querySelector('.as-qty') ? parseInt(tr.querySelector('.as-qty').value || 1, 10) : 1,
            operational_status: tr.querySelector('.as-status') ? tr.querySelector('.as-status').value : 'Working / Operational'
          });
        }
      });

      // 7. Loans Table
      payload.loans_table = [];
      document.querySelectorAll('#tableLoans tbody tr').forEach(tr => {
        const source = tr.querySelector('.ln-source') ? tr.querySelector('.ln-source').value : '';
        if (source) {
          payload.loans_table.push({
            source: source,
            loan_amount: tr.querySelector('.ln-amt') ? parseFloat(tr.querySelector('.ln-amt').value || 0) : 0,
            purpose: tr.querySelector('.ln-purp') ? tr.querySelector('.ln-purp').value : 'Crop Inputs',
            outstanding_amount: tr.querySelector('.ln-out') ? parseFloat(tr.querySelector('.ln-out').value || 0) : 0
          });
        }
      });

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
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-check"></i> Submit Baseline Survey';
        }

        if (res.message && res.message.success) {
          form.style.display = 'none';
          const successScreen = document.getElementById('successScreen');
          if (successScreen) {
            successScreen.style.display = 'block';
            document.getElementById('successTitle').textContent = 'Baseline Survey Recorded!';
            document.getElementById('successMsg').textContent = `Baseline record ${res.message.name} for ${payload.farmer_name} with all child tables has been submitted successfully.`;
            document.getElementById('successRefPill').textContent = `Record ID: ${res.message.name}`;
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
          submitBtn.innerHTML = '<i class="fa-solid fa-check"></i> Submit Baseline Survey';
        }
        console.error(err);
        alert('Network error while recording Baseline Survey: ' + err.message);
      });
    }
  };

  document.addEventListener('DOMContentLoaded', function() {
    window.BaselineWizard.init();
  });
})();
