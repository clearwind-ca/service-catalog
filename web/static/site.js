window.addEventListener("load", (event) => {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

  
  const datetimeTemplate = document.getElementById("datetime");
  if (datetimeTemplate) {
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
});