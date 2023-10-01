function processDateTime(datetimeTemplate) {
  const element = document.getElementById('id_start');
  let clone = datetimeTemplate.content.cloneNode(true);
  let links = clone.querySelectorAll("a");
  for (let link of links) {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      let when = event.target.getAttribute("data-when");
      let target = new Date();
      if (when == "tomorrow") {
        target.setDate(target.getDate() + 1);
      }
      if (when == "yesterday") {
        target.setDate(target.getDate() - 1);
      }
      // Just move the date not the time, because it might be 12 or 24 hour format,
      // depending upon system settings. Doable but more work. Currently only altering the date anyway.
      element.value =
        target.toISOString().slice(0, 10) + element.value.slice(10, 19);
    });
  }
  element.parentNode.insertBefore(clone, element.nextSibling);
}

function enhanceCreateCheckForm(createCheckForm) {
  let limit = document.getElementById("id_limit");
  let services = document.getElementById("id_services");
  // Load
  if (limit.value != "some") {
    services.disabled = true;
  }
  // Change
  limit.addEventListener("change", (event) => {
    if (event.target.value != "some") {
      services.disabled = true;
    } else {
      services.disabled = false;
    }
  })
}

function processCreateAppForm(createAppForm) {
  createAppForm.addEventListener("submit", (event) => {
    event.preventDefault();
    let organization = createAppForm.querySelector("[name=organization]").value;
    let server_url = createAppForm.querySelector("[name=server_url]").value;
    let manifest = JSON.stringify({
      name: `Catalog (${organization})`,
      url: server_url,
      callback_urls: [`${server_url}/oauth/github/callback/`],
      redirect_url: `${server_url}/setup/`,
      hook_attributes: {
        url: `${server_url}/github/webhooks/`,
      },
      public: false,
      default_permissions: {
        actions: "write",
        contents: "write",
        metadata: "read",
        deployments: "read",
        emails: "read",
        organization_administration: "read",
        pull_requests: "write"
      },
      default_events: ["deployment", "release"],
    });
    let manifestField = createAppForm.querySelector("[name=manifest]");
    manifestField.value = manifest;
    let original = createAppForm.getAttribute("data-action");
    createAppForm.setAttribute(
      "action",
      original.replace("ORGANIZATION", organization)
    );
    createAppForm.submit();
  });
}

forms = {
  "check-form": enhanceCreateCheckForm,
  "create-app": processCreateAppForm,
  "datetime": processDateTime,
}

window.addEventListener("load", (event) => {
  // Load tooltips
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]'
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
  );

  // Update popover allowlist
  const myAllowList = bootstrap.Popover.Default.allowList;
  myAllowList.b = [];
  myAllowList.a = ["data-copy"];
  myAllowList.svg = ["width", "height", "version", "class"];
  myAllowList.path = ["fill-rule", "d"];

  // Load popovers
  const popoverTriggerList = document.querySelectorAll(
    '[data-bs-toggle="popover"]'
  );
  const popoverList = [...popoverTriggerList].map(
    (popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl, {allowList:myAllowList, html: true})
  );

  // Load form enhancements based on ids being present
  for (let form of Object.keys(forms)) {
    const element = document.getElementById(form);
    if (element) {
      forms[form](element);
    }
  }
  
  // Load copy to clipboard
  document.querySelectorAll(".copy").forEach((element) => {
    element.addEventListener("click", (element) => {
      navigator.clipboard.writeText(element.target.getAttribute("data-copy"))
    });
  });
});
