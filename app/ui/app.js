/*
 * Gayatri Platform v4.0.1 — UI Application Script
 * Extracted from index.html (single-file refactor).
 *
 * NOT a module: the script intentionally registers classic globals
 * (switchNav, selectCourse, sendMessage, setDemoCaption, ...) because
 * scripts/record_demo_video.py, record_teacher_demo.py, and
 * record_institution_demo.py call setDemoCaption() via page.evaluate(),
 * and index.html inline onclick handlers invoke the other functions.
 * Logic is unchanged from the v4.0.0 inline <script> block.
 */

// Tab switching
function switchNav(tabId, btn) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  const target = document.getElementById('tab-' + tabId);
  if (target) target.classList.add('active');
  if (btn) btn.classList.add('active');
  if (tabId === 'courses') renderCourses();
  if (tabId === 'progress') refreshAnalytics();
}

// Default courses fallback data
let coursesData = [
  { id: "engineering_mathematics", code: "MATH201", title: "Engineering Mathematics", description: "Foundational mathematical techniques: ODEs, Laplace transforms, Fourier series.", module_count: 4, card_count: 4, is_optional: false },
  { id: "digital_electronics", code: "EC202", title: "Digital Electronics", description: "Digital logic: Boolean algebra, universal gates, combinational and sequential logic.", module_count: 4, card_count: 4, is_optional: false },
  { id: "chemistry_optional", code: "CHEM101", title: "Senior Secondary Chemistry", description: "Optional legacy showcase covering thermodynamics and chemical bonding.", module_count: 2, card_count: 1, is_optional: true }
];

let currentCourseId = "engineering_mathematics";

// Async UI state (v4.0.1 protocol): turns and curriculum indexing execute on a
// background QThreadPool in the Python bridge and deliver through signals
// (responseReady / curriculumIngested) — the window never freezes while waiting.
let turnPending = false;
// Set when a turn payload actually arrived via responseReady. Guards the race
// where the (fast) turn signal lands before the sendQuery acknowledgment is
// processed — the queued ack must not re-enter "thinking" afterwards.
let turnDelivered = false;
let ingestPending = false;

function setThinking(on) {
  const status = document.getElementById('chatStatus');
  const sendBtn = document.getElementById('chatSendBtn');
  if (status) status.innerText = on ? 'Gayatri is thinking…' : 'Socratic Tutor Active';
  if (sendBtn) sendBtn.disabled = on;
}

function renderChatError(res) {
  const err = (res && res.error) || {};
  const parts = ['Something went wrong.'];
  if (err.message) parts.push(err.message);
  const text = parts.join(' ');
  appendMsg(text, 'bot');
  const box = document.getElementById('chatMessages');
  if (box && err.ref) {
    // Correlation id lives in the DOM title only; chat stays clean.
    const last = box.lastElementChild;
    if (last) last.setAttribute('title', `Log reference: ${err.ref}`);
  }
}

// Signal handlers — registered once the web channel is ready (see window.onload).
function handleResponseReady(payloadStr) {
  let res = payloadStr;
  try {
    res = typeof payloadStr === 'string' ? JSON.parse(payloadStr) : payloadStr;
  } catch (e) {
    console.error('Malformed turn payload from bridge.', e);
    return;
  }
  turnPending = false;
  turnDelivered = true;
  setThinking(false);
  if (res && res.success) {
    renderTutorResponse(res);
    refreshAnalytics(res.course_id || currentCourseId);
  } else {
    renderChatError(res);
  }
}

function handleCurriculumIngested(payloadStr) {
  let result = payloadStr;
  try {
    result = typeof payloadStr === 'string' ? JSON.parse(payloadStr) : payloadStr;
  } catch (e) {
    console.error('Malformed ingestion payload from bridge.', e);
    return;
  }
  ingestPending = false;
  const status = document.getElementById('ingestStatus');
  if (!status) return;
  if (result && result.success) {
    status.style.color = '#27c93f';
    status.innerText = `Indexed ${result.chunks_indexed} cards from ${result.filename} into ${currentCourseId}.`;
  } else if (result && result.error) {
    status.style.color = '#e94560';
    status.innerText = result.error.message || 'The document could not be indexed.';
    if (result.error.ref) console.log('Ingestion error reference:', result.error.ref);
  }
}

function renderCourses() {
  const grid = document.getElementById('courseGrid');
  grid.replaceChildren();
  coursesData.forEach(c => {
    const card = document.createElement('div');
    card.className = 'course-card' + (c.id === currentCourseId ? ' active-card' : '');
    card.innerHTML = `
      <div class="course-header">
        <span class="course-code">${escapeHTML(c.code)}</span>
        ${c.is_optional ? '<span style="font-size:10px; color:#f5c542; background:rgba(245,197,66,0.1); padding:2px 6px; border-radius:4px;">Optional</span>' : ''}
      </div>
      <div class="course-title">${escapeHTML(c.title)}</div>
      <div class="course-desc">${escapeHTML(c.description)}</div>
      <div class="course-meta">
        <span>📖 ${parseInt(c.module_count, 10) || 0} Modules</span>
        <span>🔍 ${parseInt(c.card_count, 10) || 0} RAG Cards</span>
      </div>
      <button class="btn-primary" style="margin-top:auto;" onclick="selectCourse('${escapeHTML(c.id)}')">
        ${c.id === currentCourseId ? '✓ Active Course' : 'Switch to Course'}
      </button>
    `;
    grid.appendChild(card);
  });
}

function selectCourse(courseId) {
  currentCourseId = courseId;
  const c = coursesData.find(x => x.id === courseId);
  if (c) {
    const hcn = document.getElementById('headerCourseName');
    if (hcn) hcn.innerText = c.title;
    const cct = document.getElementById('chatCourseTitle');
    if (cct) cct.innerText = c.title;
    const wcn = document.getElementById('welcomeCourseName');
    if (wcn) wcn.innerText = c.title;
    const valSub = document.getElementById('valSubject');
    if (valSub) valSub.innerText = c.code;
  }
  renderCourses();
  clearChat();
  if (window.bridge && typeof window.bridge.switchCourse === 'function') {
    window.bridge.switchCourse(courseId);
    refreshAnalytics(courseId);
  }
  switchNav('tutor');
}

function handleKey(e) {
  if (e.key === 'Enter') sendMessage();
}

function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text || turnPending) return;
  input.value = '';

  // Append user msg
  appendMsg(text, 'user');

  // Call bridge (async protocol) or standalone fallback
  if (window.bridge && typeof window.bridge.sendQuery === 'function') {
    turnPending = true;
    setThinking(true);
    turnDelivered = false;

    // QWebChannel resolves @Slot(result=str) invocations as Promises whose
    // RESOLVED VALUE is the raw JSON *string* the Python slot returned.
    // Normalize every shape (object / string / Promise result) into an object
    // BEFORE branch evaluation — otherwise a bare string matches no branch and
    // execution falls through (the double-render bug: a fake "runtime
    // connection required" message stacked on top of the real answer).
    const normalizeAck = (raw) => {
      if (typeof raw === 'string') {
        try { return JSON.parse(raw); } catch (e) { return null; }
      }
      return raw;
    };

    const genericFailure = () => ({
      success: false,
      error: { code: 'internal_error', message: 'Something went wrong while processing your request. Please try again shortly.' }
    });

    const processAck = (rawAck) => {
      const ack = normalizeAck(rawAck);

      if (!ack || typeof ack !== 'object') {
        // Malformed acknowledgment while the bridge IS connected: surface the
        // honest error envelope — NEVER the offline fallback message.
        turnPending = false;
        setThinking(false);
        renderChatError(genericFailure());
        return;
      }
      if (ack.success === false) {
        turnPending = false;
        setThinking(false);
        renderChatError(ack);
        return;
      }
      // Queued acknowledgment: the completed turn arrives via
      // bridge.responseReady → handleResponseReady. Keep waiting — but never
      // re-enter "thinking" if the (fast) turn already delivered.
      if (ack.queued === true && ack.success === true) {
        if (!turnDelivered) { turnPending = true; setThinking(true); }
        return;
      }
      // Defensive: legacy inline completion (payload already final).
      if (ack.success === true && ack.message) {
        turnPending = false;
        setThinking(false);
        renderTutorResponse(ack);
        refreshAnalytics(ack.course_id || currentCourseId);
        return;
      }
      // Unknown shape — same honest error treatment.
      turnPending = false;
      setThinking(false);
      renderChatError(genericFailure());
    };

    let ack = null;
    try {
      ack = window.bridge.sendQuery(text, 'demo_student');
    } catch (e) {
      ack = null;
    }

    if (ack && typeof ack.then === 'function') {
      // Promise-shaped return: processAck receives the resolved raw value and
      // normalizes it itself (it may be the JSON string, object, or undefined).
      ack.then(processAck).catch((e) => {
        turnPending = false;
        setThinking(false);
        console.error('Bridge sendQuery promise rejected.', e);
        renderChatError(genericFailure());
      });
    } else {
      processAck(ack);
    }
  } else {
    // Fallback for standalone demo inspection (HTML opened without the runtime)
    setTimeout(() => {
      simulateResponse(text);
    }, 300);
  }
}

function setDemoCaption(text) {
  const bar = document.getElementById('demo-caption-bar');
  const txt = document.getElementById('demo-caption-text');
  if (!bar || !txt) return;
  if (!text) {
    bar.classList.add('hidden');
  } else {
    txt.innerText = text;
    bar.classList.remove('hidden');
  }
}

function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatMarkdown(text) {
  if (!text) return '';
  // Escape all HTML to prevent script/tag injection before markdown formatting
  const safe = escapeHTML(text);
  return safe
    .replace(/^### (.*$)/gim, '<h4 style="margin: 8px 0 4px 0; color: #38bdf8; font-size: 14px;">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 style="margin: 10px 0 4px 0; color: #38bdf8; font-size: 15px;">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

function appendMsg(text, sender) {
  const box = document.getElementById('chatMessages');
  const msg = document.createElement('div');
  msg.className = 'msg msg-' + (sender === 'user' ? 'user' : 'bot');
  msg.innerHTML = formatMarkdown(text);
  box.appendChild(msg);
  box.scrollTop = box.scrollHeight;
}

function renderTutorResponse(res) {
  appendMsg(res.message, 'bot');
  const evidenceList = document.getElementById('evidenceList');
  const badge = document.getElementById('groundingBadge');
  evidenceList.replaceChildren();

  if (res.evidence_cards && res.evidence_cards.length > 0) {
    badge.style.display = 'inline-flex';
    document.getElementById('evidenceCount').textContent = `${res.evidence_cards.length} cards`;
    res.evidence_cards.forEach(card => {
      const cDiv = document.createElement('div');
      cDiv.className = 'evidence-card';
      const tDiv = document.createElement('div');
      tDiv.className = 'evidence-card-title';
      tDiv.textContent = card.title || '';
      const bDiv = document.createElement('div');
      bDiv.className = 'evidence-card-content';
      bDiv.textContent = card.content || '';
      cDiv.append(tDiv, bDiv);
      evidenceList.appendChild(cDiv);
    });
  } else {
    badge.style.display = 'none';
    document.getElementById('evidenceCount').textContent = '0 cards';
    const emptyP = document.createElement('p');
    emptyP.style.cssText = 'font-size: 12px; color: #64748b;';
    emptyP.textContent = 'Response synthesized via general pedagogical guidance.';
    evidenceList.appendChild(emptyP);
  }

  if (res.misconception) {
    const valMisc = document.getElementById('valMisconceptions');
    if (valMisc) valMisc.textContent = res.misconception;
    const valAct = document.getElementById('valAction');
    if (valAct) valAct.textContent = "Remediate: " + res.misconception;
  }
}

function simulateResponse(text) {
  renderTutorResponse({
    message: "Gayatri desktop runtime connection required for interactive pedagogical inference.",
    evidence_cards: []
  });
}

function clearChat() {
  const box = document.getElementById('chatMessages');
  const hName = document.getElementById('headerCourseName');
  const title = hName ? hName.textContent : 'Course';
  box.innerHTML = `<div class="msg msg-bot">Session context refreshed for <strong>${escapeHTML(title)}</strong>. What would you like to explore?</div>`;
  document.getElementById('evidenceList').innerHTML = '<p style="font-size: 12px; color: #64748b;">Submit a query to inspect real-time RAG grounding cards and source citations.</p>';
  document.getElementById('groundingBadge').style.display = 'none';
  turnPending = false;
  turnDelivered = false;
  ingestPending = false;
  setThinking(false);
}

function refreshAnalytics(courseId = currentCourseId) {
  if (!window.bridge || typeof window.bridge.getAnalytics !== 'function') return;
  window.bridge.getAnalytics(courseId, 'demo_student', function(payload) {
    try {
      const state = typeof payload === 'string' ? JSON.parse(payload) : payload;
      document.getElementById('valMastery').innerText = `${Math.round(state.overall_mastery * 100)}%`;
      const course = coursesData.find(item => item.id === courseId);
      document.getElementById('valSubject').innerText = course ? course.code : courseId;
      document.getElementById('valMisconceptions').innerText = `${(state.recent_misconceptions || []).length} Detected`;
      document.getElementById('valAction').innerText = state.recommended_next_action || 'Continue guided practice';

      const breakdown = document.getElementById('masteryBreakdown');
      breakdown.replaceChildren();
      const topics = Object.entries(state.topic_mastery || {});
      if (topics.length === 0) {
        const empty = document.createElement('p');
        empty.innerText = 'No topic-level mastery data yet.';
        breakdown.appendChild(empty);
      }
      topics.forEach(([topic, score]) => {
        const row = document.createElement('div');
        const label = document.createElement('div');
        label.style.cssText = 'display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;';
        const name = document.createElement('span');
        name.innerText = topic;
        const value = document.createElement('span');
        value.innerText = `${Math.round(score * 100)}%`;
        label.append(name, value);
        const track = document.createElement('div');
        track.style.cssText = 'height:6px;background:#0f172a;border-radius:3px;overflow:hidden;';
        const bar = document.createElement('div');
        bar.style.cssText = `width:${Math.max(0, Math.min(100, score * 100))}%;height:100%;background:#27c93f;`;
        track.appendChild(bar);
        row.append(label, track);
        breakdown.appendChild(row);
      });
    } catch (error) {
      console.error('Could not render mastery analytics:', error);
    }
  });
}

function uploadCurriculum() {
  const status = document.getElementById('ingestStatus');
  if (!window.bridge || typeof window.bridge.selectAndUploadCurriculum !== 'function') {
    status.style.color = '#f5c542';
    status.innerText = 'Curriculum upload is available in the desktop app.';
    return;
  }
  if (ingestPending) return;

  ingestPending = true;
  status.style.color = '#94a3b8';
  status.innerText = 'Selecting a document — indexing runs in the background…';

  let ack = null;
  try {
    ack = window.bridge.selectAndUploadCurriculum(currentCourseId);
  } catch (e) {
    ack = null;
  }
  if (typeof ack === 'string') {
    try { ack = JSON.parse(ack); } catch (e) { ack = null; }
  }

  if (!ack || ack.success !== true) {
    ingestPending = false;
    if (ack && ack.cancelled) {
      status.style.color = '#94a3b8';
      status.innerText = 'Upload cancelled.';
    } else {
      const msg = (ack && ack.error && ack.error.message) || 'The upload could not be started.';
      status.style.color = '#e94560';
      status.innerText = msg;
      if (ack && ack.error && ack.error.ref) console.log('Ingestion error reference:', ack.error.ref);
    }
    return;
  }
  if (ack.filename) {
    status.style.color = '#94a3b8';
    status.innerText = `Indexing "${ack.filename}" — this may take a few seconds…`;
  }
}

function startGuidedShowcase() {
  selectCourse('engineering_mathematics');
  setTimeout(() => {
    document.getElementById('chatInput').value = "Explain first-order differential equations";
    sendMessage();
  }, 400);
}

// Window controls
function minWindow() { if (window.bridge) window.bridge.minimizeWindow(); }
function maxWindow() { if (window.bridge) window.bridge.maximizeWindow(); }
function closeWindow() { if (window.bridge) window.bridge.closeWindow(); }

// Init WebChannel
window.onload = function() {
  renderCourses();
  if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, function(channel) {
      window.bridge = channel.objects.bridge;
      // Wire the async delivery signals before bootstrapping course data.
      if (window.bridge.responseReady && window.bridge.responseReady.connect) {
        window.bridge.responseReady.connect(handleResponseReady);
      }
      if (window.bridge.curriculumIngested && window.bridge.curriculumIngested.connect) {
        window.bridge.curriculumIngested.connect(handleCurriculumIngested);
      }
      window.bridge.listCourses(function(payload) {
        try {
          coursesData = typeof payload === 'string' ? JSON.parse(payload) : payload;
          const initialCourse = coursesData.find(course => course.code === 'MATH201') || coursesData[0];
          if (initialCourse) {
            currentCourseId = initialCourse.id;
            document.getElementById('headerCourseName').innerText = initialCourse.title;
            document.getElementById('chatCourseTitle').innerText = initialCourse.title;
            document.getElementById('welcomeCourseName').innerText = initialCourse.title;
            document.getElementById('valSubject').innerText = initialCourse.code;
            renderCourses();
            refreshAnalytics(currentCourseId);
          }
        } catch (error) {
          console.error('Could not load courses from the desktop bridge:', error);
        }
      });
    });
  }
};
