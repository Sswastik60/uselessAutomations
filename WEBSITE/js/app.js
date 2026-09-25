/**
 * Automation Hub — Official Website Interactions
 * Performance-first vanilla JavaScript:
 * - Live Mode Execution Pipeline Simulator
 * - Global Browser Keyboard Shortcut Listeners (Ctrl+Alt+G, Ctrl+Alt+X, etc.)
 * - Scroll-driven floating pill navigation
 * - Interactive Product Showcase tab switcher
 * - Tactile micro-interactions & Web Audio synthesized feedback
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initSignatureSimulator();
  initShowcaseTabs();
  initGlobalHotkeys();
  initTactileFeedback();
});

/* ==========================================================================
   1. Floating Pill Navigation & Scroll Spy
   ========================================================================== */

function initNavigation() {
  const navWrapper = document.getElementById('mainNav');
  if (!navWrapper) return;

  const handleScroll = () => {
    if (window.scrollY > 50) {
      navWrapper.classList.add('scrolled');
    } else {
      navWrapper.classList.remove('scrolled');
    }
  };

  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        const navHeight = 80;
        const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight;
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

/* ==========================================================================
   2. Signature Interaction Pipeline Simulator
   ========================================================================== */

const MODE_CONFIGS = {
  guitar: {
    id: 'guitar_mode',
    name: 'Guitar Mode',
    icon: '🎸',
    hotkey: 'CTRL + ALT + G',
    keyCombo: ['Ctrl', 'Alt', 'G'],
    steps: [
      { name: 'Detect Audio Interface', detail: "Scarlett 2i2 USB (WASAPI)", time: '42ms' },
      { name: 'Set Audio Output', detail: "Studio Headphones (Direct Monitor)", time: '88ms' },
      { name: 'Launch FL Studio', detail: "FL64.exe (PID 27616)", time: '110ms' },
      { name: 'Open Guitar Project', detail: "Lead_Practice_Template.flp", time: '120ms' },
      { name: 'Notify Ready', detail: "Acrylic Toast: 'Guitar practice setup ready!'", time: '20ms' }
    ],
    totalTime: '0.38s'
  },
  gaming: {
    id: 'gaming_mode',
    name: 'Gaming Mode',
    icon: '🎮',
    hotkey: 'CTRL + ALT + X',
    keyCombo: ['Ctrl', 'Alt', 'X'],
    steps: [
      { name: 'Configure Audio', detail: "Spatial Audio Headset (Dolby Atmos)", time: '52ms' },
      { name: 'Launch Steam', detail: "Steam Client Bootstrap", time: '94ms' },
      { name: 'Launch Discord', detail: "Discord.exe & Auto-Join Voice", time: '105ms' },
      { name: 'Minimize Background', detail: "Minimize All Windows (Win+M)", time: '40ms' },
      { name: 'Notify Ready', detail: "Acrylic Toast: 'Gaming setup initiated.'", time: '18ms' }
    ],
    totalTime: '0.31s'
  },
  coding: {
    id: 'coding_mode',
    name: 'Coding Mode',
    icon: '💻',
    hotkey: 'CTRL + ALT + C',
    keyCombo: ['Ctrl', 'Alt', 'C'],
    steps: [
      { name: 'Launch VS Code', detail: "Code.exe in Project Workspace", time: '75ms' },
      { name: 'Launch Terminal', detail: "Windows Terminal (PowerShell 7)", time: '60ms' },
      { name: 'Focus Window', detail: "SetForegroundWindow -> Code", time: '45ms' },
      { name: 'Open Browser URL', detail: "http://localhost:3000 (F11 Fullscreen)", time: '90ms' },
      { name: 'Notify Ready', detail: "Acrylic Toast: 'Development workspace ready.'", time: '15ms' }
    ],
    totalTime: '0.29s'
  },
  study: {
    id: 'study_mode',
    name: 'Study Mode',
    icon: '📚',
    hotkey: 'CTRL + ALT + S',
    keyCombo: ['Ctrl', 'Alt', 'S'],
    steps: [
      { name: 'Launch Spotify', detail: "Spotify.exe & Resume Deep Focus", time: '82ms' },
      { name: 'Silence Background', detail: "Mute Non-Essential Audio", time: '35ms' },
      { name: 'Minimize Distractions', detail: "Minimize Non-Active Windows", time: '45ms' },
      { name: 'Notify Ready', detail: "Acrylic Toast: 'Focus environment prepared.'", time: '18ms' }
    ],
    totalTime: '0.24s'
  }
};

let currentSimulationTimeout = null;
let isSimulating = false;

function initSignatureSimulator() {
  const triggerBtn = document.getElementById('simTriggerBtn');
  const simStepsList = document.getElementById('simStepsList');
  const simReadyBanner = document.getElementById('simReadyBanner');
  const simStatusText = document.getElementById('simStatusText');
  const simModeBadge = document.getElementById('simModeBadge');
  const simHotkeysContainer = document.getElementById('simHotkeysContainer');

  if (!triggerBtn || !simStepsList) return;

  function renderMode(modeKey) {
    const config = MODE_CONFIGS[modeKey] || MODE_CONFIGS.guitar;

    // Update keys
    if (simHotkeysContainer) {
      simHotkeysContainer.innerHTML = config.keyCombo
        .map(k => `<span class="sim-key">${k}</span>`)
        .join('<span style="color: #64748b; font-size: 11px;">+</span>');
    }

    // Update badge
    if (simModeBadge) {
      simModeBadge.innerHTML = `<span class="badge-icon">${config.icon}</span> <span>${config.name}</span>`;
    }

    // Update steps list
    simStepsList.innerHTML = config.steps.map((step, idx) => `
      <li class="sim-step-item" id="simStep_${idx}">
        <div class="step-left">
          <div class="step-check">✓</div>
          <div>
            <div class="step-name">${step.name}</div>
            <div class="step-detail">${step.detail}</div>
          </div>
        </div>
        <div class="step-time">${step.time}</div>
      </li>
    `).join('');

    if (simReadyBanner) {
      simReadyBanner.classList.remove('visible');
    }

    if (simStatusText) {
      simStatusText.textContent = `Ready to execute (${config.hotkey})`;
    }
  }

  window.runSimulation = function(modeKey = 'guitar') {
    if (isSimulating) return;
    isSimulating = true;

    const config = MODE_CONFIGS[modeKey] || MODE_CONFIGS.guitar;
    renderMode(modeKey);

    // Visual key press animation
    const keys = simHotkeysContainer.querySelectorAll('.sim-key');
    keys.forEach(k => k.classList.add('pressed'));
    playSyntheticClick();

    setTimeout(() => {
      keys.forEach(k => k.classList.remove('pressed'));
    }, 200);

    if (simStatusText) {
      simStatusText.innerHTML = `<span style="color: #0a84ff;">●</span> Preparing your setup...`;
    }

    // Step-by-step pipeline sequence
    const stepElements = config.steps.map((_, idx) => document.getElementById(`simStep_${idx}`));
    const stepDelay = 220;

    stepElements.forEach((el, index) => {
      setTimeout(() => {
        if (index > 0 && stepElements[index - 1]) {
          stepElements[index - 1].classList.remove('active');
          stepElements[index - 1].classList.add('completed');
        }
        if (el) {
          el.classList.add('active');
          playSyntheticTick();
        }

        // Final step completion
        if (index === stepElements.length - 1) {
          setTimeout(() => {
            el.classList.remove('active');
            el.classList.add('completed');

            if (simReadyBanner) {
              simReadyBanner.classList.add('visible');
              simReadyBanner.querySelector('.sim-ready-metric').textContent = `Elapsed: ${config.totalTime} • 0 errors`;
            }

            if (simStatusText) {
              simStatusText.innerHTML = `<span style="color: #22c55e;">✓</span> Setup complete & active`;
            }

            // Sync with hero app HUD
            updateHeroAppHud(config);

            playSyntheticSuccess();
            isSimulating = false;
          }, stepDelay);
        }
      }, index * stepDelay);
    });
  };

  triggerBtn.addEventListener('click', () => {
    window.runSimulation('guitar');
  });

  // Render initial Guitar Mode
  renderMode('guitar');

  // Connect hero mode cards to trigger simulation
  document.querySelectorAll('.app-mode-card').forEach(card => {
    card.addEventListener('click', function() {
      const modeKey = this.getAttribute('data-mode') || 'guitar';
      
      // Update visual selection on app mockup
      document.querySelectorAll('.app-mode-card').forEach(c => c.classList.remove('triggered'));
      this.classList.add('triggered');

      // Scroll smoothly to signature interaction section
      const sigSection = document.getElementById('interaction');
      if (sigSection) {
        const topPos = sigSection.getBoundingClientRect().top + window.pageYOffset - 80;
        window.scrollTo({ top: topPos, behavior: 'smooth' });
      }

      setTimeout(() => {
        window.runSimulation(modeKey);
      }, 400);
    });
  });
}

function updateHeroAppHud(config) {
  const hudTitle = document.getElementById('heroHudTitle');
  const hudSub = document.getElementById('heroHudSub');
  const hudTime = document.getElementById('heroHudTime');
  const hudPulse = document.getElementById('heroHudPulse');

  if (hudTitle) hudTitle.textContent = `${config.icon} ${config.name} Active`;
  if (hudSub) hudSub.textContent = `All ${config.steps.length} actions completed with non-blocking feedback`;
  if (hudTime) hudTime.textContent = config.totalTime;
  if (hudPulse) {
    hudPulse.classList.add('running');
    setTimeout(() => hudPulse.classList.remove('running'), 2000);
  }
}

/* ==========================================================================
   3. Global Hotkey Listeners on Webpage
   ========================================================================== */

function initGlobalHotkeys() {
  window.addEventListener('keydown', (e) => {
    // Intercept Ctrl+Alt combinations
    if (e.ctrlKey && e.altKey) {
      const key = e.key.toUpperCase();
      if (key === 'G') {
        e.preventDefault();
        scrollToAndRun('guitar');
      } else if (key === 'X') {
        e.preventDefault();
        scrollToAndRun('gaming');
      } else if (key === 'C') {
        e.preventDefault();
        scrollToAndRun('coding');
      } else if (key === 'S') {
        e.preventDefault();
        scrollToAndRun('study');
      }
    }
  });

  function scrollToAndRun(modeKey) {
    const target = document.getElementById('interaction');
    if (target) {
      const topPos = target.getBoundingClientRect().top + window.pageYOffset - 80;
      window.scrollTo({ top: topPos, behavior: 'smooth' });
    }
    setTimeout(() => {
      if (window.runSimulation) {
        window.runSimulation(modeKey);
      }
    }, 350);
  }
}

/* ==========================================================================
   4. Interactive Showcase Tabs
   ========================================================================== */

function initShowcaseTabs() {
  const tabButtons = document.querySelectorAll('.showcase-tab-btn');
  const tabPanes = document.querySelectorAll('.showcase-tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabTarget = btn.getAttribute('data-tab');

      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const activePane = document.getElementById(`tab_${tabTarget}`);
      if (activePane) {
        activePane.classList.add('active');
      }

      playSyntheticClick();
    });
  });
}

/* ==========================================================================
   5. Tactile Web Audio Micro-Sound Synthesis
   ========================================================================== */

let audioCtx = null;

function getAudioContext() {
  if (!audioCtx && (window.AudioContext || window.webkitAudioContext)) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContextClass();
  }
  return audioCtx;
}

function playSyntheticClick() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(320, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(140, ctx.currentTime + 0.04);
    gain.gain.setValueAtTime(0.04, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.04);
  } catch (err) {
    // Non-critical audio feedback
  }
}

function playSyntheticTick() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(480, ctx.currentTime);
    gain.gain.setValueAtTime(0.02, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.03);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.03);
  } catch (err) {}
}

function playSyntheticSuccess() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(520, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(780, ctx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.05, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.14);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.14);
  } catch (err) {}
}

function initTactileFeedback() {
  document.querySelectorAll('.btn, .app-mode-card, .showcase-tab-btn').forEach(el => {
    el.addEventListener('mouseenter', () => {
      // Subtle tactile hover feedback
    });
  });
}
