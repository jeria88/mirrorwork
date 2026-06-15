
// ==========================================================================
   // THREE.JS KEPLERIAN BLACK HOLE SIMULATION
   // ==========================================================================
   // Three.js loaded as global from CDN script tag
   // Use THREE directly - addons may not be available as globals
   // Fallback: create stubs if addons not loaded
   var EffectComposer = THREE.EffectComposer || function(){};
   var RenderPass = THREE.RenderPass || function(){};
   var UnrealBloomPass = THREE.UnrealBloomPass || function(){};

   // Configuración de Presets por Sección (Alineados con mirrorwork/base.html)
   const PRESETS = {
     desktop: {
       landing:      { bhr: 4.0, density: 0.22, sizeMult: 2.20, bloom: 7.5, speedInner: 1.80, speedOuter: 0.04, camZ: 180, camAng: 8  },
       feed:         { bhr: 4.0, density: 0.35, sizeMult: 1.70, bloom: 6.5, speedInner: 2.10, speedOuter: 0.04, camZ: 140, camAng: 20 },
       inbox:        { bhr: 4.0, density: 0.25, sizeMult: 1.70, bloom: 6.0, speedInner: 2.10, speedOuter: 0.04, camZ: 140, camAng: 20 },
       suenos:       { bhr: 4.0, density: 0.32, sizeMult: 1.80, bloom: 6.0, speedInner: 3.05, speedOuter: 0.05, camZ: 149, camAng: 16 },
       mapainterior: { bhr: 4.0, density: 0.55, sizeMult: 1.40, bloom: 5.0, speedInner: 2.00, speedOuter: 0.05, camZ: 118, camAng: 32 },
       regulacion:   { bhr: 4.0, density: 0.15, sizeMult: 2.50, bloom: 8.5, speedInner: 1.00, speedOuter: 0.02, camZ: 130, camAng: 45 },
       espejo:       { bhr: 4.0, density: 0.18, sizeMult: 2.40, bloom: 9.5, speedInner: 4.50, speedOuter: 0.05, camZ: 149, camAng: 85 },
       saas:         { bhr: 4.0, density: 0.50, sizeMult: 1.65, bloom: 5.8, speedInner: 2.30, speedOuter: 0.05, camZ: 125, camAng: 35 },
       perfil:       { bhr: 4.0, density: 0.28, sizeMult: 1.90, bloom: 7.0, speedInner: 1.50, speedOuter: 0.03, camZ: 160, camAng: 12 },
       general:      { bhr: 4.0, density: 0.32, sizeMult: 1.80, bloom: 6.0, speedInner: 3.05, speedOuter: 0.05, camZ: 149, camAng: 16 },
       transition:   { bhr: 4.0, density: 0.65, sizeMult: 3.50, bloom: 16.0, speedInner: 12.0, speedOuter: 0.50, camZ: 50, camAng: 40 }
     }
   };

   let scene, camera, renderer, composer, bloomPass;
   let particleMaterial, particleField;
   let clock, mouseX = 0, mouseY = 0, targetX = 0, targetY = 0;
   
   let currentPreset = { ...PRESETS.desktop.landing };
   let targetPreset = { ...PRESETS.desktop.landing };
   let lerpBoost = 0;
let scrollY = 0; 
let mainContent = document.querySelector('.app-main-content');
if(mainContent) {
    mainContent.addEventListener('scroll', () => { scrollY = mainContent.scrollTop; });
} else {
    window.addEventListener('scroll', () => { scrollY = window.scrollY; });
}



   function initCosmos() {
     const container = document.getElementById('cosmos-bg-container');
     if (!container) return;

     // Escena y Cámara
     scene = new THREE.Scene();
     camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 3000);
     camera.position.set(0, 20, 180);

     // WebGL Renderer con Alpha para overlays
     renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false });
     renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
     renderer.setSize(window.innerWidth, window.innerHeight);
     renderer.domElement.id = 'bh-canvas';
     container.appendChild(renderer.domElement);

     // Post-procesamiento Bloom
     composer = new EffectComposer(renderer);
     composer.addPass(new RenderPass(scene, camera));
     bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 6.0, 0.70, 0.04);
     composer.addPass(bloomPass);

     // Inicialización de Campo Kepleriano (190,000 Partículas)
     const BH_R = 8, N = 190000, R_MIN = BH_R * 1.15, R_MAX = 130;
     const geometry = new THREE.BufferGeometry();
     
     const positions = new Float32Array(N * 3);
     const colors = new Float32Array(N * 3);
     const angles = new Float32Array(N);
     const radii = new Float32Array(N);
     const speeds = new Float32Array(N);
     const sizes = new Float32Array(N);
     const randoms = new Float32Array(N);

     for (let i = 0; i < N; i++) {
       // Distribución radial concentrada cerca del horizonte de sucesos
       let r = Math.random() < 0.72
         ? R_MIN + Math.pow(Math.random(), 2.0) * 52
         : 52 + Math.random() * (R_MAX - 52);

       const a = Math.random() * Math.PI * 2;
       const norm = (r - R_MIN) / (R_MAX - R_MIN);
       const y = (Math.random() - 0.5) * r * (0.04 + norm * 0.55);

       positions[i*3]   = Math.cos(a) * r;
       positions[i*3+1] = y;
       positions[i*3+2] = Math.sin(a) * r;

       // Color base grisáceo / estelar con desaturación
       const brightness = Math.max(0.18, 1.0 - norm * 0.82);
       colors[i*3] = colors[i*3+1] = colors[i*3+2] = brightness;

       angles[i] = a;
       radii[i] = r;
       // Velocidad angular kepleriana: v ~ 1/sqrt(r)
       speeds[i] = (1.0 / Math.sqrt(r)) * 2.4 * (0.85 + Math.random() * 0.30);
       sizes[i]  = 0.10 + norm * norm * 2.80 + Math.random() * (0.20 + norm * 1.0);
       randoms[i] = Math.random();
     }

     geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
     geometry.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
     geometry.setAttribute('aAngle',   new THREE.BufferAttribute(angles, 1));
     geometry.setAttribute('aRadius',  new THREE.BufferAttribute(radii, 1));
     geometry.setAttribute('aSpeed',   new THREE.BufferAttribute(speeds, 1));
     geometry.setAttribute('aSize',    new THREE.BufferAttribute(sizes,  1));
     geometry.setAttribute('aRand',    new THREE.BufferAttribute(randoms, 1));

     // Shader Material Personalizado para distorsión temporal
     particleMaterial = new THREE.ShaderMaterial({
       uniforms: {
         uTime:       { value: 0 },
         uBHR:        { value: currentPreset.bhr },
         uSpeedInner: { value: currentPreset.speedInner },
         uSpeedOuter: { value: currentPreset.speedOuter },
         uSizeMult:   { value: currentPreset.sizeMult },
         uDensity:    { value: currentPreset.density }
       },
       vertexShader: `
         uniform float uTime, uBHR, uSpeedInner, uSpeedOuter, uSizeMult, uDensity;
         attribute float aAngle, aRadius, aSpeed, aSize, aRand;
         varying vec3 vColor;
         void main() {
           if (aRand > uDensity || aRadius < uBHR) {
             gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
             gl_PointSize = 0.0;
             return;
           }
           vColor = color;
           float norm = clamp((aRadius - 9.2) / (130.0 - 9.2), 0.0, 1.0);
           float speedMult = mix(uSpeedInner, uSpeedOuter, norm);
           float a = aAngle - uTime * aSpeed * speedMult;
           
           vec3 p = position;
           p.x = cos(a) * aRadius;
           p.z = sin(a) * aRadius;
           p.y += sin(a * 3.0 + aRadius * 0.10) * (aRadius * 0.006);
           
           vec4 mv = modelViewMatrix * vec4(p, 1.0);
           gl_PointSize = aSize * uSizeMult * (120.0 / -mv.z);
           gl_Position = projectionMatrix * mv;
         }
       `,
       fragmentShader: `
         varying vec3 vColor;
         void main() {
           vec2 uv = gl_PointCoord - 0.5;
           float d = length(uv);
           if (d > 0.5) discard;
           gl_FragColor = vec4(vColor, smoothstep(0.5, 0.04, d) * 0.92);
         }
       `,
       transparent: true,
       blending: THREE.AdditiveBlending,
       depthWrite: false,
       vertexColors: true
     });

     particleField = new THREE.Points(geometry, particleMaterial);
     particleField.rotation.x = 0.10;
     particleField.rotation.z = -0.03;
     scene.add(particleField);

     clock = new THREE.Clock();

     // Eventos de Mouse e interacción
     document.addEventListener('mousemove', (e) => {
       mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
       mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
     });

     // Evento de redimensión
     window.addEventListener('resize', onWindowResize);

     // Loop de Animación
     animate();
   }

   function onWindowResize() {
     camera.aspect = window.innerWidth / window.innerHeight;
     camera.updateProjectionMatrix();
     renderer.setSize(window.innerWidth, window.innerHeight);
     composer.setSize(window.innerWidth, window.innerHeight);
   }

   function lerp(a, b, t) {
     return a + (b - a) * t;
   }

   function animate() {
     requestAnimationFrame(animate);
     const elapsed = clock.getElapsedTime();

     // Suavizar inputs de mouse
     targetX += (mouseX - targetX) * 0.038;
     targetY += (mouseY - targetY) * 0.038;

     // Lerp dinámico de presets
     lerpBoost = Math.max(0, lerpBoost - 0.008);
     const L = 0.018 + (0.12 - 0.018) * lerpBoost;

     currentPreset.bhr        = lerp(currentPreset.bhr,        targetPreset.bhr,        L);
     currentPreset.density    = lerp(currentPreset.density,    targetPreset.density,    L);
     currentPreset.sizeMult   = lerp(currentPreset.sizeMult,   targetPreset.sizeMult,   L);
     currentPreset.bloom      = lerp(currentPreset.bloom,      targetPreset.bloom,      L);
     currentPreset.speedInner = lerp(currentPreset.speedInner, targetPreset.speedInner, L);
     currentPreset.speedOuter = lerp(currentPreset.speedOuter, targetPreset.speedOuter, L);
     currentPreset.camZ       = lerp(currentPreset.camZ,       targetPreset.camZ,       L);
     currentPreset.camAng     = lerp(currentPreset.camAng,     targetPreset.camAng,     L);

     // Aplicar uniformes actualizados al Shader
     particleMaterial.uniforms.uBHR.value        = currentPreset.bhr;
     particleMaterial.uniforms.uDensity.value    = currentPreset.density;
     particleMaterial.uniforms.uSizeMult.value   = currentPreset.sizeMult;
     particleMaterial.uniforms.uSpeedInner.value = currentPreset.speedInner;
     particleMaterial.uniforms.uSpeedOuter.value = currentPreset.speedOuter;
     bloomPass.strength                          = currentPreset.bloom;

     // Movimiento orbital de la cámara
     let maxScroll = (mainContent ? mainContent.scrollHeight - mainContent.clientHeight : document.body.scrollHeight - window.innerHeight);
     let ratio = Math.max(0, Math.min(scrollY / (maxScroll || 1), 1.0));
     
     let isLanding = document.getElementById('page-landing').classList.contains('active');
     
     let effectiveAng = currentPreset.camAng;
     let effectiveZ = currentPreset.camZ;
     
     if (isLanding) {
         effectiveZ = 180 - (ratio * 130); // Zooms in from 180 to 50
     }
     
     const angRad = effectiveAng * Math.PI / 180;
     camera.position.x = Math.sin(elapsed * 0.036) * 3.0 + targetX * 4.5;
     camera.position.y = effectiveZ * Math.sin(angRad) + Math.sin(elapsed * 0.022) * 1.5 - targetY * 2.5;
     camera.position.z = effectiveZ * Math.cos(angRad);
     camera.lookAt(0, 0, 0);

     particleMaterial.uniforms.uTime.value = elapsed;
     composer.render();
   }

   function updateCosmosPreset(presetName) {
     if (PRESETS.desktop[presetName]) {
       targetPreset = { ...PRESETS.desktop[presetName] };
       lerpBoost = 1.0; // Acelera el lerp transitoriamente
     }
   }


    // ==========================================================================
    // INTERACTIVIDAD DE LA APLICACIÓN (FLIGHT DECK CONSOLE & EVENTS)
    // ==========================================================================
    class EndonautasApp {
      constructor() {
        const config = window.ENDONAUTAS_CONFIG || {};
        this.isBitacoraUnlocked = config.isBitacoraUnlocked || false;
        this.completedTests = config.completedTests !== undefined ? config.completedTests : 4;
        this.fractons = config.fractons !== undefined ? config.fractons : 450;
        
        // System telemetry initial parameters
        this.polarities = config.polarities || {
          conciencia: 65,
          apertura: 70,
          rigidez: 45,
          evasion: 55
        };

        this.currentSessionId = null;

        this.initElements();
        this.bindEvents();
        this.setupSomaticResponses();
        
        // Tab routing based on URL hash
        const validTabs = ['feed', 'perfil-social', 'foros', 'inbox', 'perfil', 'mapainterior', 'espejo', 'regulacion', 'suenos', 'saas'];
        const hash = window.location.hash.slice(1);
        if (config.isAuthenticated) {
          this.activeTab = validTabs.includes(hash) ? hash : (config.activeTab || 'feed');
          this.switchTab(this.activeTab);
          // Handle onboarding source from landing login
          if (config.onboardingSource) {
            this.mostrarOnboarding(config.onboardingSource);
          }
        } else {
          this.activeTab = 'landing';
        }

        // Listen for history / hash changes
        window.addEventListener('hashchange', () => {
          const newHash = window.location.hash.slice(1);
          if (config.isAuthenticated && validTabs.includes(newHash) && newHash !== this.activeTab) {
            this.switchTab(newHash);
          }
        });
      }

      initElements() {
        // Tab switching links
        this.menuItems = document.querySelectorAll('.menu-item');
        this.pages = document.querySelectorAll('.app-page');

        // Modal checkout
        this.checkoutModal = document.getElementById('checkout-modal');
        this.btnComprarBitacora = document.getElementById('btn-comprar-bitacora');
        this.btnDesbloquearDirecto = document.getElementById('btn-desbloquear-bitacora-directo');
        this.btnCloseModal = document.getElementById('btn-close-modal');

        // Somatic Chat
        this.chatMessagesBox = document.getElementById('chat-messages-box');
        this.chatTextarea = document.getElementById('chat-textarea');
        this.btnChatSend = document.getElementById('btn-chat-send');
        this.breathingCircle = document.getElementById('breathing-circle');
        this.breathingText = document.getElementById('breathing-text');
        this.breathingBadge = document.getElementById('breathing-telemetry-badge');

        // B2B SaaS
        this.clientItems = document.querySelectorAll('.client-item');

        // Auth Modal & Transitions
        this.authModal = document.getElementById('auth-modal');
        this.transitionOverlay = document.getElementById('transition-overlay');
        this.authForm = document.getElementById('auth-form-element');
      }

      bindEvents() {
        // Tab switches
        this.menuItems.forEach(item => {
          item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.dataset.tab;
            this.switchTab(tab);
          });
        });

        // Checkout triggers
        if (this.btnComprarBitacora) {
          this.btnComprarBitacora.addEventListener('click', () => this.openCheckout());
        }
        if (this.btnDesbloquearDirecto) {
          this.btnDesbloquearDirecto.addEventListener('click', () => this.openCheckout());
        }
        if (this.btnCloseModal) {
          this.btnCloseModal.addEventListener('click', () => this.closeCheckout());
        }

        // SaaS client selection
        this.clientItems.forEach(item => {
          item.addEventListener('click', () => {
            this.clientItems.forEach(ci => ci.classList.remove('active'));
            item.classList.add('active');
            const clientName = item.querySelector('h5').innerText;
            this.showToast(`info`, `Portal Clínico: Visualizando datos de ${clientName}`);
            this.loadClientDetails(item.dataset.client);
          });
        });

        // Theme switcher
        const themeBtn = document.getElementById('theme-toggle');
        if (themeBtn) {
          themeBtn.addEventListener('click', () => {
            const currentTheme = document.body.dataset.theme || 'dark';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.body.dataset.theme = newTheme;
            
            // Toggle icon visibility
            const darkIcon = document.getElementById('theme-toggle-dark-icon');
            const lightIcon = document.getElementById('theme-toggle-light-icon');
            if (darkIcon && lightIcon) {
              if (newTheme === 'light') {
                darkIcon.style.display = 'none';
                lightIcon.style.display = 'block';
              } else {
                darkIcon.style.display = 'block';
                lightIcon.style.display = 'none';
              }
            }
            this.showToast('info', `Interfaz calibrada en modo: ${newTheme === 'light' ? 'Luz / Alta Claridad' : 'Espacio Profundo'}`);
          });
        }

        // Sidebar logout
        const logoutBtn = document.getElementById('sidebar-logout-btn');
        if (logoutBtn) {
          logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.processLogout();
          });
        }

        // Feed post submit
        const postSubmitBtn = document.getElementById('btn-feed-post-submit');
        if (postSubmitBtn) {
          postSubmitBtn.addEventListener('click', () => this.submitFeedPost());
        }

        // Dialog light-dismiss fallback
        if (this.authModal && !('closedBy' in HTMLDialogElement.prototype)) {
          this.authModal.addEventListener('click', (event) => {
            if (event.target !== this.authModal) return;
            const rect = this.authModal.getBoundingClientRect();
            const isDialogContent = (
              rect.top <= event.clientY &&
              event.clientY <= rect.top + rect.height &&
              rect.left <= event.clientX &&
              event.clientX <= rect.left + rect.width
            );
            if (isDialogContent) return;
            this.closeAuthModal();
          });
        }

        // Espejo: chat form submit
        const espejoForm = document.getElementById('espejo-chat-form');
        if (espejoForm) {
          espejoForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendChatMessage();
          });
        }
        // Espejo: allow Ctrl+Enter to send from textarea
        if (this.chatTextarea) {
          this.chatTextarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              this.sendChatMessage();
            }
          });
        }
        // Espejo: Nueva Sesión button
        const btnNuevo = document.getElementById('btn-espejo-nuevo');
        if (btnNuevo) {
          btnNuevo.addEventListener('click', () => {
            this.espejoNuevo().then(data => {
              const box = document.getElementById('chat-messages-box');
              if (box) box.innerHTML = '';
              const titleEl = document.getElementById('espejo-chat-title');
              if (data && data.session_id) {
                this.currentSessionId = data.session_id;
                if (titleEl && data.title) titleEl.textContent = (data.title || '').toUpperCase();
              } else {
                this.currentSessionId = null;
                if (titleEl) titleEl.textContent = 'ESPEJO DE RESONANCIA SOMÁTICA — INTERFAZ TELEMÉTRICA';
              }
              this.addAIMessage('Iniciando secuencia de interacción del Espejo. ¿Dónde se encuentra localizada la molestia física que estás intentando evadir hoy?');
              this.espejoLoadTarjetas();
              this.chatTextarea.disabled = false;
              this.btnChatSend.disabled = false;
              this.chatTextarea.focus();
            }).catch(() => {
              this.showEspejoError('Error al crear nueva sesión.');
            });
          });
        }
      }

      switchTab(tabName) {
        this.activeTab = tabName;

        // Only set hash if user is authenticated and not landing
        if (tabName !== 'landing') {
          window.location.hash = tabName;
        } else {
          window.location.hash = '';
        }

        // Actualizar UI de navegación
        this.menuItems.forEach(item => {
          if (item.dataset.tab === tabName) {
            item.classList.add('active');
          } else {
            item.classList.remove('active');
          }
        });

        // Actualizar páginas visibles
        this.pages.forEach(page => {
          if (page.id === `page-${tabName}`) {
            page.classList.add('active');
          } else {
            page.classList.remove('active');
          }
        });

        // Cambiar preset de animación cósmica
        updateCosmosPreset(tabName);

        // Perfil: ensure edit mode is reset when switching away
        if (tabName !== 'perfil') {
          const actions = document.getElementById('perfil-edit-actions');
          const editBtn = document.getElementById('btn-edit-profile');
          if (actions) actions.style.display = 'none';
          if (editBtn) editBtn.style.display = 'inline-flex';
          ['perfil-first-name', 'perfil-last-name', 'perfil-email', 'perfil-bio'].forEach(id => {
            const el = document.getElementById(id);
            if (el) { el.disabled = true; el.style.background = 'rgba(0,0,0,0.15)'; }
          });
        }

        // Mapa Interior: scroll to top for better UX
        if (tabName === 'mapainterior') {
          const mainContent = document.querySelector('.app-main-content');
          if (mainContent) mainContent.scrollTop = 0;
        }

        // Feed: dynamic refresh from API if needed
        if (tabName === 'feed') {
          const mainContent = document.querySelector('.app-main-content');
          if (mainContent) mainContent.scrollTop = 0;
          // Feed is rendered server-side; optionally refresh from API
          // this.loadFeedFromAPI();
        }

        // Espejo: load tarjetas when switching to this tab
        if (tabName === 'espejo') {
          this.espejoLoadTarjetas();
          // Enable chat input
          if (this.chatTextarea) this.chatTextarea.disabled = false;
          if (this.btnChatSend) this.btnChatSend.disabled = false;
          // If we have a current session loaded, ensure chat is ready
          if (this.currentSessionId) {
            // Session already loaded, just focus
            if (this.chatTextarea) this.chatTextarea.focus();
          } else {
            // Show initial AI greeting
            const box = document.getElementById('chat-messages-box');
            if (box && box.children.length === 0) {
              this.addAIMessage('Iniciando secuencia de interacción del Espejo. ¿Dónde se encuentra localizada la molestia física que estás intentando evadir hoy?');
            }
            if (this.chatTextarea) this.chatTextarea.focus();
          }
        }
      }

      openAuthModal(mode = 'login', source = null) {
        if (!this.authModal) return;
        this.toggleAuthTab(mode);
        // Store the source section for onboarding tracking
        if (source) {
          this.authSource = source;
          const subtitle = document.getElementById('auth-modal-subtitle');
          if (subtitle && mode === 'register') {
            subtitle.innerText = `Crea tu cuenta para acceder a ${source}. Tu onboarding será personalizado.`;
          }
        } else {
          this.authSource = null;
        }
        this.authModal.showModal();
      }

      closeAuthModal() {
        if (!this.authModal) return;
        this.authModal.close();
      }

      toggleAuthTab(mode) {
        const title = document.getElementById('auth-modal-title');
        const subtitle = document.getElementById('auth-modal-subtitle');
        const nameGroup = document.getElementById('group-name');
        const submitBtn = document.getElementById('btn-submit-auth');
        const tabLogin = document.getElementById('tab-login');
        const tabRegister = document.getElementById('tab-register');
        const nameInput = document.getElementById('auth-name');

        if (mode === 'register') {
          if (title) { title.innerText = "Registrarse"; this.authModalTitle = title; }
          if (subtitle) subtitle.innerText = "Crea tu bitácora de conciencia somática.";
          if (nameGroup) { nameGroup.style.display = "flex"; }
          if (nameInput) nameInput.required = true;
          if (submitBtn) submitBtn.innerText = "Registrarse y Entrar";
          if (tabLogin) tabLogin.classList.remove('active');
          if (tabRegister) tabRegister.classList.add('active');
        } else {
          if (title) { title.innerText = "Iniciar Sesión"; this.authModalTitle = title; }
          if (subtitle) subtitle.innerText = "Alinea tu bitácora de conciencia somática.";
          if (nameGroup) { nameGroup.style.display = "none"; }
          if (nameInput) nameInput.required = false;
          if (submitBtn) submitBtn.innerText = "Acceder a la Consola";
          if (tabLogin) tabLogin.classList.add('active');
          if (tabRegister) tabRegister.classList.remove('active');
        }
      }

      processAuth() {
        const emailInput = document.getElementById('auth-email');
        const passwordInput = document.getElementById('auth-password');
        const nameInput = document.getElementById('auth-name');
        const submitBtn = document.getElementById('btn-submit-auth');
        const email = emailInput?.value?.trim() || '';
        const password = passwordInput?.value || '';
        const firstName = nameInput?.value?.trim() || '';
        const isRegister = document.getElementById('tab-register')?.classList.contains('active') || false;

        // Basic validation
        if (!email || !password) {
          this.showToast('error', 'Completa todos los campos obligatorios.');
          return;
        }
        if (isRegister && !firstName) {
          this.showToast('error', 'Ingresa tu nombre.');
          return;
        }
        if (isRegister && password.length < 8) {
          this.showToast('error', 'La contraseña debe tener al menos 8 caracteres.');
          return;
        }

        // Disable button
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerText = 'Procesando...';
        }

        // Show transition overlay while authenticating
        this.closeAuthModal();
        if (this.transitionOverlay) this.transitionOverlay.classList.add('active');
        const msgEl = document.getElementById('transition-message');
        if (msgEl) msgEl.innerText = 'Estabilizando ritmo somático...';
        updateCosmosPreset('transition');

        const endpoint = isRegister ? '/accounts/api/register/' : '/accounts/api/login/';
        const body = isRegister
          ? { email, password, first_name: firstName, onboarding_source: this.authSource || '' }
          : { email, password };

        fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCookie('csrftoken'),
          },
          body: JSON.stringify(body),
        })
        .then(r => r.json())
        .then(data => {
          if (!data.ok) {
            // Hide overlay, show error
            if (this.transitionOverlay) this.transitionOverlay.classList.remove('active');
            this.showToast('error', data.error || 'Error en la autenticación.');
            if (submitBtn) {
              submitBtn.disabled = false;
              submitBtn.innerText = isRegister ? 'Registrarse y Entrar' : 'Acceder a la Consola';
            }
            return;
          }
          // Success! Redirect to app.endonautas.cl with onboarding source
          if (msgEl) msgEl.innerText = '¡Autenticado! Cargando tu espacio...';
          setTimeout(() => {
            const source = this.authSource || '';
            const onboarding = source ? '?onboarding=' + encodeURIComponent(source) : '';
            window.location.href = 'https://app.endonautas.cl/' + onboarding;
          }, 800);
        })
        .catch(() => {
          if (this.transitionOverlay) this.transitionOverlay.classList.remove('active');
          this.showToast('error', 'Error de conexión. Intenta nuevamente.');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = isRegister ? 'Registrarse y Entrar' : 'Acceder a la Consola';
          }
        });
      }

      getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      }

      mostrarOnboarding(source) {
        const sourceMap = {
          'Espejo': 'espejo',
          'Tests': 'mapainterior',
          'Mapa Fractal': 'mapainterior',
        };
        const tab = sourceMap[source] || 'feed';
        this.switchTab(tab);
        const banner = document.createElement('div');
        banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;background:var(--calipso);color:#000;padding:12px 24px;text-align:center;font-weight:600;font-size:0.9rem;';
        banner.innerHTML = `¡Bienvenido! Estás en tu espacio de ${source || 'inicio'}. <a href="#" onclick="this.parentElement.remove();return false;" style="color:#000;margin-left:12px;text-decoration:underline;">Cerrar</a>`;
        document.body.appendChild(banner);
        setTimeout(() => banner.remove(), 8000);
      }

      processLogout() {
        window.location.href = '/accounts/logout/';
      }

      openCheckout() {
        this.checkoutModal.classList.add('active');
      }

      closeCheckout() {
        this.checkoutModal.classList.remove('active');
      }

      processSimulatedPayment() {
        const btn = document.getElementById('btn-submit-payment');
        const originalText = btn.innerText;
        btn.innerText = "Procesando y generando reporte de sombras...";
        btn.disabled = true;

        // Simulación de respuesta de pasarela de pago (Mercado Pago / Hotmart Webhook)
        setTimeout(() => {
          this.isBitacoraUnlocked = true;
          this.closeCheckout();
          
          // Actualizar badges e interfaces
          document.getElementById('bitacora-locked-overlay').style.display = 'none';
          const lockBadge = document.getElementById('bitacora-lock-badge');
          if (lockBadge) lockBadge.remove();

          // Remover banner promocional del dashboard y cambiar diseño
          const promoCard = document.getElementById('bitacora-promo-card');
          if (promoCard) {
            promoCard.innerHTML = `
              <div class="bitacora-promo-content" style="grid-column: 1 / -1; text-align: center;">
                <span class="promo-tag" style="background:var(--calipso-glow); color:var(--calipso); border-color:var(--calipso)">BITÁCORA COMPILADA</span>
                <h3>¡Tu Bitácora de Sombras está desbloqueada!</h3>
                <p>El análisis de tus polaridades de sombra ha sido procesado e integrado en tu perfil.</p>
                <button class="btn btn-primary" onclick="document.getElementById(\'bitacora-locked-overlay\').scrollIntoView({ behavior: \'smooth\', block: \'start\' })">Ver Bitácora</button>
              </div>
            `;
            promoCard.style.borderColor = 'rgba(126, 204, 205, 0.4)';
          }

          this.showToast('success', '¡Procesamiento finalizado! Bitácora de Sombras compilada.');
          document.getElementById('bitacora-locked-overlay').scrollIntoView({ behavior: 'smooth', block: 'start' });
          
          btn.innerText = originalText;
          btn.disabled = false;
        }, 2200);
      }

      // --- SYSTEM TELEMETRY CALIBRATION CONTROL (DASHBOARD) ---
      calibrateSomaticSystem(systemKey) {
        let changeText = "";
        let logLine = "";
        
        if (systemKey === 'conciencia') {
          this.polarities.conciencia = Math.min(100, this.polarities.conciencia + 5);
          document.getElementById('bar-conciencia').style.width = `${this.polarities.conciencia}%`;
          document.querySelector('#bar-conciencia').parentNode.previousElementSibling.querySelector('.val-teal').innerHTML = `${this.polarities.conciencia}% <span class="calibration-trigger">[CALIBRAR]</span>`;
          changeText = "Conciencia corporal registrada al " + this.polarities.conciencia + "%";
          logLine = `> [Registro] Conciencia corporal incrementada. Mayor atención a la respuesta somática.`;
        } else if (systemKey === 'apertura') {
          this.polarities.apertura = Math.min(100, this.polarities.apertura + 3);
          document.getElementById('bar-apertura').style.width = `${this.polarities.apertura}%`;
          document.querySelector('#bar-apertura').parentNode.previousElementSibling.querySelector('.val-teal').innerHTML = `${this.polarities.apertura}% <span class="calibration-trigger">[CALIBRAR]</span>`;
          changeText = "Apertura cognitiva integrada al " + this.polarities.apertura + "%";
          logLine = `> [Registro] Flexibilidad mental incrementada. Disminución de sesgos defensivos.`;
        } else if (systemKey === 'rigidez') {
          this.polarities.rigidez = Math.max(0, this.polarities.rigidez - 5);
          document.getElementById('bar-rigidez').style.width = `${this.polarities.rigidez}%`;
          document.querySelector('#bar-rigidez').parentNode.previousElementSibling.querySelector('.val-purple').innerHTML = `${this.polarities.rigidez}% <span class="calibration-trigger">[REGULAR]</span>`;
          changeText = "Rigidez somática reducida al " + this.polarities.rigidez + "%";
          logLine = `> [Registro] Liberación de coraza física. Reducción de la opresión intercostal.`;
        } else if (systemKey === 'evasion') {
          this.polarities.evasion = Math.max(0, this.polarities.evasion - 6);
          document.getElementById('bar-evasion').style.width = `${this.polarities.evasion}%`;
          document.querySelector('#bar-evasion').parentNode.previousElementSibling.querySelector('.val-rose').innerHTML = `${this.polarities.evasion}% <span class="calibration-trigger">[REGULAR]</span>`;
          changeText = "Evitación somática reducida al " + this.polarities.evasion + "%";
          logLine = `> [Registro] Evitación atenuada. Mayor tolerancia a zonas de fricción interna.`;
        }

        // Award fuel (FK)
        this.fractons += 3;
        document.getElementById('stats-fractons').innerText = `${this.fractons} FK`;

        // Calculate global integration
        const globalCoeff = Math.round((this.polarities.conciencia + this.polarities.apertura + (100 - this.polarities.rigidez) + (100 - this.polarities.evasion)) / 4);
        document.getElementById('val-integracion-global').innerText = `${globalCoeff}%`;

        // Update Log Console
        const logBox = document.getElementById('calibration-log');
        if (logBox) {
          const line = document.createElement('span');
          line.className = "console-log-line";
          line.innerText = logLine;
          logBox.appendChild(line);
          logBox.scrollTop = logBox.scrollHeight;
        }

        this.showToast('success', `Calibración: ${changeText}. +3 FK de Combustible cargados.`);
      }

      // --- SPATIAL CONSTELLATION MAP NODE SELECTION (EXPLORAR) ---
      selectConstellationNode(portalNum, element) {
        // Toggle active class on nodes
        const nodes = document.querySelectorAll('.constellation-node');
        nodes.forEach(n => n.classList.remove('active'));
        element.classList.add('active');

        // Target box highlighting and scrolling
        if (portalNum === 'phq9') {
          this.showToast('info', 'Enfoque: Cuestionario PHQ-9 (Evaluación de Estrés Somático)');
          const banner = document.getElementById('assigned-tests-section');
          if (banner) {
            banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
            banner.classList.add('highlighted-box');
            setTimeout(() => banner.classList.remove('highlighted-box'), 2000);
          }
          document.getElementById('constellation-telemetry-badge').innerText = "ATENCIÓN: CUESTIONARIO ASIGNADO POR TU TERAPEUTA";
          document.getElementById('constellation-telemetry-badge').className = "telemetry-badge-warning";
        } else {
          this.showToast('info', `Visualizando Portal ${portalNum}`);
          
          // Clear all highlighted boxes
          const boxes = document.querySelectorAll('.portal-box');
          boxes.forEach(b => b.classList.remove('highlighted-box'));
          
          const targetBox = document.getElementById(`portal-box-${portalNum}`);
          if (targetBox) {
            targetBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetBox.classList.add('highlighted-box');
            
            const isLocked = targetBox.classList.contains('locked');
            const statusBadge = document.getElementById('constellation-telemetry-badge');
            if (isLocked) {
              statusBadge.innerText = `PORTAL ${portalNum}: EN SOMBRA / REQUIERE COMPLETAR PORTAL PREVIO`;
              statusBadge.className = "telemetry-badge-warning";
            } else {
              statusBadge.innerText = `PORTAL ${portalNum}: ACCESO DISPONIBLE`;
              statusBadge.className = "telemetry-badge-nominal";
            }
          }
        }
      }

      // --- FRICTIONLESS SOMATIC HOTSPOT SELECTOR (ESPEJO BODY MAP) ---
      triggerSomaticHotspot(hotspotKey) {
        // Map hotspots keys to descriptions and logs
        const scanData = {
          mandibula: {
            input: "Registro Somático: Tensión mandibular activa (presión en mandíbula).",
            reply: "Espejo de Conflictos: Se registra tensión mandibular. Suele reflejar rigidez atencional o represión de impulsos de enojo. Sugerencia: Libera conscientemente la mandíbula, entreabriendo los labios durante 20 segundos."
          },
          diafragma: {
            input: "Registro Somático: Restricción en el diafragma (respiración superficial).",
            reply: "Espejo de Conflictos: Se registra contracción diafragmática. Tu sistema nervioso autónomo está en alerta. Evita racionalizar la tensión; selecciona 'Pausa de Respiración' para regular tu respiración."
          },
          plexo: {
            input: "Registro Somático: Opresión en el plexo solar (sensación de vacío o alerta).",
            reply: "Espejo de Conflictos: Se registra opresión en el plexo. Es una respuesta visceral común de autoprotección. Intenta sostener la atención en esa molestia física sin huir hacia pensamientos explicativos."
          },
          extremidades: {
            input: "Registro Somático: Extremidades frías y hormigueo en las manos.",
            reply: "Espejo de Conflictos: Se registra baja temperatura en manos. Es una reacción simpática ante la incomodidad o la evitación. Respira prolongando la exhalación para reequilibrar la temperatura."
          }
        };

        const currentScan = scanData[hotspotKey];
        if (!currentScan) return;

        this.chatTextarea.disabled = true;
        this.btnChatSend.disabled = true;

        // Print somatic feed to chat
        this.addUserMessage(currentScan.input);
        this.showToast('info', 'Registro corporal enviado al Espejo');
        this.showAITypingIndicator();

        // Simulate processing and write AI somatic reply
        setTimeout(() => {
          this.removeTypingIndicator();
          this.addAIMessage(currentScan.reply);

          // Update Dashboard system status elements to nominal
          const led = document.getElementById('telemetry-soma-led');
          const text = document.getElementById('telemetry-soma-text');
          if (led) {
            led.className = "indicator-led status-nominal green-pulse";
          }
          if (text) {
            text.innerText = "REGISTRO CORPORAL: COMPLETADO";
          }

          // Award Fractons
          this.fractons += 10;
          document.getElementById('stats-fractons').innerText = `${this.fractons} FK`;
          this.showToast('success', '¡Registro somático integrado! +10 Fractones (FK) ganados.');

        }, 1300);
      }

      // --- CHAT ESPEJO SOMÁTICO ORIGINAL METHODS ---
      setupSomaticResponses() {
        this.somaticReplies = [
          "Espejo de Conflictos: Se registra tensión intercostal. La mente tiende a racionalizar el conflicto laboral para desviar la incomodidad corporal. Sugerencia: Dirige tu atención a esa contracción física durante 15 segundos sin buscar explicaciones inmediatas.",
          "Espejo de Conflictos: Se registra tensión en extremidades. La mente busca evadir la incomodidad física refugiándose en ideas místicas o evasivas. Recomendación: Mantén la atención en el cuerpo, observando la sensación fría sin conceptualizarla.",
          "Espejo de Conflictos: Noto una tendencia a interpretar el registro corporal como una historia de injusticia laboral. Esto desvía el procesamiento real. Te sugiero regresar al diafragma, sintiendo su movimiento natural."
        ];
        this.replyIndex = 0;
      }

      triggerSomaticAction(actionType) {
        if (actionType === 'escribir') {
          this.chatTextarea.disabled = false;
          this.btnChatSend.disabled = false;
          this.chatTextarea.focus();
          this.showToast('info', 'Escribe libremente. Describe la molestia física.');
        } else if (actionType === 'somatica') {
          this.chatTextarea.disabled = true;
          this.btnChatSend.disabled = true;
          
          this.addUserMessage("Franco (Registro Somático): Siento opresión en el plexo.");
          this.showAITypingIndicator();

          setTimeout(() => {
            this.removeTypingIndicator();
            const reply = this.somaticReplies[this.replyIndex % this.somaticReplies.length];
            this.replyIndex++;
            this.addAIMessage(reply);
          }, 1500);
        } else if (actionType === 'pausa') {
          this.runBreathingGuide();
        }
      }

      addUserMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'chat-msg user';
        msg.innerHTML = `
          <div class="msg-avatar">F</div>
          <div class="msg-bubble">
            <p>${text}</p>
          </div>
        `;
        this.chatMessagesBox.appendChild(msg);
        this.chatMessagesBox.scrollTop = this.chatMessagesBox.scrollHeight;
      }

      addAIMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'chat-msg ai';
        msg.innerHTML = `
          <div class="msg-avatar">E</div>
          <div class="msg-bubble">
            <p>${text}</p>
          </div>
        `;
        this.chatMessagesBox.appendChild(msg);
        this.chatMessagesBox.scrollTop = this.chatMessagesBox.scrollHeight;
      }

      showAITypingIndicator() {
        const loader = document.createElement('div');
        loader.className = 'chat-msg ai typing-indicator';
        loader.id = 'chat-typing-indicator';
        loader.innerHTML = `
          <div class="msg-avatar">E</div>
          <div class="msg-bubble">
            <p><em>El Espejo analiza...</em></p>
          </div>
        `;
        this.chatMessagesBox.appendChild(loader);
        this.chatMessagesBox.scrollTop = this.chatMessagesBox.scrollHeight;
      }

      removeTypingIndicator() {
        const loader = document.getElementById('chat-typing-indicator');
        if (loader) loader.remove();
      }

      sendChatMessage() {
        const text = this.chatTextarea.value.trim();
        if (!text) return;
        
        this.addUserMessage(text);
        this.chatTextarea.value = '';
        this.chatTextarea.disabled = true;
        this.btnChatSend.disabled = true;
        this.showAITypingIndicator();

        setTimeout(() => {
          this.removeTypingIndicator();
          const reply = this.somaticReplies[this.replyIndex % this.somaticReplies.length];
          this.replyIndex++;
          this.addAIMessage(reply);
        }, 1800);
      }

      // --- REGULACIÓN DE RESPIRACIÓN SOMÁTICA ---
      runBreathingGuide() {
        this.breathingCircle.classList.add('animating');
        this.breathingText.innerText = "INHALA SUAVEMENTE (4s)";
        if (this.breathingBadge) {
          this.breathingBadge.innerText = "92 L/M / TENSIÓN DETECTADA";
          this.breathingBadge.className = "telemetry-badge-warning";
        }
        this.showToast('info', 'Iniciando ciclo de respiración para reequilibrar la tensión corporal');

        let seconds = 0;
        const interval = setInterval(() => {
          seconds++;
          
          if (seconds === 4) {
            this.breathingText.innerText = "MANTÉN EL AIRE (2s)";
            if (this.breathingBadge) this.breathingBadge.innerText = "84 L/M / REGULANDO";
          } else if (seconds === 6) {
            this.breathingText.innerText = "EXHALA LENTAMENTE (4s)";
            if (this.breathingBadge) this.breathingBadge.innerText = "75 L/M / REGULANDO RITMO";
          } else if (seconds >= 10) {
            clearInterval(interval);
            this.breathingCircle.classList.remove('animating');
            this.breathingText.innerText = "PAUSA COMPLETADA / ESTADO DE CALMA";
            if (this.breathingBadge) {
              this.breathingBadge.innerText = "68 L/M / EN CALMA";
              this.breathingBadge.className = "telemetry-badge-nominal";
            }
            this.addUserMessage("Franco: Ciclo de respiración completado.");
            this.addAIMessage("Ejercicio completado. La respiración prolongada ha estabilizado tu ritmo cardíaco, reduciendo la respuesta somática de alarma.");
            
            // Add fractons
            this.fractons += 5;
            document.getElementById('stats-fractons').innerText = `${this.fractons} FK`;
          }
        }, 1000);
      }

      // --- SAAS PRACTITIONER LOGIC ---
      loadClientDetails(clientSlug) {
        const nameHeader = document.querySelector('.client-details-header h3');
        const summaryParagraph = document.querySelector('.summary-content p');
        
        if (clientSlug === 'franco') {
          nameHeader.innerText = "Franco Jeria";
          document.getElementById('chk-phq9').checked = true;
          document.getElementById('chk-gad7').checked = false;
          document.getElementById('chk-maia').checked = false;
          document.getElementById('lbl-phq9-status').innerText = "(Asignado)";
          summaryParagraph.innerHTML = `<strong>Perfil General:</strong> Franco presenta una polaridad de sombra enfocada en la represión de la agresividad y el control obsesivo (Eneagrama 1). Intelectualiza las heridas para evadir el procesamiento somático.`;
        } else if (clientSlug === 'sofia') {
          nameHeader.innerText = "Sofía G.";
          document.getElementById('chk-phq9').checked = true;
          document.getElementById('chk-gad7').checked = true;
          document.getElementById('chk-maia').checked = true;
          document.getElementById('lbl-phq9-status').innerText = "(Asignado)";
          summaryParagraph.innerHTML = `<strong>Perfil General:</strong> Sofía muestra una alta inestabilidad somática (DERS-16). Utiliza la hiperactividad y el control exhaustivo como máscara de seguridad ante la herida de abandono.`;
        } else if (clientSlug === 'mateo') {
          nameHeader.innerText = "Mateo R.";
          document.getElementById('chk-phq9').checked = false;
          document.getElementById('chk-gad7').checked = false;
          document.getElementById('chk-maia').checked = false;
          document.getElementById('lbl-phq9-status').innerText = "";
          summaryParagraph.innerHTML = `<strong>Perfil General:</strong> Sin datos suficientes en la plataforma. Paciente no ha resuelto tests del Portal I.`;
        }
      }

      updateTestAssignments() {
        const isPHQ9Checked = document.getElementById('chk-phq9').checked;
        const patientBanner = document.getElementById('assigned-tests-section');
        
        if (isPHQ9Checked) {
          patientBanner.style.display = 'block';
          document.getElementById('assigned-test-phq9').style.display = 'flex';
          document.getElementById('lbl-phq9-status').innerText = "(Asignado)";
        } else {
          document.getElementById('lbl-phq9-status').innerText = "";
          // Ocultar test asignado si se desmarca
          document.getElementById('assigned-test-phq9').style.display = 'none';
          patientBanner.style.display = 'none';
        }

        this.showToast('success', 'Asignación de misiones y tests actualizada con éxito');
      }

      // --- PATIENT RESOLVES ASSIGNED TEST ---
      startMockTest(testName) {
        this.showToast('info', `Inicializando cuestionario ${testName}...`);
        
        setTimeout(() => {
          // Simular resolución de PHQ-9
          this.showToast('success', `¡Cuestionario PHQ-9 completado! +8 Fractones (FK) agregados.`);
          
          // Modificar contador de tests e iconografía en Explorar
          this.completedTests = 5;
          const statVal = document.getElementById('stats-missions');
          if (statVal) statVal.innerText = this.completedTests;

          // Agregar visual de test completado en el listado del terapeuta
          const patientBanner = document.getElementById('assigned-tests-section');
          if (patientBanner) patientBanner.style.display = 'none';

          // Incrementar fractones
          this.fractons += 8;
          const fkStat = document.getElementById('stats-fractons');
          if (fkStat) fkStat.innerText = `${this.fractons} FK`;

        }, 1500);
      }

      // --- SYSTEM TOASTS ---
      showToast(type, message) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
          <span>${message}</span>
        `;
        container.appendChild(toast);

        // Quitar toast tras 4 segundos
        setTimeout(() => {
          toast.style.animation = 'slide-out 0.3s forwards';
          setTimeout(() => toast.remove(), 300);
        }, 4000);
      }

      // --- PERFIL PÚBLICO ---
      buscarUsuario() {
        const query = document.getElementById('perfil-search-input')?.value?.trim();
        if (!query) return;

        fetch(`/comunidad/api/buscar/?q=${encodeURIComponent(query)}`)
          .then(r => r.json())
          .then(data => {
            const resultsDiv = document.getElementById('perfil-search-results');
            resultsDiv.innerHTML = '';
            if (!data.results || data.results.length === 0) {
              resultsDiv.innerHTML = '<div class="card telemetry-console-border" style="padding:16px;text-align:center;color:var(--muted);">No se encontraron usuarios.</div>';
              return;
            }
            data.results.forEach(u => {
              const div = document.createElement('div');
              div.className = 'card telemetry-console-border';
              div.style.cssText = 'padding:12px;display:flex;align-items:center;gap:12px;cursor:pointer;';
              div.innerHTML = `
                <div style="width:40px;height:40px;border-radius:50%;background:var(--calipso-glow);display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--calipso);flex-shrink:0;">${(u.first_name||'?')[0].toUpperCase()}</div>
                <div><div style="color:#fff;font-weight:600;">${u.first_name||'Sin nombre'}</div><div style="font-size:0.75rem;color:var(--muted);">${u.email}</div></div>
              `;
              div.onclick = () => this.verPerfilPublico(u);
              resultsDiv.appendChild(div);
            });
          })
          .catch(() => {
            this.showToast('error', 'Error en la búsqueda.');
          });
      }

      verPerfilPublico(usuario) {
        document.getElementById('perfil-public-view').style.display = 'block';
        document.getElementById('perfil-public-name').innerText = usuario.first_name || 'Usuario';
        document.getElementById('perfil-public-display-name').innerText = usuario.first_name || 'Sin nombre';
        document.getElementById('perfil-public-email').innerText = usuario.email;
        document.getElementById('perfil-public-bio').innerText = usuario.bio || 'Sin biografía';
        document.getElementById('perfil-public-avatar-placeholder').innerText = (usuario.first_name||'?')[0].toUpperCase();
        if (usuario.avatar) {
          document.getElementById('perfil-public-avatar-img').src = usuario.avatar;
          document.getElementById('perfil-public-avatar-img').style.display = 'block';
          document.getElementById('perfil-public-avatar-placeholder').style.display = 'none';
        }
        document.getElementById('perfil-public-tests').innerText = usuario.tests_count || 0;
        document.getElementById('perfil-public-fractons').innerText = (usuario.fractons_balance || 0) + ' FK';
        document.getElementById('perfil-public-espejo').innerText = usuario.espejo_count || 0;
        document.getElementById('perfil-public-plan').innerText = usuario.plan || 'Free';
      }

      seguirUsuario() {
        this.showToast('info', 'Función de seguir en desarrollo.');
      }

      enviarMensaje() {
        this.showToast('info', 'Función de mensajería en desarrollo.');
      }

      // --- API: ESPEJO ---
      async espejoSend(message, sessionId, enfoque) {
        const resp = await fetch('/espejo/send/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCookie('csrftoken'),
          },
          body: JSON.stringify({ mensaje: message, sesion_id: sessionId, enfoque }),
        });
        return resp.json();
      }

      async espejoNuevo() {
        const resp = await fetch('/espejo/nuevo/', { method: 'POST', headers: {'X-CSRFToken': this.getCookie('csrftoken')} });
        return resp.json();
      }

      async espejoSesiones() {
        const resp = await fetch('/espejo/');
        return resp.json();
      }

      async espejoLoadTarjetas() {
        const container = document.getElementById('espejo-tarjetas-list');
        if (!container) return;
        try {
          const data = await fetch('/espejo/tarjetas/').then(r => r.json());
          container.innerHTML = '';
          const pending = data.pending || [];
          const revealed = data.revealed || [];
          if (pending.length === 0 && revealed.length === 0) {
            container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--muted);font-size:0.85rem;">No hay tarjetas aún. Completa tests o reportes para generar insights.</div>';
            return;
          }
          if (pending.length > 0) {
            const label = document.createElement('span');
            label.style.cssText = 'font-size:0.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;padding-left:4px;margin-top:8px;';
            label.textContent = 'Pendientes';
            container.appendChild(label);
            pending.forEach(c => {
              const div = document.createElement('div');
              div.className = 'espejo-tarjeta-item';
              div.style.borderLeftColor = 'var(--amber)';
              div.innerHTML = `<div style="font-size:0.85rem;font-weight:600;color:#fff;">${c.title}</div><div style="font-size:0.7rem;color:var(--muted);margin-top:4px;">${c.date || ''}</div>`;
              if (c.id) {
                div.dataset.sessionId = c.id;
                div.onclick = () => {
                  // Highlight selected tarjeta
                  container.querySelectorAll('.espejo-tarjeta-item').forEach(t => t.classList.remove('active'));
                  div.classList.add('active');
                  this.espejoLoadSession(c.id);
                };
              } else if (c.url) {
                div.onclick = () => window.location.href = c.url;
              }
              container.appendChild(div);
            });
          }
          if (revealed.length > 0) {
            const label = document.createElement('span');
            label.style.cssText = 'font-size:0.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;padding-left:4px;margin-top:16px;';
            label.textContent = 'Revelados';
            container.appendChild(label);
            revealed.forEach(c => {
              const div = document.createElement('div');
              div.className = 'espejo-tarjeta-item';
              div.style.borderLeftColor = 'var(--calipso)';
              div.innerHTML = `<div style="font-size:0.85rem;font-weight:600;color:#fff;">${c.title}</div><div style="font-size:0.7rem;color:var(--muted);margin-top:4px;">${c.date || ''}</div>`;
              if (c.id) {
                div.dataset.sessionId = c.id;
                div.onclick = () => {
                  container.querySelectorAll('.espejo-tarjeta-item').forEach(t => t.classList.remove('active'));
                  div.classList.add('active');
                  this.espejoLoadSession(c.id);
                };
              } else if (c.url) {
                div.onclick = () => window.location.href = c.url;
              }
              container.appendChild(div);
            });
          }
        } catch (e) {
          container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--rose);font-size:0.85rem;">Error al cargar tarjetas.</div>';
        }
      }

      async espejoLoadSession(sessionId) {
        this.currentSessionId = sessionId;
        const box = document.getElementById('chat-messages-box');
        const titleEl = document.getElementById('espejo-chat-title');
        if (!box) return;
        box.innerHTML = '';
        this.showAITypingIndicator();
        try {
          const data = await fetch(`/espejo/${sessionId}/mensajes/`).then(r => r.json());
          this.removeTypingIndicator();
          if (data.title && titleEl) titleEl.textContent = data.title.toUpperCase();
          const msgs = data.messages || [];
          if (msgs.length === 0) {
            this.addAIMessage('Iniciando secuencia de interacción del Espejo. ¿Dónde se encuentra localizada la molestia física que estás intentando evadir hoy?');
          } else {
            msgs.forEach(m => {
              if (m.role === 'user') this.addUserMessage(m.content);
              else if (m.role === 'assistant') this.addAIMessage(m.content);
            });
          }
          // Hide enfoques and error
          const enfDiv = document.getElementById('espejo-enfoques');
          if (enfDiv) enfDiv.style.display = 'none';
          const errDiv = document.getElementById('espejo-error');
          if (errDiv) errDiv.style.display = 'none';
        } catch (e) {
          this.removeTypingIndicator();
          this.showEspejoError('Error al cargar la conversación.');
        }
      }

      showEspejoError(msg) {
        const errDiv = document.getElementById('espejo-error');
        if (errDiv) {
          errDiv.textContent = msg;
          errDiv.style.display = 'block';
        }
        this.showToast('error', msg);
      }

      hideEspejoError() {
        const errDiv = document.getElementById('espejo-error');
        if (errDiv) errDiv.style.display = 'none';
      }

      renderEnfoques(enfoques) {
        const enfDiv = document.getElementById('espejo-enfoques');
        if (!enfDiv) return;
        enfDiv.innerHTML = '';
        if (!enfoques || !Array.isArray(enfoques) || enfoques.length === 0) {
          enfDiv.style.display = 'none';
          return;
        }
        enfDiv.style.display = 'flex';
        enfoques.forEach(e => {
          const btn = document.createElement('button');
          btn.className = 'espejo-enfoque-btn';
          btn.textContent = e.titulo || e.id || 'Enfoque';
          btn.onclick = () => {
            const text = `Quiero explorar el enfoque: ${e.titulo || e.id}`;
            this.chatTextarea.value = text;
            this.chatTextarea.focus();
          };
          enfDiv.appendChild(btn);
        });
      }

      sendChatMessage() {
        const text = this.chatTextarea.value.trim();
        if (!text) return;
        this.hideEspejoError();
        this.addUserMessage(text);
        this.chatTextarea.value = '';
        this.chatTextarea.disabled = true;
        this.btnChatSend.disabled = true;
        this.showAITypingIndicator();
        const enfDiv = document.getElementById('espejo-enfoques');
        if (enfDiv) enfDiv.style.display = 'none';

        this.espejoSend(text, this.currentSessionId, null)
          .then(data => {
            this.removeTypingIndicator();
            this.chatTextarea.disabled = false;
            this.btnChatSend.disabled = false;
            this.chatTextarea.focus();
            if (data.error) {
              this.showEspejoError(data.error);
              return;
            }
            if (data.respuesta) this.addAIMessage(data.respuesta);
            if (data.sesion_id) this.currentSessionId = data.sesion_id;
            if (data.sesion_titulo) {
              const titleEl = document.getElementById('espejo-chat-title');
              if (titleEl) titleEl.textContent = data.sesion_titulo.toUpperCase();
            }
            if (data.enfoques) this.renderEnfoques(data.enfoques);
          })
          .catch(err => {
            this.removeTypingIndicator();
            this.chatTextarea.disabled = false;
            this.btnChatSend.disabled = false;
            this.showEspejoError('Error de conexión con el Espejo. Intenta de nuevo.');
          });
      }

      // --- API: TESTS ---
      async testsList() {
        const resp = await fetch('/psychometrics/api/tests/');
        return resp.json();
      }

      async testStart(testId) {
        const resp = await fetch(`/psychometrics/api/tests/${testId}/start/`, { method: 'POST', headers: {'X-CSRFToken': this.getCookie('csrftoken')} });
        return resp.json();
      }

      async testAnswer(testId, questionId, answer) {
        const resp = await fetch(`/psychometrics/api/tests/${testId}/answer/`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken')},
          body: JSON.stringify({ question_id: questionId, answer }),
        });
        return resp.json();
      }

      // API: COMMUNITY ---
      async feedLoad() {
        const resp = await fetch('/comunidad/api/feed/');
        return resp.json();
      }

      async feedPost(text) {
        const resp = await fetch('/comunidad/compartir/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken')},
          body: JSON.stringify({ text, source_type: 'native' }),
        });
        return resp.json();
      }

      // API: USER PROFILE ---
      async loadUserProfile() {
        const resp = await fetch('/accounts/api/profile/');
        return resp.json();
      }

      async saveUserProfile(data) {
        const resp = await fetch('/accounts/api/profile/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken')},
          body: JSON.stringify(data),
        });
        return resp.json();
      }

      // --- PERFIL EDIT MODE ---
      togglePerfilEdit() {
        const fields = ['perfil-first-name', 'perfil-last-name', 'perfil-email', 'perfil-bio'];
        const actions = document.getElementById('perfil-edit-actions');
        const btn = document.getElementById('btn-edit-profile');
        fields.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.disabled = false;
          if (el) el.style.background = 'rgba(0,0,0,0.35)';
        });
        if (actions) actions.style.display = 'flex';
        if (btn) btn.style.display = 'none';
      }

      cancelPerfilEdit() {
        const fields = ['perfil-first-name', 'perfil-last-name', 'perfil-email', 'perfil-bio'];
        const actions = document.getElementById('perfil-edit-actions');
        const btn = document.getElementById('btn-edit-profile');
        // Reset to original Django-rendered values by re-reading from DOM data
        // The values are already the server-rendered ones, just re-disable
        fields.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.disabled = true;
          if (el) el.style.background = 'rgba(0,0,0,0.15)';
        });
        if (actions) actions.style.display = 'none';
        if (btn) btn.style.display = 'inline-flex';
      }

      async savePerfil() {
        const firstName = document.getElementById('perfil-first-name')?.value?.trim() || '';
        const lastName = document.getElementById('perfil-last-name')?.value?.trim() || '';
        const bio = document.getElementById('perfil-bio')?.value?.trim() || '';

        const formData = new FormData();
        formData.append('first_name', firstName);
        formData.append('last_name', lastName);
        formData.append('bio', bio);

        try {
          const resp = await fetch('/accounts/api/profile/update/', {
            method: 'POST',
            headers: {'X-CSRFToken': this.getCookie('csrftoken')},
            body: formData,
          });
          const data = await resp.json();
          if (data.ok) {
            this.showToast('success', 'Perfil actualizado correctamente.');
            this.cancelPerfilEdit();
            // Update displayed name in sidebar
            const sidebarName = document.querySelector('.user-info h4');
            if (sidebarName) sidebarName.textContent = firstName || 'Navegante';
          } else {
            this.showToast('error', data.error || 'Error al guardar el perfil.');
          }
        } catch (e) {
          this.showToast('error', 'Error de conexión al guardar el perfil.');
        }
      }
    }

   // --- INICIALIZACIÓN DE THREE.JS E INTERACTIVIDAD ---
   window.addEventListener('DOMContentLoaded', () => {
     try {
       initCosmos();
       window.app = new EndonautasApp();
       console.log('EndonautasApp initialized successfully');
     } catch (e) {
       console.error('EndonautasApp initialization error:', e);
       // Fallback: try to initialize without Three.js
       try {
         window.app = new EndonautasApp();
       } catch (e2) {
         console.error('Fallback init also failed:', e2);
       }
     }
   });

