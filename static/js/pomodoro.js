// Constants and configurations
const CONFIG = {
  CIRCUMFERENCE: 2 * Math.PI * 88,
  AUDIO_TRACKS: {
    whitenoise: '/static/audio/lofi.mp3',
    nature: '/static/audio/lofi.mp3',
    lofi: '/static/audio/lofi.mp3',
    rain: '/static/audio/lofi.mp3',
    ocean: '/static/audio/lofi.mp3'
  },
  API_ENDPOINTS: {
    pomodoro: '/pomodoro/api/'
  }
};

class PomodoroAudioManager {
  constructor() {
    this.audioTracks = {};
    this.currentAudio = null;
    this.volume = 0.5;
    this.currentTrack = null;
    this.initializeAudio();
  }

  initializeAudio() {
    // Crear los elementos de audio para cada pista
    Object.entries(CONFIG.AUDIO_TRACKS).forEach(([key, path]) => {
      const audio = new Audio(path);
      audio.loop = true;
      this.audioTracks[key] = audio;
      
      // Agregar manejadores de error
      audio.onerror = () => {
        console.error(`Error loading audio track: ${key}`);
      };
    });

    // Agregar controles de audio al DOM
    this.createAudioControls();
  }

  createAudioControls() {
    const controls = document.createElement('div');
    controls.className = 'fixed bottom-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-4 space-y-4';
    
    // Selector de pista
    const trackSelector = document.createElement('select');
    trackSelector.className = 'w-full p-2 rounded border border-gray-300';
    
    // Agregar opciones de pistas
    const tracks = [
      { value: '', label: 'Sin sonido' },
      { value: 'lofi', label: 'Lo-Fi Music' },
      { value: 'whitenoise', label: 'White Noise' },
      { value: 'nature', label: 'Nature Sounds' },
      { value: 'rain', label: 'Rain Sounds' },
      { value: 'ocean', label: 'Ocean Waves' }
    ];
    
    tracks.forEach(track => {
      const option = document.createElement('option');
      option.value = track.value;
      option.textContent = track.label;
      trackSelector.appendChild(option);
    });

    // Control de volumen
    const volumeControl = document.createElement('input');
    volumeControl.type = 'range';
    volumeControl.min = 0;
    volumeControl.max = 100;
    volumeControl.value = this.volume * 100;
    volumeControl.className = 'w-full';

    // Event listeners
    trackSelector.addEventListener('change', (e) => {
      this.playTrack(e.target.value);
    });

    volumeControl.addEventListener('input', (e) => {
      this.setVolume(e.target.value / 100);
    });

    // Agregar elementos al contenedor
    controls.appendChild(trackSelector);
    controls.appendChild(volumeControl);

    // Agregar controles al DOM
    document.body.appendChild(controls);
  }

  async playTrack(trackName) {
    try {
      // Detener la pista actual si existe
      if (this.currentAudio) {
        await this.currentAudio.pause();
        this.currentAudio.currentTime = 0;
      }

      // Si se seleccionó una nueva pista, reproducirla
      if (trackName && this.audioTracks[trackName]) {
        this.currentAudio = this.audioTracks[trackName];
        this.currentTrack = trackName;
        this.currentAudio.volume = this.volume;
        
        // Intentar reproducir con manejo de errores
        try {
          await this.currentAudio.play();
        } catch (error) {
          if (error.name === 'NotAllowedError') {
            // Mostrar mensaje al usuario sobre la política de autoplay
            this.showPlaybackNotification();
          } else {
            console.error('Error playing audio:', error);
          }
        }
      } else {
        this.currentAudio = null;
        this.currentTrack = null;
      }
    } catch (error) {
      console.error('Error switching tracks:', error);
    }
  }

  setVolume(value) {
    this.volume = Math.max(0, Math.min(1, value));
    if (this.currentAudio) {
      this.currentAudio.volume = this.volume;
    }
  }

  showPlaybackNotification() {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 rounded shadow-md';
    notification.innerHTML = `
      <p class="font-bold">Activar sonido</p>
      <p>Haz clic en cualquier parte de la página para activar el sonido de fondo.</p>
    `;
    
    document.body.appendChild(notification);
    
    // Remover la notificación después de un click
    document.addEventListener('click', () => {
      notification.remove();
      if (this.currentTrack) {
        this.playTrack(this.currentTrack);
      }
    }, { once: true });
  }

  pauseAudio() {
    if (this.currentAudio) {
      this.currentAudio.pause();
    }
  }

  resumeAudio() {
    if (this.currentAudio) {
      this.currentAudio.play().catch(console.error);
    }
  }
}

class PomodoroApp {
  constructor() {
    this.initializeState();
    this.initializeElements();
    this.initializeAudio();
    this.setupEventListeners();
    this.initializeActiveSession();
    this.audioManager = new PomodoroAudioManager();
  }

  // State initialization
  initializeState() {
    this.timeLeft = 0;
    this.totalTime = 0;
    this.timerId = null;
    this.activeSession = null;
    this.currentAudio = null;
    this.audioTracks = {};
    this.deferredPrompt = null;
  }

  // DOM elements initialization
  initializeElements() {
    this.elements = {
      timer: document.getElementById('timer'),
      sessionType: document.getElementById('sessionType'),
      mainActionBtn: document.getElementById('mainActionBtn'),
      timerProgress: document.getElementById('timerProgress'),
      taskModal: document.getElementById('taskModal'),
      taskToggle: document.getElementById('taskToggle'),
      closeTaskModal: document.getElementById('closeTaskModal'),
      taskName: document.querySelector('.task-name'),
      cancelSessionBtn: document.getElementById('cancelSessionBtn')
    };

    // Set initial timer progress properties
    this.elements.timerProgress.style.strokeDasharray = `${CONFIG.CIRCUMFERENCE} ${CONFIG.CIRCUMFERENCE}`;
  }

  // Audio system initialization
  initializeAudio() {
    Object.entries(CONFIG.AUDIO_TRACKS).forEach(([key, path]) => {
      this.audioTracks[key] = new Audio(path);
    });
  }

  // Event listeners setup
  setupEventListeners() {
    // Main controls
    this.elements.mainActionBtn.addEventListener('click', () => {
      if (this.activeSession) {
        this.toggleTimer();
      } else {
        this.elements.taskModal.classList.remove('hidden');
      }
    });

    // Task selection
    this.elements.taskToggle.addEventListener('click', () => {
      if (!this.activeSession) {
        this.elements.taskModal.classList.remove('hidden');
      }
    });

    this.elements.closeTaskModal.addEventListener('click', () => {
      this.elements.taskModal.classList.add('hidden');
    });

    // Task options
    document.querySelectorAll('.task-option').forEach(button => {
      button.addEventListener('click', () => {
        const taskId = button.dataset.taskId;
        this.startSession(taskId);
        this.elements.taskModal.classList.add('hidden');
      });
    });

    // Cancel session button
    if (this.elements.cancelSessionBtn) {
      this.elements.cancelSessionBtn.addEventListener('click', () => {
        this.showConfirmDialog(
          'Cancelar Sesión',
          '¿Estás seguro de que deseas cancelar la sesión actual?',
          () => {
            if (this.activeSession) {
              this.cancelSession(this.activeSession.session_id);
            }
          }
        );
      });
    }

    // Mobile specific
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    window.addEventListener('popstate', this.handleBackGesture.bind(this));
    window.addEventListener('beforeinstallprompt', this.handleInstallPrompt.bind(this));
    window.addEventListener('beforeunload', () => {
      this.saveSessionToLocalStorage();
    });

    // Initialize notifications if available
    if ('Notification' in window) {
      Notification.requestPermission();
    }
  }

  // Timer management
  updateProgress(timeLeft) {
    const progress = timeLeft / this.totalTime;
    const offset = CONFIG.CIRCUMFERENCE - (progress * CONFIG.CIRCUMFERENCE);
    this.elements.timerProgress.style.strokeDashoffset = offset;
  }

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  startTimerCountdown() {
    this.updateMainActionButton('pause');
    // Reanudar audio si existe
    this.audioManager.resumeAudio();
    
    this.timerId = setInterval(() => {
      this.timeLeft--;
      this.elements.timer.textContent = this.formatTime(this.timeLeft);
      this.updateProgress(this.timeLeft);
      
      if (this.timeLeft % 5 === 0) {
        this.saveSessionToLocalStorage();
      }

      if (this.timeLeft <= 0) {
        clearInterval(this.timerId);
        this.audioManager.pauseAudio();
        this.completeSession();
      }
    }, 1000);
  }

  resetTimer() {
    clearInterval(this.timerId);
    this.timeLeft = 0;
    this.totalTime = 0;
    this.elements.timer.textContent = this.formatTime(0);
    this.updateProgress(0);
    this.updateMainActionButton('play');
  }

  // Session management
  async startSession(taskId) {
    try {
      // Check for active session first
      const activeSession = await this.checkActiveSession();
      
      if (activeSession) {
        const shouldCancel = await this.confirmCancelActiveSession(activeSession);
        if (shouldCancel) {
          await this.cancelSession(activeSession.session_id);
        } else {
          return;
        }
      }

      // Start new session
      const response = await this.makeRequest('POST', {
        action: 'start',
        task_id: taskId,
        session_type: 'pomodoro'
      });
      
      this.activeSession = response;
      this.timeLeft = response.duration * 60;
      this.totalTime = this.timeLeft;
      this.startTimerCountdown();
      this.updateUIForActiveSession();
      this.saveSessionToLocalStorage();
      
    } catch (error) {
      if (error.message) {
        this.showNotification('error', error.message);
      }
    }
  }

  async checkActiveSession() {
    try {
      const response = await this.makeRequest('GET');
      return response.active_session || null;
    } catch (error) {
      console.error('Error checking active session:', error);
      return null;
    }
  }

  async confirmCancelActiveSession(session) {
    return new Promise((resolve) => {
      const taskName = session.task.title;
      const message = `Ya tienes una sesión activa para la tarea "${taskName}". ¿Deseas cancelarla y comenzar una nueva?`;
      
      this.showConfirmDialog(
        'Sesión Activa',
        message,
        () => resolve(true),
        () => resolve(false)
      );
    });
  }

  async toggleTimer() {
    if (!this.activeSession) return;

    try {
      const action = this.activeSession.status === 'in_progress' ? 'pause' : 'resume';
      const response = await this.makeRequest('POST', {
        action: action,
        session_id: this.activeSession.session_id
      });

      if (action === 'pause') {
        clearInterval(this.timerId);
        this.audioManager.pauseAudio();
        this.updateMainActionButton('play');
      } else {
        this.startTimerCountdown();
      }
      
      this.activeSession = response;
      this.saveSessionToLocalStorage();
      
    } catch (error) {
      this.showNotification('error', error.message);
    }
  }

  async cancelSession(sessionId) {
    try {
      await this.makeRequest('POST', {
        action: 'cancel',
        session_id: sessionId
      });
      
      this.audioManager.pauseAudio();
      this.resetTimer();
      this.activeSession = null;
      this.updateUIForNoSession();
      localStorage.removeItem('pomodoroSession');
      
    } catch (error) {
      this.showNotification('error', error.message);
    }
  }

  async completeSession() {
    if (!this.activeSession) return;
    
    try {
      const response = await this.makeRequest('POST', {
        action: 'complete',
        session_id: this.activeSession.session_id
      });
      
      this.toggleAudio(null);
      this.showSessionSummary(response);
      
      if (response.task.completed_pomodoros >= response.task.estimated_pomodoros) {
        this.showTaskCompletionMessage();
      }
      
      this.activeSession = null;
      this.resetTimer();
      localStorage.removeItem('pomodoroSession');
      
    } catch (error) {
      this.showNotification('error', error.message);
    }
  }

  // UI updates
  updateMainActionButton(state) {
    const icons = {
      play: `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>`,
      pause: `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
             </svg>`
    };
    this.elements.mainActionBtn.innerHTML = icons[state];
  }

  updateUIForActiveSession() {
    if (!this.activeSession) return;
    
    this.elements.taskName.textContent = this.activeSession.task.title;
    this.elements.sessionType.textContent = 
      this.activeSession.session_type.replace('_', ' ').toUpperCase();
    this.updateMainActionButton(
      this.activeSession.status === 'in_progress' ? 'pause' : 'play'
    );
    this.elements.timer.textContent = this.formatTime(this.timeLeft);
    this.updateProgress(this.timeLeft);
  }

  updateUIForNoSession() {
    this.elements.taskName.textContent = 'Select Task';
    this.elements.sessionType.textContent = 'POMODORO';
    this.updateMainActionButton('play');
    if (this.elements.cancelSessionBtn) {
      this.elements.cancelSessionBtn.classList.add('hidden');
    }
  }

  // Session persistence
  async initializeActiveSession() {
    try {
      // Check server for active session first
      const response = await this.makeRequest('GET');
      const serverSession = response.active_session;
      
      if (serverSession) {
        this.activeSession = serverSession;
        
        // Calculate remaining time based on server session
        const startTime = new Date(serverSession.started_at);
        const currentTime = new Date();
        const elapsedSeconds = Math.floor((currentTime - startTime) / 1000);
        const pauseDuration = serverSession.total_pause_duration || 0;
        
        // Adjust for pauses
        const adjustedElapsedSeconds = elapsedSeconds - pauseDuration;
        this.timeLeft = Math.max(0, (serverSession.duration * 60) - adjustedElapsedSeconds);
        this.totalTime = serverSession.duration * 60;

        // Update UI
        this.updateUIForActiveSession();
        
        // If session is in progress, start countdown
        if (serverSession.status === 'in_progress') {
          this.startTimerCountdown();
        } else if (serverSession.status === 'paused') {
          this.updateMainActionButton('play');
        }
        
        // Store session data in localStorage for redundancy
        this.saveSessionToLocalStorage();
      } else {
        // If no server session, try to recover from localStorage
        this.recoverSessionFromLocalStorage();
      }
    } catch (error) {
      console.error('Error initializing session:', error);
      // Attempt to recover from localStorage if server fails
      this.recoverSessionFromLocalStorage();
    }
  }

  saveSessionToLocalStorage() {
    if (this.activeSession) {
      const sessionData = {
        ...this.activeSession,
        timeLeft: this.timeLeft,
        totalTime: this.totalTime,
        lastUpdate: new Date().toISOString()
      };
      localStorage.setItem('pomodoroSession', JSON.stringify(sessionData));
    } else {
      localStorage.removeItem('pomodoroSession');
    }
  }

  recoverSessionFromLocalStorage() {
    const savedSession = localStorage.getItem('pomodoroSession');
    if (savedSession) {
      try {
        const sessionData = JSON.parse(savedSession);
        const lastUpdate = new Date(sessionData.lastUpdate);
        const currentTime = new Date();
        const timeDiff = Math.floor((currentTime - lastUpdate) / 1000);
        
        // Only recover if less than 5 minutes have passed
        if (timeDiff < 300) {
          this.activeSession = sessionData;
          this.timeLeft = Math.max(0, sessionData.timeLeft);
          this.totalTime = sessionData.totalTime;
          
          this.updateUIForActiveSession();
          
          if (sessionData.status === 'in_progress') {
            this.startTimerCountdown();
          } else if (sessionData.status === 'paused') {
            this.updateMainActionButton('play');
          }
        } else {
          localStorage.removeItem('pomodoroSession');
        }
      } catch (error) {
        console.error('Error recovering session:', error);
        localStorage.removeItem('pomodoroSession');
      }
    }
  }

  // Audio management
  toggleAudio(track) {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
    }
    
    if (track && this.audioTracks[track]) {
      this.currentAudio = this.audioTracks[track];
      this.currentAudio.loop = true;
      this.currentAudio.volume = 0.5;
      this.currentAudio.play().catch(e => console.log('Audio autoplay blocked'));
    }
  }

  // Utility methods
  async makeRequest(method, data) {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCookie('csrftoken')
      }
    };
    
    if (method !== 'GET' && data) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(CONFIG.API_ENDPOINTS.pomodoro, options);
    const responseData = await response.json();
    
    if (!response.ok) {
      throw new Error(responseData.error || 'Server error');
    }
    
    return responseData;
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

  showNotification(type, message) {
    const notificationDiv = document.createElement('div');
    notificationDiv.className = `fixed top-4 right-4 p-4 rounded-lg ${
      type === 'error' ? 'bg-red-500' : 'bg-green-500'
    } text-white z-50 transition-opacity duration-300`;
    notificationDiv.textContent = message;
    
    document.body.appendChild(notificationDiv);
    
    // Fade out effect
    setTimeout(() => {
      notificationDiv.style.opacity = '0';
      setTimeout(() => {
        notificationDiv.remove();
      }, 300);
    }, 2700);
  }

  showSessionSummary(data) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-semibold mb-4">¡Sesión Completada!</h3>
        <div class="space-y-2 mb-4">
          <p class="text-gray-600">
            Has completado una sesión de ${data.duration} minutos para la tarea:
            <span class="font-medium text-gray-900">${data.task.title}</span>
          </p>
          <p class="text-gray-600">
            Pomodoros completados: ${data.task.completed_pomodoros}/${data.task.estimated_pomodoros}
          </p>
        </div>
        <div class="flex justify-end">
          <button class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700" onclick="this.closest('.fixed').remove()">
            Cerrar
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  showTaskCompletionMessage() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <div class="mb-4">
          <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-center mb-2">¡Tarea Completada!</h3>
          <p class="text-gray-600 text-center">
            Has completado todos los pomodoros estimados para esta tarea.
            ¡Excelente trabajo!
          </p>
        </div>
        <div class="flex justify-center">
          <button class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600" onclick="this.closest('.fixed').remove()">
            Continuar
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  showConfirmDialog(title, message, confirmCallback, cancelCallback = null) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg p-6 max-w-sm w-full">
        <h3 class="text-lg font-semibold mb-2">${title}</h3>
        <p class="text-gray-600 mb-4">${message}</p>
        <div class="flex justify-end space-x-2">
          <button class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded" id="cancelBtn">
            Cancelar
          </button>
          <button class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700" id="confirmBtn">
            Confirmar
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    modal.querySelector('#confirmBtn').addEventListener('click', () => {
      confirmCallback();
      modal.remove();
    });

    modal.querySelector('#cancelBtn').addEventListener('click', () => {
      if (cancelCallback) {
        cancelCallback();
      }
      modal.remove();
    });
  }

  // Mobile specific handlers
  handleVisibilityChange() {
    if (document.hidden && this.activeSession?.status === 'in_progress') {
      if ('serviceWorker' in navigator && 'Notification' in window) {
        navigator.serviceWorker.ready.then(registration => {
          registration.showNotification('Pomodoro en progreso', {
            body: `${this.formatTime(this.timeLeft)} restantes`,
            icon: '/static/img/pomodoro-icon.png',
            vibrate: [200, 100, 200],
            tag: 'pomodoro-notification',
            renotify: false
          });
        });
      }
    }
  }

  handleBackGesture(e) {
    if (this.activeSession?.status === 'in_progress') {
      e.preventDefault();
      this.showConfirmDialog(
        'Sesión en progreso',
        '¿Deseas cancelar la sesión actual?',
        () => this.cancelSession(this.activeSession.session_id)
      );
      return false;
    }
  }

  handleInstallPrompt(e) {
    e.preventDefault();
    this.deferredPrompt = e;
    // Implementar lógica de instalación PWA si se necesita
  }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.pomodoroApp = new PomodoroApp();
});