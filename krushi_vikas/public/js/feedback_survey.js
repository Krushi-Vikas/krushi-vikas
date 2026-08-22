/**
 * Feedback Survey Multi-Step Form Logic
 * Krushi Vikas Agri & Watershed Management
 */

(function () {
  'use strict';

  window.feedbackSurveyLoaded = true;

  // State
  let currentStep = 1;
  const totalSteps = 4;
  const formData = {
    village: '',
    date_of_visit: '',
    field_officer: '',
    activity: '',
    respondent_type: '',
    respondent_type_other: '',
    total_participants: '',
    households_involved: '',
    sessions_conducted: '',
    adoption_percentage: '',
    outputs_achieved: '',
    significant_change: '',
    community_voice: '',
    barriers_challenges: '',
    facilitator_observations: '',
    overall_rating: '3',
    confirmation_accuracy: false
  };

  // DOM Elements
  const panels = document.querySelectorAll('.form-step-panel');
  const sidebarStepItems = document.querySelectorAll('.step-item');
  const panelStepDots = document.querySelectorAll('.panel-step-dot');
  const mobileStepCounter = document.getElementById('mobileStepCounter');
  const mobileStepDots = document.querySelectorAll('.mobile-step-dot');
  const respondentTypeSelect = document.getElementById('respondent_type');
  const otherGroup = document.getElementById('group_other_specify');
  const dateInput = document.getElementById('date_of_visit');

  // Initialize
  document.addEventListener('DOMContentLoaded', () => {
    initDefaultDate();
    initOptions();
    bindEvents();
    updateUI();
  });

  function initDefaultDate() {
    if (dateInput && !dateInput.value) {
      const today = new Date().toISOString().split('T')[0];
      dateInput.value = today;
    }
  }

  function initOptions() {
    // Attempt to load dynamic options from Frappe API if available
    if (window.frappe && frappe.call) {
      frappe.call({
        method: 'krushi_vikas.api.get_feedback_survey_options',
        callback: function (r) {
          if (r.message) {
            populateSelect('village', r.message.villages, 'Select village');
            populateOfficers('field_officer', r.message.field_officers);
            populateSelect('activity', r.message.activities, 'Select activity');
            populateSelect('respondent_type', r.message.respondent_types, 'Select type');
          }
        }
      });
    }
  }

  function populateSelect(elemId, items, placeholder) {
    const select = document.getElementById(elemId);
    if (!select || !items) return;
    const currentVal = select.value;
    select.innerHTML = `<option value="">${placeholder}</option>` +
      items.map(item => `<option value="${escapeHtml(item)}" ${currentVal === item ? 'selected' : ''}>${escapeHtml(item)}</option>`).join('');
  }

  function populateOfficers(elemId, officers) {
    const select = document.getElementById(elemId);
    if (!select || !officers) return;
    const currentVal = select.value;
    select.innerHTML = `<option value="">Select name</option>` +
      officers.map(o => `<option value="${escapeHtml(o.name)}" ${currentVal === o.name ? 'selected' : ''}>${escapeHtml(o.full_name || o.name)}</option>`).join('');
  }

  function bindEvents() {
    // Step navigation buttons
    document.querySelectorAll('[data-action="next"]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (validateCurrentStep()) {
          collectStepData();
          goToStep(currentStep + 1);
        }
      });
    });

    document.querySelectorAll('[data-action="back"]').forEach(btn => {
      btn.addEventListener('click', () => {
        collectStepData();
        goToStep(currentStep - 1);
      });
    });

    // Jump from review card edit buttons
    document.querySelectorAll('[data-jump-step]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const targetStep = parseInt(btn.getAttribute('data-jump-step'), 10);
        if (targetStep >= 1 && targetStep <= 3) {
          collectStepData();
          goToStep(targetStep);
        }
      });
    });

    // Sidebar clicks
    sidebarStepItems.forEach((item, idx) => {
      item.addEventListener('click', () => {
        const targetStep = idx + 1;
        if (targetStep < currentStep || validateCurrentStep()) {
          collectStepData();
          goToStep(targetStep);
        }
      });
    });

    // Respondent Type conditional 'Other' field
    if (respondentTypeSelect) {
      respondentTypeSelect.addEventListener('change', () => {
        const isOther = respondentTypeSelect.value === 'Other';
        if (otherGroup) {
          otherGroup.style.display = isOther ? 'flex' : 'none';
          const otherInput = document.getElementById('respondent_type_other');
          if (otherInput && !isOther) otherInput.value = '';
        }
      });
    }

    // Rating selection change
    document.querySelectorAll('input[name="overall_rating"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        formData.overall_rating = e.target.value;
      });
    });

    // Submit form action
    const submitBtn = document.getElementById('submitSurveyBtn');
    if (submitBtn) {
      submitBtn.addEventListener('click', handleFormSubmit);
    }
  }

  function goToStep(step) {
    if (step < 1 || step > totalSteps) return;
    currentStep = step;
    updateUI();
    if (currentStep === 4) {
      populateReviewCards();
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function collectStepData() {
    const activePanel = document.querySelector(`.form-step-panel[data-step="${currentStep}"]`);
    if (!activePanel) return;

    activePanel.querySelectorAll('input, select, textarea').forEach(input => {
      const name = input.name || input.id;
      if (!name) return;
      if (input.type === 'checkbox') {
        formData[name] = input.checked;
      } else if (input.type === 'radio') {
        if (input.checked) {
          formData[name] = input.value;
        }
      } else {
        formData[name] = input.value.trim();
      }
    });
  }

  function validateCurrentStep() {
    clearErrors();
    let isValid = true;

    if (currentStep === 1) {
      const village = document.getElementById('village');
      const dateOfVisit = document.getElementById('date_of_visit');
      const officer = document.getElementById('field_officer');
      const activity = document.getElementById('activity');
      const respondentType = document.getElementById('respondent_type');
      const otherInput = document.getElementById('respondent_type_other');

      if (!village.value.trim()) { showError(village, 'Please select or enter village/location'); isValid = false; }
      if (!dateOfVisit.value.trim()) { showError(dateOfVisit, 'Please select date of visit'); isValid = false; }
      if (!officer.value.trim()) { showError(officer, 'Please select field officer'); isValid = false; }
      if (!activity.value.trim()) { showError(activity, 'Please select activity'); isValid = false; }
      if (!respondentType.value.trim()) { showError(respondentType, 'Please select respondent type'); isValid = false; }
      if (respondentType.value === 'Other' && (!otherInput || !otherInput.value.trim())) {
        showError(otherInput, 'Please specify the respondent type');
        isValid = false;
      }
    } else if (currentStep === 2) {
      const participants = document.getElementById('total_participants');
      const adoption = document.getElementById('adoption_percentage');

      if (!participants.value.trim() || parseInt(participants.value, 10) < 0) {
        showError(participants, 'Please enter valid total participants (0 or more)');
        isValid = false;
      }
      if (!adoption.value.trim() || parseFloat(adoption.value) < 0 || parseFloat(adoption.value) > 100) {
        showError(adoption, 'Please enter a valid adoption percentage (0 to 100%)');
        isValid = false;
      }
    } else if (currentStep === 3) {
      const change = document.getElementById('significant_change');
      if (!change.value.trim()) {
        showError(change, 'Most Significant Change / Success Story is required');
        isValid = false;
      }
    } else if (currentStep === 4) {
      const confirmCheck = document.getElementById('confirmation_accuracy');
      if (confirmCheck && !confirmCheck.checked) {
        alert('Please confirm that the information provided is accurate before submitting.');
        isValid = false;
      }
    }

    return isValid;
  }

  function showError(element, msg) {
    if (!element) return;
    element.style.borderColor = '#ef4444';
    let hint = element.parentNode.querySelector('.error-hint');
    if (!hint) {
      hint = document.createElement('div');
      hint.className = 'error-hint';
      hint.style.color = '#ef4444';
      hint.style.fontSize = '12px';
      hint.style.marginTop = '4px';
      element.parentNode.appendChild(hint);
    }
    hint.textContent = msg;
  }

  function clearErrors() {
    document.querySelectorAll('.form-control').forEach(el => {
      el.style.borderColor = '';
    });
    document.querySelectorAll('.error-hint').forEach(el => el.remove());
  }

  function updateUI() {
    // Panels
    panels.forEach(panel => {
      const step = parseInt(panel.getAttribute('data-step'), 10);
      if (step === currentStep) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });

    // Sidebar items
    sidebarStepItems.forEach((item, idx) => {
      const step = idx + 1;
      item.classList.remove('active', 'completed');
      const badge = item.querySelector('.step-badge');
      if (step === currentStep) {
        item.classList.add('active');
        badge.innerHTML = step;
      } else if (step < currentStep) {
        item.classList.add('completed');
        badge.innerHTML = '✓';
      } else {
        badge.innerHTML = step;
      }
    });

    // Panel step dots
    panelStepDots.forEach(dot => {
      const step = parseInt(dot.getAttribute('data-dot-step'), 10);
      dot.classList.remove('active', 'completed');
      if (step === currentStep) {
        dot.classList.add('active');
        dot.innerHTML = step;
      } else if (step < currentStep) {
        dot.classList.add('completed');
        dot.innerHTML = '✓';
      } else {
        dot.innerHTML = step;
      }
    });

    // Mobile Stepper Bar
    if (mobileStepCounter) {
      mobileStepCounter.textContent = `Step ${currentStep} of ${totalSteps}`;
    }
    mobileStepDots.forEach((dot, idx) => {
      const step = idx + 1;
      dot.classList.remove('active', 'completed');
      if (step === currentStep) {
        dot.classList.add('active');
      } else if (step < currentStep) {
        dot.classList.add('completed');
      }
    });
  }

  function populateReviewCards() {
    collectStepData();

    // Section A Review
    const revVillage = document.getElementById('rev_village');
    const revDate = document.getElementById('rev_date');
    const revOfficer = document.getElementById('rev_officer');
    const revActivity = document.getElementById('rev_activity');
    const revRespondentType = document.getElementById('rev_respondent_type');
    const revOther = document.getElementById('rev_other');

    if (revVillage) revVillage.textContent = formData.village || '-';
    if (revDate) revDate.textContent = formatDateDisplay(formData.date_of_visit);
    if (revOfficer) {
      const officerSelect = document.getElementById('field_officer');
      const officerText = officerSelect ? officerSelect.options[officerSelect.selectedIndex]?.text : formData.field_officer;
      revOfficer.textContent = officerText || formData.field_officer || '-';
    }
    if (revActivity) revActivity.textContent = formData.activity || '-';
    if (revRespondentType) revRespondentType.textContent = formData.respondent_type || '-';
    if (revOther) revOther.textContent = formData.respondent_type_other || '-';

    // Section B Review
    const revParticipants = document.getElementById('rev_participants');
    const revHouseholds = document.getElementById('rev_households');
    const revSessions = document.getElementById('rev_sessions');
    const revAdoption = document.getElementById('rev_adoption');
    const revOutputs = document.getElementById('rev_outputs');

    if (revParticipants) revParticipants.textContent = formData.total_participants || '0';
    if (revHouseholds) revHouseholds.textContent = formData.households_involved || '-';
    if (revSessions) revSessions.textContent = formData.sessions_conducted || '-';
    if (revAdoption) revAdoption.textContent = formData.adoption_percentage ? `${formData.adoption_percentage}%` : '-';
    if (revOutputs) revOutputs.textContent = formData.outputs_achieved || '-';

    // Section C Review
    const revStory = document.getElementById('rev_story');
    const revQuote = document.getElementById('rev_quote');
    const revChallenges = document.getElementById('rev_challenges');
    const revObservations = document.getElementById('rev_observations');
    const revRating = document.getElementById('rev_rating');

    if (revStory) revStory.textContent = formData.significant_change || '-';
    if (revQuote) revQuote.textContent = formData.community_voice || '-';
    if (revChallenges) revChallenges.textContent = formData.barriers_challenges || '-';
    if (revObservations) revObservations.textContent = formData.facilitator_observations || '-';
    if (revRating) {
      const r = formData.overall_rating || '3';
      revRating.textContent = `${r} / 5 (${getRatingLabel(r)})`;
    }
  }

  function getRatingLabel(val) {
    switch (val) {
      case '1': return 'Low Impact';
      case '2': return 'Minor Impact';
      case '3': return 'Moderate Impact';
      case '4': return 'Significant Impact';
      case '5': return 'High Impact';
      default: return '';
    }
  }

  function formatDateDisplay(isoDate) {
    if (!isoDate) return '-';
    const parts = isoDate.split('-');
    if (parts.length === 3) {
      return `${parts[2]} / ${parts[1]} / ${parts[0]}`;
    }
    return isoDate;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function handleFormSubmit() {
    collectStepData();
    if (!validateCurrentStep()) return;

    const submitBtn = document.getElementById('submitSurveyBtn');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Submitting...';
    }

    const payload = { ...formData, submit_now: true };

    if (window.frappe && frappe.call) {
      frappe.call({
        method: 'krushi_vikas.api.submit_feedback_survey',
        args: { data: payload },
        callback: function (r) {
          if (r.message && r.message.success) {
            showSuccessScreen(r.message.name);
          } else {
            alert('Submission failed. Please check your inputs.');
            if (submitBtn) {
              submitBtn.disabled = false;
              submitBtn.innerHTML = 'Submit ✈';
            }
          }
        },
        error: function () {
          alert('An error occurred during submission.');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Submit ✈';
          }
        }
      });
    } else {
      // Fallback for standalone demo / offline testing
      setTimeout(() => {
        const mockRef = 'FS-2026-' + Math.floor(10000 + Math.random() * 90000);
        showSuccessScreen(mockRef);
      }, 600);
    }
  }

  function showSuccessScreen(referenceId) {
    const mainCard = document.querySelector('.survey-main-card');
    if (!mainCard) return;

    mainCard.innerHTML = `
      <div class="success-card">
        <div class="success-icon-wrap">✓</div>
        <h2 class="success-title">Feedback Submitted Successfully!</h2>
        <p class="success-desc">
          Thank you for taking the time to share your feedback. Your responses have been securely recorded and will help measure outcomes and improve future initiatives.
        </p>
        <div>
          <span class="ref-badge">Reference ID: ${escapeHtml(referenceId)}</span>
        </div>
        <div style="display: flex; justify-content: center; gap: 14px; margin-top: 16px;">
          <button class="btn btn-secondary" onclick="window.location.reload();">Submit Another Response</button>
          <a href="/app/feedback-survey" class="btn btn-primary">View in Desk</a>
        </div>
      </div>
    `;
  }
})();
