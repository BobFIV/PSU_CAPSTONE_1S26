(() => {
    const modal = document.getElementById("wfModal");
    const modalTitle = document.getElementById("wfModalTitle");
    const modalBody = document.getElementById("wfModalBody");
    const btnCloseX = document.getElementById("wfClose");
    const btnClose = document.getElementById("wfJustClose");
    const btnBackTopo = document.getElementById("wfBackToTopo");
    const statusEl = document.getElementById("wfStatus");
  
    const nodeLeftText = document.getElementById("nodeLeftText");
    const nodeRightText = document.getElementById("nodeRightText");
  
    const tpl = (id) => document.getElementById(id).content.cloneNode(true);
  
    const state = {
      host: { ip: "", port: "", extra: "", deployedAction: null },
      cse: { name: "", extra: "", deployedAction: null },
      ae: { name: "", extra: "", deployedAction: null },
    };
  
    function setStatus(msg) {
      statusEl.textContent = msg;
    }
  
    function openModal(kind) {
      btnBackTopo.disabled = true;
      btnBackTopo.dataset.ready = "0";
  
      modalBody.innerHTML = "";
  
      if (kind === "host") {
        modalTitle.textContent = "Provision Host";
        modalBody.appendChild(tpl("tplHost"));
        bindHost(modalBody);
      } else if (kind === "cse") {
        modalTitle.textContent = "Add CSE";
        modalBody.appendChild(tpl("tplCSE"));
        bindCSE(modalBody);
      } else if (kind === "ae") {
        modalTitle.textContent = "Deploy AE";
        modalBody.appendChild(tpl("tplAE"));
        bindAE(modalBody);
      }
  
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
    }
  
    function closeModal() {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
      modalBody.innerHTML = "";
    }
  
    function markSelected(root, actionKey) {
      root.querySelectorAll(".wfAction").forEach((b) => {
        b.classList.toggle("selected", b.dataset.action === actionKey);
      });
    }
  
    function enableBackToTopology(msg) {
      btnBackTopo.disabled = false;
      btnBackTopo.dataset.ready = "1";
      setStatus(msg);
      refreshTopologyText();
    }
  
    function refreshTopologyText() {
      const cse = (state.cse.name || "MN-CSE").trim();
      const ae = (state.ae.name || "sample AE").trim();
  
      nodeLeftText.innerHTML = `<div>rPI</div><div>${escapeHtml(cse)}</div><div>${escapeHtml(ae)}</div>`;
      nodeRightText.innerHTML = `<div>rPI</div><div>${escapeHtml(cse)}</div><div>${escapeHtml(ae)}</div>`;
    }
  
    function escapeHtml(s) {
      return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
  
    // Bind Host screen
    function bindHost(root) {
      const ip = root.querySelector('input[name="host_ip"]');
      const port = root.querySelector('input[name="host_port"]');
      const extra = root.querySelector('input[name="host_extra"]');
  
      ip.value = state.host.ip;
      port.value = state.host.port;
      extra.value = state.host.extra;
  
      ip.addEventListener("input", () => (state.host.ip = ip.value));
      port.addEventListener("input", () => (state.host.port = port.value));
      extra.addEventListener("input", () => (state.host.extra = extra.value));
  
      if (state.host.deployedAction) markSelected(root, state.host.deployedAction);
  
      root.querySelectorAll(".wfAction").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.host.deployedAction = btn.dataset.action;
          markSelected(root, state.host.deployedAction);
  
          enableBackToTopology(`Host deployed (${btn.textContent.trim()}) • click "Back to Topology"`);
        });
      });
    }
  
    // Bind CSE screen
    function bindCSE(root) {
      const name = root.querySelector('input[name="cse_name"]');
      const extra = root.querySelector('input[name="cse_extra"]');
  
      name.value = state.cse.name;
      extra.value = state.cse.extra;
  
      name.addEventListener("input", () => {
        state.cse.name = name.value;
        refreshTopologyText();
      });
      extra.addEventListener("input", () => (state.cse.extra = extra.value));
  
      if (state.cse.deployedAction) markSelected(root, state.cse.deployedAction);
  
      root.querySelectorAll(".wfAction").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.cse.deployedAction = btn.dataset.action;
          markSelected(root, state.cse.deployedAction);
  
          enableBackToTopology(`CSE deployed (${btn.textContent.trim()}) • click "Back to Topology"`);
        });
      });
    }
  
    // Bind AE screen
    function bindAE(root) {
      const name = root.querySelector('input[name="ae_name"]');
      const extra = root.querySelector('input[name="ae_extra"]');
  
      name.value = state.ae.name;
      extra.value = state.ae.extra;
  
      name.addEventListener("input", () => {
        state.ae.name = name.value;
        refreshTopologyText();
      });
      extra.addEventListener("input", () => (state.ae.extra = extra.value));
  
      if (state.ae.deployedAction) markSelected(root, state.ae.deployedAction);
  
      root.querySelectorAll(".wfAction").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.ae.deployedAction = btn.dataset.action;
          markSelected(root, state.ae.deployedAction);
  
          enableBackToTopology(`AE deployed (${btn.textContent.trim()}) • click "Back to Topology"`);
        });
      });
    }
  
    // Nav buttons -> open popup
    document.querySelectorAll(".wfNavItem").forEach((btn) => {
      btn.addEventListener("click", () => {
        openModal(btn.dataset.open);
      });
    });
  
    // Close behavior
    btnCloseX.addEventListener("click", closeModal);
    btnClose.addEventListener("click", closeModal);
  
    // Back to topology (only enabled after a deploy click)
    btnBackTopo.addEventListener("click", () => {
      if (btnBackTopo.dataset.ready !== "1") return;
      closeModal();
      setStatus("Topology view (UI-only) • updated from your inputs");
    });
  
    // click outside panel closes
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });
  
    // init
    refreshTopologyText();
  })();
  