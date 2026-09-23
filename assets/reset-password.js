"use strict";
(() => {
  const field = document.getElementById("reset-token");
  if (!field) return;
  field.value = location.hash.slice(1);
  history.replaceState(null, "", "/reset-password");
})();
