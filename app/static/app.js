const statusText = document.querySelector('#status');
const version = document.querySelector('#version');
const environment = document.querySelector('#environment');
const refresh = document.querySelector('#refresh');

async function checkHealth() {
  refresh.disabled = true;
  statusText.textContent = 'Checking backend…';
  try {
    const response = await fetch('/api/v1/health', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const health = await response.json();
    statusText.textContent = health.status === 'ok' ? 'Backend is online' : 'Unexpected service status';
    version.textContent = health.version;
    environment.textContent = health.environment;
  } catch (error) {
    statusText.textContent = `Connection failed: ${error.message}`;
    version.textContent = '—';
    environment.textContent = '—';
  } finally {
    refresh.disabled = false;
  }
}

refresh.addEventListener('click', checkHealth);
checkHealth();
