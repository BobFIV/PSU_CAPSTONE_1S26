(() => {
  const modal = document.getElementById("wfModal");
  const modalTitle = document.getElementById("wfModalTitle");
  const modalBody = document.getElementById("wfModalBody");
  const btnCloseX = document.getElementById("wfClose");
  const btnClose = document.getElementById("wfJustClose");
  const btnBackTopo = document.getElementById("wfBackToTopo");
  const statusEl = document.getElementById("wfStatus");
  const topoMetaEl = document.getElementById("wfTopoMeta");
  const cyContainer = document.getElementById("cyTopology");
  const infoPanel = document.getElementById("wfInfoPanel");
  const infoPanelTitle = document.getElementById("wfInfoPanelTitle");
  const infoPanelBody = document.getElementById("wfInfoPanelBody");
  const infoPanelClose = document.getElementById("wfInfoPanelClose");

  const tpl = (id) => document.getElementById(id).content.cloneNode(true);

  let cy = null;
  let topologyPollTimer = null;

  const state = {
    host: { ip: "", port: "", extra: "", deployedAction: null },
    cse: { name: "", port: "", cseID: "", dockerName: "", extra: "", deployedAction: null },
    ae: { name: "", extra: "", deployedAction: null },
    topology: {
      version: 0,
      updated_at: null,
      cses: [],
      aes: [],
    },
  };

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  function normalizeTopology(topology) {
    const safe = topology || {};
    return {
      version: typeof safe.version === "number" ? safe.version : 0,
      updated_at: safe.updated_at || null,
      cses: Array.isArray(safe.cses) ? safe.cses : [],
      aes: Array.isArray(safe.aes) ? safe.aes : [],
    };
  }

  function applyTopology(topology) {
    state.topology = normalizeTopology(topology);
    updateMeta();
    renderTopology();
  }

  function latestCse() {
    return state.topology.cses.length
      ? state.topology.cses[state.topology.cses.length - 1]
      : null;
  }

  function updateMeta() {
    const cseCount = state.topology.cses.length;
    const aeCount = state.topology.aes.filter(ae => ae.name !== 'CAdmin').length;
    if (topoMetaEl) {
      topoMetaEl.textContent =
        `${cseCount} MN-CSE${cseCount === 1 ? "" : "s"} • ` +
        `${aeCount} AE${aeCount === 1 ? "" : "s"}`;
    }
  }

  // ── Info Panel ────────────────────────────────────────────────
  function showInfoPanel(title, htmlContent) {
    infoPanelTitle.textContent = title;
    infoPanelBody.innerHTML = htmlContent;
    infoPanel.classList.add("open");
  }

  function hideInfoPanel() {
    infoPanel.classList.remove("open");
    infoPanelBody.innerHTML = "";
  }

  infoPanelClose.addEventListener("click", hideInfoPanel);

  async function fetchNodeInfo(nodeType, resourceName) {
    showInfoPanel(resourceName || "IN-CSE", `<div class="wfInfoLoading">Loading…</div>`);
    try {
      const params = new URLSearchParams({ type: nodeType, name: resourceName || "" });
      const res = await fetch(`/api/node/info/?${params}`);
      const data = await res.json();

      if (!data.success) {
        showInfoPanel(resourceName || "IN-CSE",
          `<div class="wfInfoError">⚠ ${data.message || "Failed to fetch"}</div>`);
        return;
      }

      const props = data.properties || {};
      const rows = Object.entries(props).map(([k, v]) => {
        const val = Array.isArray(v) ? v.join(", ") : String(v);
        return `<tr><td class="wfInfoKey">${k}</td><td class="wfInfoVal">${val}</td></tr>`;
      }).join("");

      const typeLabel = {
        "m2m:cb":  "CSE Base",
        "m2m:ae":  "Application Entity",
        "m2m:csr": "Remote CSE",
      }[data.resourceType] || data.resourceType || "";

      showInfoPanel(
        resourceName || "IN-CSE",
        `<div class="wfInfoType">${typeLabel}</div>
         <table class="wfInfoTable"><tbody>${rows}</tbody></table>`
      );
    } catch (e) {
      showInfoPanel(resourceName || "IN-CSE",
        `<div class="wfInfoError">⚠ Request failed: ${e}</div>`);
    }
  }
  // ─────────────────────────────────────────────────────────────

  function ensureCytoscape() {
    if (cy || !window.cytoscape || !cyContainer) return;

    cy = window.cytoscape({
      container: cyContainer,
      elements: [],
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#ffffff",
            "border-width": 3,
            "border-color": "#1b1b1b",
            "shape": "roundrectangle",
            "width": 170,
            "height": 68,
            "label": "data(label)",
            "text-wrap": "wrap",
            "text-max-width": 140,
            "text-valign": "center",
            "text-halign": "center",
            "font-size": 13,
            "font-weight": 800,
            "color": "#1b1b1b",
            "padding": "10px",
          },
        },
        {
          selector: 'node[type = "in"]',
          style: { "background-color": "#2d6cdf", "color": "#ffffff" },
        },
        {
          selector: 'node[type = "mn"]',
          style: { "background-color": "#2ca24d", "color": "#ffffff" },
        },
        {
          selector: 'node[type = "ae"]',
          style: {
            "background-color": "#d72d2d",
            "color": "#ffffff",
            "width": 145,
            "height": 56,
          },
        },
        {
          selector: "edge",
          style: {
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "line-color": "#1b1b1b",
            "target-arrow-color": "#1b1b1b",
            "width": 3,
          },
        },
      ],
      layout: {
        name: "breadthfirst",
        directed: true,
        roots: ["in-cse"],
        padding: 40,
        spacingFactor: 1.25,
        animate: false,
      },
      wheelSensitivity: 0.18,
    });

    cy.on("tap", "node", (event) => {
      const data = event.target.data();
      setStatus(data.statusText || data.label);
      fetchNodeInfo(data.type, data.resourceName);
    });
  }

  function topologyElements() {
    const elements = [
      {
        data: {
          id: "in-cse",
          label: "IN-CSE\norchestration AE",
          type: "in",
          resourceName: "",
          statusText: "IN-CSE / Orchestrator node",
        },
      },
    ];

    state.topology.cses.forEach((cse) => {
      const labelParts = [cse.name || "MN-CSE"];
      if (cse.cseID) labelParts.push(`ID: ${cse.cseID}`);
      if (cse.port) labelParts.push(`Port: ${cse.port}`);

      elements.push({
        data: {
          id: cse.nodeId,
          label: labelParts.join("\n"),
          type: "mn",
          resourceName: cse.name || "",
          statusText:
            `${cse.name || "MN-CSE"}` +
            `${cse.cseID ? ` (${cse.cseID})` : ""}` +
            `${cse.port ? ` on port ${cse.port}` : ""}`,
        },
      });

      elements.push({
        data: {
          id: `reg-${cse.nodeId}`,
          source: "in-cse",
          target: cse.nodeId,
          type: "registration",
        },
      });
    });

    state.topology.aes.forEach((ae) => {
      if (ae.name === "CAdmin") return;

      elements.push({
        data: {
          id: ae.nodeId,
          label: ae.name || "AE",
          type: "ae",
          resourceName: ae.name || "",
          statusText: `AE: ${ae.name || "AE"}`,
        },
      });

      elements.push({
        data: {
          id: `edge-${ae.parentNodeId}-${ae.nodeId}`,
          source: ae.parentNodeId,
          target: ae.nodeId,
          type: "ae-link",
        },
      });
    });

    return elements;
  }

  function renderTopology() {
    ensureCytoscape();
    if (!cy) { setStatus("Cytoscape failed to load."); return; }
    cy.elements().remove();
    cy.add(topologyElements());
    cy.layout({
      name: "breadthfirst",
      directed: true,
      roots: ["in-cse"],
      padding: 40,
      spacingFactor: 1.25,
      animate: false,
    }).run();
  }

  async function fetchJson(url, options = {}) {
    try {
      const res = await fetch(url, options);
      const text = await res.text();
      try {
        return JSON.parse(text);
      } catch {
        return {
          success: false,
          message: `Server returned non-JSON response (status ${res.status})`,
          raw_response: text.slice(0, 500),
        };
      }
    } catch (e) {
      return { success: false, message: String(e) };
    }
  }

  async function fetchTopologyFromBackend() {
    const result = await fetchJson("/api/topology/");
    if (result.success && result.topology) {
      return normalizeTopology(result.topology);
    }
    return null;
  }

  async function syncTopologyFromBackend(silent = false) {
    const topology = await fetchTopologyFromBackend();
    if (!topology) {
      if (!silent) setStatus("Failed to sync topology from backend");
      return false;
    }
    const currentVersion = state.topology.version || 0;
    applyTopology(topology);
    if (!silent && topology.version !== currentVersion) {
      setStatus("Topology synced from backend");
    }
    return true;
  }

  function startTopologyPolling() {
    if (topologyPollTimer) return;
    topologyPollTimer = window.setInterval(() => {
      syncTopologyFromBackend(true);
    }, 3000);
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
  }

  function refreshAeTargetHint(root) {
    const hint = root.querySelector("#aeTargetHint");
    if (!hint) return;
    const parent = latestCse();
    if (!parent) {
      hint.textContent = "No CSE deployed yet — AE will attach to IN-CSE.";
      return;
    }
    hint.textContent =
      `New AEs will attach to: ${parent.name}` +
      `${parent.cseID ? ` (${parent.cseID})` : ""}`;
  }

  async function provision_host() {
    return await fetchJson("/api/provision/host/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
  }

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
      btn.addEventListener("click", async () => {
        state.host.deployedAction = btn.dataset.action;
        markSelected(root, state.host.deployedAction);
        if (btn.dataset.action === "deploy_local") {
          try {
            const data = await provision_host();

            if (data.success) {
              enableBackToTopology("Host deployed locally");
            } else {
              enableBackToTopology("Deployment failed");
            }
          } catch (err) {
            console.error(err);
            enableBackToTopology("Error deploying host");
          }
        } else {
          enableBackToTopology(`Host step saved (${btn.textContent.trim()})`);
        }
        //enableBackToTopology(`Host step saved (${btn.textContent.trim()})`);
      });
    });
  }

  async function sendDataToGateway(data) {
    return await fetchJson("/api/gateway/data/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  async function sendCommandToGateway(payload) {
    return await fetchJson("/api/gateway/command/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  function bindCSE(root) {
    const name = root.querySelector('input[name="cse_name"]');
    const cseId = root.querySelector('input[name="cse_id"]');
    const port = root.querySelector('input[name="cse_port"]');
    const dockerName = root.querySelector('input[name="cse_docker_name"]');
    const extra = root.querySelector('input[name="cse_extra"]');

    name.value = state.cse.name;
    cseId.value = state.cse.cseID;
    port.value = state.cse.port;
    dockerName.value = state.cse.dockerName;
    extra.value = state.cse.extra;

    name.addEventListener("input", () => (state.cse.name = name.value));
    cseId.addEventListener("input", () => (state.cse.cseID = cseId.value));
    port.addEventListener("input", () => (state.cse.port = port.value));
    dockerName.addEventListener("input", () => (state.cse.dockerName = dockerName.value));
    extra.addEventListener("input", () => (state.cse.extra = extra.value));

    if (state.cse.deployedAction) markSelected(root, state.cse.deployedAction);

    root.querySelectorAll(".wfAction").forEach((btn) => {
      btn.addEventListener("click", async () => {
        state.cse.deployedAction = btn.dataset.action;
        markSelected(root, state.cse.deployedAction);

        const payload = {
          cseName: (state.cse.name || "").trim(),
          localPort: (state.cse.port || "").trim(),
          cseID: (state.cse.cseID || "").trim(),
          dockerName: (state.cse.dockerName || "").trim(),
          deployType: btn.textContent.trim(),
        };

        if (btn.dataset.action === "deploy_cse_acme") {
          setStatus("Sending MN-CSE details to Gateway...");
          const result = await sendDataToGateway(payload);

          if (!result.success) {
            setStatus(
              "Failed: " +
              (result.message || "Unknown") +
              (result.data_cse_response ? ` (${result.data_cse_response.slice(0, 80)}…)` : "") +
              (result.cmd_cse_response ? ` (${result.cmd_cse_response.slice(0, 80)}…)` : "")
            );
            return;
          }

          if (result.topology) {
            applyTopology(result.topology);
          } else {
            await syncTopologyFromBackend(true);
          }

          enableBackToTopology("MN-CSE added to topology • click \"Back to Topology\"");
          return;
        }

        await syncTopologyFromBackend(true);
        enableBackToTopology(`CSE step saved (${btn.textContent.trim()})`);
      });
    });
  }

  function bindAE(root) {
    const name = root.querySelector('input[name="ae_name"]');
    const extra = root.querySelector('input[name="ae_extra"]');

    name.value = state.ae.name;
    extra.value = state.ae.extra;
    refreshAeTargetHint(root);

    name.addEventListener("input", () => (state.ae.name = name.value));
    extra.addEventListener("input", () => (state.ae.extra = extra.value));

    if (state.ae.deployedAction) markSelected(root, state.ae.deployedAction);

    root.querySelectorAll(".wfAction").forEach((btn) => {
      btn.addEventListener("click", async () => {
        state.ae.deployedAction = btn.dataset.action;
        markSelected(root, state.ae.deployedAction);

        const parent = latestCse();
        if (!parent) {
          setStatus("Deploy a CSE first so the AE has somewhere to attach.");
          refreshAeTargetHint(root);
          return;
        }

        const payload = {
          command: "execute",
          aeName: (state.ae.name || "").trim(),
          parentNodeId: parent.nodeId,
          cseID: parent.cseID || "",
          deployType: btn.textContent.trim(),
        };

        if (btn.dataset.action === "deploy_sample_ae") {
          setStatus("Sending execute command to Gateway...");
          const result = await sendCommandToGateway(payload);

          if (!result.success) {
            setStatus(
              "Failed: " +
              (result.message || "Unknown") +
              (result.cse_response ? ` (${result.cse_response.slice(0, 80)}…)` : "")
            );
            return;
          }

          if (result.topology) {
            applyTopology(result.topology);
          } else {
            await syncTopologyFromBackend(true);
          }

          enableBackToTopology("AE added to topology • click \"Back to Topology\"");
          return;
        }

        await syncTopologyFromBackend(true);
        enableBackToTopology(`AE step saved (${btn.textContent.trim()})`);
      });
    });
  }

  document.querySelectorAll(".wfNavItem").forEach((btn) => {
    btn.addEventListener("click", () => openModal(btn.dataset.open));
  });

  btnCloseX.addEventListener("click", closeModal);
  btnClose.addEventListener("click", closeModal);

  btnBackTopo.addEventListener("click", async () => {
    if (btnBackTopo.dataset.ready !== "1") return;
    closeModal();
    await syncTopologyFromBackend(true);
    setStatus("Topology updated");
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  renderTopology();
  updateMeta();
  setStatus("Topology ready");
  syncTopologyFromBackend(true);
  startTopologyPolling();
})();