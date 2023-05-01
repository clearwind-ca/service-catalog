function processDateTime(datetimeTemplate) {
  const datetimeList = document.querySelectorAll('input[type="datetime-local"]')
  for (let element of datetimeList) {
    let clone = datetimeTemplate.content.cloneNode(true);
    let links = clone.querySelectorAll("a")
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
        element.value = target.toISOString().slice(0, 16);
      });
    }
    element.parentNode.insertBefore(clone, element.nextSibling);
  }
}

function processCreateAppForm(createAppForm) {
  createAppForm.addEventListener("submit", (event) => {
    event.preventDefault();
    let organization = createAppForm.querySelector("[name=organization]").value;
    let server_url = createAppForm.querySelector("[name=server_url]").value;
    let manifest = JSON.stringify({
      "name": `Catalog (${organization})`,
      "url": server_url,
      "callback_urls": [`${server_url}/oauth/github/callback/`],
      "redirect_url": `${server_url}/setup/`,
      "public": false,
      "default_permissions": {'contents': 'write', 'metadata': 'read', 'organization_administration': 'read'},
    })
    let manifestField = createAppForm.querySelector("[name=manifest]");
    manifestField.value = manifest;
    let original = createAppForm.getAttribute("data-action");
    createAppForm.setAttribute("action", original.replace("ORGANIZATION", organization));
    createAppForm.submit();
  });
}

window.addEventListener("load", (event) => {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

  const datetimeTemplate = document.getElementById("datetime");
  if (datetimeTemplate) {
    processDateTime(datetimeTemplate);
  }

  const createAppForm = document.getElementById("create-app");
  if (createAppForm) {
    processCreateAppForm(createAppForm);
  }
});