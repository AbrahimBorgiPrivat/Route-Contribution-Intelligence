window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"]],
  },
  options: {
    skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"],
  },
  chtml: {
    scale: 1,
  },
};

const SITE = {
  name: "Route Contribution Intelligence",
  subtitle: "Economic outlier detection through graph theory and route optimization",
  author: "Author: Abrahim Borgi, Senior Buisness Analyst",
  footer: "Route Contribution Intelligence",
  sections: [
    {
      id: "introduction",
      title: "Introduction",
      items: [
        {
          label: "The Problem",
          href: "introduction.html",
          page: "introduction",
          desc: "Why the route question is economic, not statistical.",
        },
      ],
    },
    {
      id: "theory",
      title: "Theory",
      items: [
        {
          label: "Graphs & Routes",
          href: "theory.html#graphs-routes-economics",
          page: "theory",
          hash: "#graphs-routes-economics",
          desc: "How the route becomes a graph with measurable structure.",
        },
        {
          label: "Contribution Margin",
          href: "theory.html#contribution-margin",
          page: "theory",
          hash: "#contribution-margin",
          desc: "How route length and revenue become one economic score.",
        },
        {
          label: "Economic Outlier Definition",
          href: "theory.html#economic-outlier-definition",
          page: "theory",
          hash: "#economic-outlier-definition",
          desc: "Threshold, significance and superset logic.",
        },
      ],
    },
    {
      id: "solution",
      title: "Solution",
      items: [
        {
          label: "Type 1 - Fixed Sequence",
          href: "fixed-sequence.html#type-1-fixed-sequence",
          page: "fixed-sequence",
          hash: "#type-1-fixed-sequence",
          desc: "Evaluate removal without changing order.",
        },
        {
          label: "Type 2 - Optimized Sequence",
          href: "fixed-sequence.html#type-2-optimized-sequence",
          page: "fixed-sequence",
          hash: "#type-2-optimized-sequence",
          desc: "Let the remaining route be re-solved.",
        },
        {
          label: "Route Solvers",
          href: "fixed-sequence.html#route-solvers",
          page: "fixed-sequence",
          hash: "#route-solvers",
          desc: "Which solver families support Type 1 and Type 2 evaluation.",
        },
        {
          label: "Exact Search",
          href: "fixed-sequence.html#exact-search",
          page: "fixed-sequence",
          hash: "#exact-search",
          desc: "The fully implemented theoretical reference.",
        },
        {
          label: "Hybrid Search",
          href: "fixed-sequence.html#hybrid-search",
          page: "fixed-sequence",
          hash: "#hybrid-search",
          desc: "Heuristic expansion after the exact core.",
          children: [
            {
              label: "Peripheral Clusters",
              href: "fixed-sequence.html#peripheral-clusters",
              page: "fixed-sequence",
              hash: "#peripheral-clusters",
              desc: "Greedy geometric groups near the route boundary.",
            },
            {
              label: "Marginal Blocks",
              href: "fixed-sequence.html#marginal-blocks",
              page: "fixed-sequence",
              hash: "#marginal-blocks",
              desc: "Contiguous low-margin windows along the route.",
            },
            {
              label: "Union-based Expansion",
              href: "fixed-sequence.html#union-expansion",
              page: "fixed-sequence",
              hash: "#union-expansion",
              desc: "Combine promising subsets into larger candidates.",
            },
            {
              label: "Beam Search",
              href: "fixed-sequence.html#beam-search",
              page: "fixed-sequence",
              hash: "#beam-search",
              desc: "Expand promising subsets without exploding the search.",
            },
          ],
        },
        {
          label: "Outlier Engine",
          href: "fixed-sequence.html#outlier-engine",
          page: "fixed-sequence",
          hash: "#outlier-engine",
          desc: "How subsets are scored, filtered and classified.",
        },
        {
          label: "Complexity & Guarantees",
          href: "fixed-sequence.html#complexity-guarantees",
          page: "fixed-sequence",
          hash: "#complexity-guarantees",
          desc: "What stays exact and what becomes heuristic.",
        },
      ],
    },
    {
      id: "implementation",
      title: "Implementation",
      items: [
        {
          label: "Architecture",
          href: "implementation.html#architecture",
          page: "implementation",
          hash: "#architecture",
          desc: "How the modules fit together in code.",
        },
        {
          label: "Distance Matrices",
          href: "implementation.html#distance-matrix",
          page: "implementation",
          hash: "#distance-matrix",
          desc: "OSRM, routed distances and cached matrices.",
        },
        {
          label: "Algorithm Integration",
          href: "implementation.html#algorithm-integration",
          page: "implementation",
          hash: "#algorithm-integration",
          desc: "How the software system calls the algorithmic layer.",
        },
        {
          label: "Configuration",
          href: "implementation.html#configuration",
          page: "implementation",
          hash: "#configuration",
          desc: "Runtime settings, problem types and solver choices.",
        },
        {
          label: "Visual Representation",
          href: "implementation.html#visual-representation",
          page: "implementation",
          hash: "#visual-representation",
          desc: "Maps, route pages and KPI-oriented output.",
        },
      ],
    },
    {
      id: "example",
      title: "Example",
      items: [
        {
          label: "Data",
          href: "example.html#data",
          page: "example",
          hash: "#data",
          desc: "Input sources and scenario-specific demo data.",
        },
        {
          label: "Static",
          href: "example.html#static",
          page: "example",
          hash: "#static",
          desc: "Static presentation output for the demo route case.",
        },
        {
          label: "Application",
          href: "example.html#application",
          page: "example",
          hash: "#application",
          desc: "Interactive application output for the same scenario.",
        },
        {
          label: "How to Use the Solution",
          href: "example.html#how-to-use-the-solution",
          page: "example",
          hash: "#how-to-use-the-solution",
          desc: "How to read the outputs from scenario view to stop-level explanation.",
        },
      ],
    },
    {
      id: "demo",
      title: "Demo",
      items: [
        {
          label: "Interactive application",
          href: "../../views/application/demo_bus_routes_nyc/html/index.html",
          desc: "Multi-scenario interactive demo.",
        },
        {
          label: "Single-scenario application",
          href: "../../views/application/demo_bus_routes_nyc_single_scenario/html/index.html",
          desc: "Fixed New York bus-route scenario.",
        },
        {
          label: "Static presentation",
          href: "../../views/static/demo_bus_routes_nyc/index.html",
          desc: "Rendered static overview output.",
        },
      ],
    },
    {
      id: "article",
      title: "Article",
      items: [
        {
          label: "Article",
          href: "article.html",
          page: "article",
          desc: "The written article introducing the method and results.",
        },
      ],
    },
  ],
};

const SECTION_STATE_KEY = "route-coverage-sidebar-sections";

function currentPageKey() {
  return document.body.dataset.page || "index";
}

function currentHash() {
  return (window.location.hash || "").toLowerCase();
}

function setSidebarState() {
  const saved = localStorage.getItem("route-coverage-sidebar-collapsed");
  if (saved === "true") {
    document.body.dataset.sidebarCollapsed = "true";
  }
}

function readSectionState() {
  try {
    return JSON.parse(localStorage.getItem(SECTION_STATE_KEY) || "{}");
  } catch {
    return {};
  }
}

function writeSectionState(state) {
  localStorage.setItem(SECTION_STATE_KEY, JSON.stringify(state));
}

function itemIsActive(item, activePage, activeHash) {
  if (item.page !== activePage) {
    return false;
  }

  if (item.children && item.children.length) {
    if (item.hash && item.hash.toLowerCase() === activeHash) {
      return true;
    }

    return item.children.some((child) => child.hash && child.hash.toLowerCase() === activeHash);
  }

  return !item.hash || item.hash.toLowerCase() === activeHash;
}

function linkClass(item, activePage, activeHash) {
  return itemIsActive(item, activePage, activeHash) ? "active" : "";
}

function sectionHasActive(section, activePage, activeHash) {
  return section.items.some((item) => {
    if (item.page === activePage) {
      if (!item.hash || item.hash.toLowerCase() === activeHash || !activeHash) {
        return true;
      }
    }

    if (itemIsActive(item, activePage, activeHash)) {
      return true;
    }

    return Boolean(
      item.children &&
      item.children.some((child) => itemIsActive(child, activePage, activeHash))
    );
  });
}

function sectionIsOpen(section, activePage, activeHash, sectionState, sidebarCollapsed) {
  if (sidebarCollapsed) {
    return true;
  }

  if (Object.prototype.hasOwnProperty.call(sectionState, section.id)) {
    return Boolean(sectionState[section.id]);
  }

  return sectionHasActive(section, activePage, activeHash);
}

function renderSidebar() {
  const sidebar = document.querySelector("[data-sidebar]");
  if (!sidebar) {
    return;
  }

  const activePage = currentPageKey();
  const activeHash = currentHash();
  const sectionState = readSectionState();
  const sidebarCollapsed = document.body.dataset.sidebarCollapsed === "true";
  const html = [];

  html.push(`
    <div class="sidebar-top">
      <a class="brand brand-link" href="index.html">
        <div class="brand-name">${SITE.name}</div>
        <div class="brand-tag">${SITE.subtitle}</div>
      </a>
    </div>
  `);

  SITE.sections.forEach((section) => {
    const sectionActive = sectionHasActive(section, activePage, activeHash) ? "active" : "";
    const open = sectionIsOpen(section, activePage, activeHash, sectionState, sidebarCollapsed);
    const sectionHref = (section.items[0]?.href || "#").split("#")[0];
    html.push(`
      <div class="section-block ${open ? "is-open" : ""}">
        <div class="section-heading">
          <a class="section-link ${sectionActive}" href="${sectionHref}">${section.title}</a>
          <button
            class="section-toggle"
            type="button"
            data-section-toggle="${section.id}"
            aria-label="Toggle ${section.title} section"
            aria-expanded="${open ? "true" : "false"}">
            <span class="section-chevron" aria-hidden="true"></span>
          </button>
        </div>
    `);
    html.push(`<div class="nav-group" data-section-panel="${section.id}" ${open ? "" : "hidden"}>`);

    section.items.forEach((item) => {
      const active = linkClass(item, activePage, activeHash);
      html.push(`
        <a class="nav-link ${active}" href="${item.href}">
          <div class="nav-dot"></div>
          <div class="nav-body">
            <div class="nav-title">${item.label}</div>
            <div class="nav-desc">${item.desc || ""}</div>
          </div>
        </a>
      `);

      if (item.children && item.children.length) {
        html.push(`<div class="nav-child">`);
        item.children.forEach((child) => {
          const childActive = linkClass(child, activePage, activeHash);
          html.push(`
            <a class="nav-link ${childActive}" href="${child.href}">
              <div class="nav-dot"></div>
              <div class="nav-body">
                <div class="nav-title">${child.label}</div>
                <div class="nav-desc">${child.desc || ""}</div>
              </div>
            </a>
          `);
        });
        html.push(`</div>`);
      }
    });

    html.push(`</div></div>`);
  });

  sidebar.innerHTML = html.join("");
  bindSidebarSectionToggles(sidebar);
}

function bindSidebarSectionToggles(sidebar) {
  sidebar.querySelectorAll("[data-section-toggle]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();

      const sectionId = button.dataset.sectionToggle;
      const sectionState = readSectionState();
      const expanded = button.getAttribute("aria-expanded") === "true";
      sectionState[sectionId] = !expanded;
      writeSectionState(sectionState);
      renderSidebar();
    });
  });
}

function renderTopbar() {
  const topbar = document.querySelector("[data-topbar]");
  if (!topbar) {
    return;
  }

  const title = document.body.dataset.pageTitle || SITE.name;
  const subtitle = document.body.dataset.pageSubtitle || "";

  topbar.innerHTML = `
    <div class="topbar-title">
      <h1>${title}</h1>
      <p>${subtitle}</p>
      <p>${SITE.author}</p>
    </div>
    <div class="topbar-actions">
      <button class="icon-button" type="button" data-sidebar-toggle>Menu</button>
      <img class="topbar-logo" src="assets/logo.png" alt="Logo">
    </div>
  `;
}

function renderFooter() {
  const footer = document.querySelector("[data-footer]");
  if (!footer) {
    return;
  }

  const year = new Date().getFullYear();
  footer.textContent = `${SITE.footer} - ${SITE.author} - ${year}`;
}

function loadMathJax() {
  if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
    window.MathJax.typesetPromise();
    return;
  }

  if (document.querySelector('script[data-mathjax-loader="true"]')) {
    return;
  }

  const script = document.createElement("script");
  script.dataset.mathjaxLoader = "true";
  script.async = true;
  script.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js";
  script.onload = () => {
    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
      window.MathJax.typesetPromise();
    }
  };
  document.head.appendChild(script);
}

function setupImageZoom() {
  const images = Array.from(document.querySelectorAll(".prose figure img"));
  if (!images.length) {
    return;
  }

  let lightbox = document.querySelector("[data-image-lightbox]");

  if (!lightbox) {
    lightbox = document.createElement("div");
    lightbox.className = "image-lightbox";
    lightbox.dataset.imageLightbox = "true";
    lightbox.hidden = true;
    lightbox.innerHTML = `
      <div class="image-lightbox-dialog" role="dialog" aria-modal="true" aria-label="Expanded figure">
        <button class="image-lightbox-close" type="button" aria-label="Close image view">Close</button>
        <img alt="">
        <div class="image-lightbox-caption"></div>
      </div>
    `;
    document.body.appendChild(lightbox);
  }

  const lightboxImage = lightbox.querySelector("img");
  const lightboxCaption = lightbox.querySelector(".image-lightbox-caption");
  const closeButton = lightbox.querySelector(".image-lightbox-close");
  let lastTrigger = null;

  function closeLightbox() {
    lightbox.classList.remove("is-open");
    window.setTimeout(() => {
      lightbox.hidden = true;
    }, 180);
    document.body.style.overflow = "";
    if (lastTrigger) {
      lastTrigger.focus();
    }
  }

  function openLightbox(image) {
    lastTrigger = image;
    lightboxImage.src = image.currentSrc || image.src;
    lightboxImage.alt = image.alt || "";
    const caption = image.closest("figure")?.querySelector("figcaption")?.textContent?.trim() || image.alt || "";
    lightboxCaption.textContent = caption;
    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
    requestAnimationFrame(() => {
      lightbox.classList.add("is-open");
    });
    closeButton.focus();
  }

  images.forEach((image) => {
    image.classList.add("zoomable-image");
    image.tabIndex = 0;
    image.setAttribute("role", "button");
    image.setAttribute("aria-label", `${image.alt || "Figure"} (click to enlarge)`);
    image.addEventListener("click", () => openLightbox(image));
    image.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openLightbox(image);
      }
    });
  });

  closeButton.addEventListener("click", closeLightbox);

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !lightbox.hidden) {
      closeLightbox();
    }
  });
}

function wireEvents() {
  document.querySelectorAll("[data-sidebar-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const isMobile = window.matchMedia("(max-width: 980px)").matches;

      if (isMobile) {
        const open = document.body.dataset.sidebarOpen === "true";
        document.body.dataset.sidebarOpen = open ? "false" : "true";
        return;
      }

      const collapsed = document.body.dataset.sidebarCollapsed === "true";
      document.body.dataset.sidebarCollapsed = collapsed ? "false" : "true";
      localStorage.setItem("route-coverage-sidebar-collapsed", String(!collapsed));
      renderSidebar();
    });
  });

  document.addEventListener("click", (event) => {
    const link = event.target.closest(".sidebar a");
    if (!link) {
      return;
    }
    if (window.matchMedia("(max-width: 980px)").matches) {
      document.body.dataset.sidebarOpen = "false";
    }
  });

  window.addEventListener("resize", () => {
    if (!window.matchMedia("(max-width: 980px)").matches) {
      document.body.dataset.sidebarOpen = "false";
    }
  });

  window.addEventListener("hashchange", () => {
    renderSidebar();
  });
}

function init() {
  setSidebarState();
  renderSidebar();
  renderTopbar();
  renderFooter();
  wireEvents();
  setupImageZoom();
  loadMathJax();
}

document.addEventListener("DOMContentLoaded", init);
