// Fetch the latest release from GitHub and rewrite the download buttons
// to point straight at the actual installer / portable assets.
//
// If the API call fails (rate limit, no releases yet, offline), we leave the
// fallback /releases/latest links in place — they still work.
const REPO = "sandeepbollavaram/image_editor_python";

async function loadLatest() {
  try {
    const res = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
      headers: { "Accept": "application/vnd.github+json" }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    apply(data);
  } catch (err) {
    console.warn("Could not load latest release:", err);
    document.getElementById("release-meta").textContent =
      "Could not load the latest release. Use the buttons to browse releases on GitHub.";
  }
}

function fmtBytes(n) {
  if (!Number.isFinite(n)) return "";
  const mb = n / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(n / 1024).toFixed(0)} KB`;
}

function fmtDate(s) {
  try { return new Date(s).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }); }
  catch { return s; }
}

function apply(release) {
  const version = (release.tag_name || "").replace(/^v/, "");
  if (version) document.getElementById("latest-version").textContent = version;

  const installer = (release.assets || []).find(a => /Vibrance_Setup.*\.exe$/i.test(a.name));
  const portable  = (release.assets || []).find(a => /^Vibrance\.exe$/i.test(a.name));

  const meta = document.getElementById("release-meta");
  meta.innerHTML =
    `Vibrance <strong>${version || release.tag_name || ""}</strong>` +
    ` · released ${fmtDate(release.published_at)}` +
    ` · <a href="${release.html_url}" target="_blank" rel="noopener">release notes</a>`;

  if (installer) {
    const url = installer.browser_download_url;
    document.getElementById("download-primary").setAttribute("href", url);
    document.getElementById("download-installer").setAttribute("href", url);
    document.getElementById("installer-meta").textContent =
      `${installer.name} · ${fmtBytes(installer.size)}`;
  }
  if (portable) {
    document.getElementById("download-portable").setAttribute("href", portable.browser_download_url);
    document.getElementById("portable-meta").textContent =
      `${portable.name} · ${fmtBytes(portable.size)}`;
  }
}

loadLatest();
