(() => {
    const outputBox = document.getElementById("outputBox");
    const regBadge = document.getElementById("regBadge");
  
    // Default IN-CSE values (prefill when clicking IN-CSE)
    const defaultINCSE = {
      in_base_url: "http://localhost:8080/~/id-in/cse-in",
      in_cse_id: "/id-in",
      in_cse_rn: "cse-in",
      admin_originator: "CAdmin",
      ae_rn: "orchestratorAE",
    };
  
    // Simple UI state stored in browser (still not backend)
    const state = {
      registered: false,
      in: { ...defaultINCSE },
    };
  
    function setOutput(obj) {
      outputBox.textContent = JSON.stringify(obj, null, 2);
    }
  
    function updateBadge() {
      if (state.registered) {
        regBadge.textContent = "Registered";
        regBadge.classList.remove("badge-off");
        regBadge.classList.add("badge-on");
      } else {
        regBadge.textContent = "Not registered";
        regBadge.classList.remove("badge-on");
        regBadge.classList.add("badge-off");
      }
    }
  
    function openModal(id) {
      const m = document.querySelector(id);
      m.classList.add("open");
      m.setAttribute("aria-hidden", "false");
    }
  
    function closeModal(id) {
      const m = document.querySelector(id);
      m.classList.remove("open");
      m.setAttribute("aria-hidden", "true");
    }
  
    // Buttons: Register/Unregister (UI only)
    document.getElementById("btnRegister").addEventListener("click", () => {
      state.registered = true;
      updateBadge();
      setOutput({ action: "register", result: "UI only", registered: true });
    });
  
    document.getElementById("btnUnregister").addEventListener("click", () => {
      state.registered = false;
      updateBadge();
      setOutput({ action: "unregister", result: "UI only", registered: false });
    });
  
    // IN-CSE button: open prefilled form
    document.getElementById("btnShowINCSE").addEventListener("click", () => {
      const form = document.getElementById("formINCSE");
      Object.entries(state.in).forEach(([k, v]) => {
        const el = form.elements.namedItem(k);
        if (el) el.value = v;
      });
      openModal("#modalINCSE");
    });
  
    // Save IN-CSE (UI only)
    document.getElementById("btnSaveINCSE").addEventListener("click", () => {
      const form = document.getElementById("formINCSE");
      state.in = {
        in_base_url: form.in_base_url.value.trim(),
        in_cse_id: form.in_cse_id.value.trim(),
        in_cse_rn: form.in_cse_rn.value.trim(),
        admin_originator: form.admin_originator.value.trim(),
        ae_rn: form.ae_rn.value.trim(),
      };
      setOutput({ action: "save_in_cse", result: "UI only", in_cse: state.in });
      closeModal("#modalINCSE");
    });
  
    // Deploy MN button: open empty form
    document.getElementById("btnShowMN").addEventListener("click", () => {
      const form = document.getElementById("formMN");
      form.reset(); // empty on purpose
      openModal("#modalMN");
    });
  
    // Apply MN (UI only)
    document.getElementById("btnApplyMN").addEventListener("click", () => {
      const f = document.getElementById("formMN");
      const payload = {
        image: f.image.value.trim(),
        container_name: f.container_name.value.trim(),
        host_port: f.host_port.value.trim(),
        container_port: f.container_port.value.trim(),
        mn_cse_id: f.mn_cse_id.value.trim(),
        mn_cse_rn: f.mn_cse_rn.value.trim(),
        registrar_url: f.registrar_url.value.trim(),
        registrar_cse_id: f.registrar_cse_id.value.trim(),
        registrar_cse_rn: f.registrar_cse_rn.value.trim(),
      };
      setOutput({ action: "deploy_mn_cse", result: "UI only", payload });
      closeModal("#modalMN");
    });
  
    // Close modal buttons
    document.querySelectorAll("[data-close]").forEach((btn) => {
      btn.addEventListener("click", () => closeModal(btn.getAttribute("data-close")));
    });
  
    // Click outside modal closes
    document.querySelectorAll(".modal").forEach((m) => {
      m.addEventListener("click", (e) => {
        if (e.target === m) closeModal("#" + m.id);
      });
    });
  
    // Init
    updateBadge();
    setOutput({ info: "UI loaded", in_cse_defaults: state.in, registered: state.registered });
  })();
  