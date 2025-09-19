document.addEventListener("DOMContentLoaded", function () {
  // Enable Bootstrap tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // Form validation
  const forms = document.querySelectorAll(".needs-validation");
  forms.forEach((form) => {
    form.addEventListener(
      "submit",
      (event) => {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add("was-validated");
      },
      false
    );
  });

  // Weather icon mapping
  const weatherIcons = {
    Sunny: "fa-sun",
    "Partly Cloudy": "fa-cloud-sun",
    Cloudy: "fa-cloud",
    Rain: "fa-cloud-rain",
    "Light Rain": "fa-cloud-drizzle",
    "Heavy Rain": "fa-cloud-showers-heavy",
    Thunderstorm: "fa-bolt",
    Snow: "fa-snowflake",
  };

  // Update weather icons
  document.querySelectorAll(".weather-icon").forEach((iconEl) => {
    const condition = iconEl.getAttribute("data-condition");
    if (weatherIcons[condition]) {
      iconEl.className = `fas ${weatherIcons[condition]} fa-2x`;
    }
  });
});
