// Public Procurement Bid Compliance Screening Service - Frontend Client
let currentRunId = null;
let pollInterval = null;

const API_BASE = window.location.origin;

document.getElementById("screening-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearResults();

  const btnSubmit = document.getElementById("btn-submit");
  const spinner = document.getElementById("btn-spinner");
  btnSubmit.disabled = true;
  spinner.classList.remove("d-none");

  const category = document.getElementById("declared_category").value;
  const certNumber = document.getElementById("cert_number").value;

  const payload = {
    bid_ref: document.getElementById("bid_ref").value,
    tender_id: document.getElementById("tender_id").value,
    bidder: {
      name: document.getElementById("bidder_name").value,
      declared_category: category,
      country_code: document.getElementById("country_code").value.toUpperCase(),
      incorporation_date: document.getElementById("incorporation_date").value,
      years_experience: parseFloat(document.getElementById("years_experience").value),
      annual_turnover_lakh: [
        parseFloat(document.getElementById("to_1").value) || 0,
        parseFloat(document.getElementById("to_2").value) || 0,
        parseFloat(document.getElementById("to_3").value) || 0,
      ],
      udyam_number: category === "MSE" ? certNumber : null,
      startup_certificate_number: category === "STARTUP" ? certNumber : null,
      manpower_payroll_percent: parseFloat(document.getElementById("payroll_pct").value),
      emd_submitted: document.getElementById("emd_submitted").checked,
      emd_amount_inr: document.getElementById("emd_submitted").checked ? 117600 : 0,
      emd_exemption_claimed: false,
      office_in_consignee_state: document.getElementById("office_state").checked,
      documents_submitted: [
        "EXPERIENCE_PROOF",
        "TURNOVER_PROOF",
        "DPIIT_CERTIFICATE",
        "PAYROLL_PROOF"
      ],
      similar_services: [
        { contract_value_lakh: 120.0, client_type: "CENTRAL" }
      ]
    },
    notes: null
  };

  try {
    const res = await fetch(`${API_BASE}/v1/screenings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Client-Id": "web-dashboard"
      },
      body: JSON.stringify(payload)
    });

    if (res.status === 422) {
      const errData = await res.json();
      showAlert(`Request Quarantined! ID: <strong>${errData.quarantine_id}</strong><br>Errors: ${JSON.stringify(errData.errors)}`, "danger");
      btnSubmit.disabled = false;
      spinner.classList.add("d-none");
      return;
    }

    if (!res.ok) {
      showAlert(`Submission error (HTTP ${res.status}): ${await res.text()}`, "danger");
      btnSubmit.disabled = false;
      spinner.classList.add("d-none");
      return;
    }

    const data = await res.json();
    currentRunId = data.run_id;
    showAlert(`Screening run queued: <code>${currentRunId}</code>. Polling worker state...`, "info");

    pollInterval = setInterval(() => pollRunStatus(currentRunId), 2000);

  } catch (err) {
    showAlert(`Network error: ${err.message}`, "danger");
    btnSubmit.disabled = false;
    spinner.classList.add("d-none");
  }
});

async function pollRunStatus(runId) {
  try {
    const res = await fetch(`${API_BASE}/v1/screenings/${runId}`);
    if (!res.ok) return;

    const data = await res.json();

    if (data.status === "COMPLETED") {
      clearInterval(pollInterval);
      document.getElementById("btn-submit").disabled = false;
      document.getElementById("btn-spinner").classList.add("d-none");
      showAlert("Screening run completed successfully.", "success");
      renderResults(data);
    } else if (data.status === "FAILED") {
      clearInterval(pollInterval);
      document.getElementById("btn-submit").disabled = false;
      document.getElementById("btn-spinner").classList.add("d-none");
      showAlert(`Screening run failed: ${data.error_message || "Unknown error"}`, "danger");
    }
  } catch (err) {
    console.error("Polling error", err);
  }
}

function renderResults(data) {
  document.getElementById("results-placeholder").classList.add("d-none");
  document.getElementById("results-container").classList.remove("d-none");

  // Run header
  document.getElementById("res-run-id").textContent = data.run_id;
  document.getElementById("res-status").textContent = data.status;
  document.getElementById("res-status").className = "badge bg-success";

  // Route badge
  const route = data.recommended_route || "UNKNOWN";
  const badgeContainer = document.getElementById("route-badge-container");
  let routeClass = "bg-secondary";
  if (route === "PASS_TO_TECHNICAL_EVALUATION") routeClass = "route-pass";
  else if (route === "REJECT_WITH_CITED_CONDITION") routeClass = "route-reject";
  else if (route === "ESCALATE_TO_HUMAN") routeClass = "route-escalate";
  else if (route === "SEEK_CLARIFICATION") routeClass = "route-clarify";

  badgeContainer.innerHTML = `<span class="badge badge-route ${routeClass}">${route.replace(/_/g, " ")}</span>`;

  // Escalation reason
  const escElem = document.getElementById("res-escalation");
  if (data.escalation_reason) {
    escElem.textContent = data.escalation_reason;
    escElem.className = "badge bg-warning text-dark";
  } else {
    escElem.textContent = "NONE";
    escElem.className = "badge bg-light text-muted";
  }

  // Findings table
  const tbody = document.getElementById("findings-body");
  tbody.innerHTML = "";

  (data.findings || []).forEach(f => {
    const tr = document.createElement("tr");

    // Citations HTML
    let citationsHtml = "-";
    if (f.citations && f.citations.length > 0) {
      citationsHtml = f.citations.map(c => `
        <div class="citation-box">
          <strong>${c.clause_id}</strong><br>
          <em>"${c.quoted_text}"</em>
        </div>
      `).join("");
    }

    tr.innerHTML = `
      <td><strong>${f.condition_id}</strong></td>
      <td>
        <div class="fw-semibold">${f.condition_name}</div>
        <div class="small text-muted">${f.advisory_note || ""}</div>
      </td>
      <td><span class="status-badge status-${f.status}">${f.status}</span></td>
      <td>${citationsHtml}</td>
    `;
    tbody.appendChild(tr);
  });

  // Advisory note
  const advBox = document.getElementById("advisory-box");
  if (data.summary_advisory) {
    advBox.innerHTML = `<strong>Advisory Notes:</strong> ${data.summary_advisory}`;
    advBox.classList.remove("d-none");
  } else {
    advBox.classList.add("d-none");
  }

  // Cost and metrics
  document.getElementById("res-metrics").textContent =
    `Steps: ${data.agent_steps || 0} | Tool Calls: ${data.tool_calls || 0} | Estimated Cost: $${(data.llm_cost_usd || 0).toFixed(4)}`;
}

async function sendFeedback(agree) {
  if (!currentRunId) return;
  try {
    const res = await fetch(`${API_BASE}/v1/screenings/${currentRunId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ satisfactory: agree, reason: agree ? "Verified accurate" : "Flagged by operator" })
    });
    if (res.ok) {
      showAlert("Feedback submitted successfully. Recorded for quality evaluation.", "info");
    }
  } catch (e) {
    console.error("Feedback error", e);
  }
}

function showAlert(msg, type) {
  const alert = document.getElementById("status-alert");
  alert.className = `alert alert-${type} py-2 small`;
  alert.innerHTML = msg;
  alert.classList.remove("d-none");
}

function clearResults() {
  if (pollInterval) clearInterval(pollInterval);
  document.getElementById("status-alert").classList.add("d-none");
  document.getElementById("results-placeholder").classList.remove("d-none");
  document.getElementById("results-container").classList.add("d-none");
  document.getElementById("route-badge-container").innerHTML = "";
}
