document.addEventListener('DOMContentLoaded', () => {
  // Check if we're on the honeypot builder page
  const form = document.getElementById('honeypot-form');
  if (form) {
    const typeEl = form.querySelector('#type');
    const portEl = form.querySelector('#port');
    const msgEl = document.getElementById('form-status');
    const checkPortBtn = document.getElementById('check-port');
    const portStatus = document.getElementById('port-status');

    // 1) load types
    fetch('/api/honeypot/types')
      .then(r => r.json())
      .then(types => {
        typeEl.innerHTML = '<option value="">Select type…</option>';
        types.forEach(t => {
          const o = document.createElement('option');
          o.value = t; o.textContent = t;
          typeEl.append(o);
        });
      })
      .catch(() => {
        typeEl.innerHTML = '<option value="">Error loading types</option>';
      });

    // Check port availability
    if (checkPortBtn) {
      checkPortBtn.addEventListener('click', () => {
        const port = portEl.value;
        if (!port) {
          portStatus.textContent = 'Please enter a port number';
          portStatus.classList.remove('hidden');
          return;
        }

        checkPortBtn.disabled = true;
        checkPortBtn.textContent = 'Checking...';

        fetch(`/api/honeypot/port-check/${port}`)
          .then(r => r.json())
          .then(data => {
            portStatus.textContent = data.message;
            portStatus.classList.remove('hidden');
            if (data.available) {
              portStatus.classList.add('text-success');
              portStatus.classList.remove('text-danger');
            } else {
              portStatus.classList.add('text-danger');
              portStatus.classList.remove('text-success');
            }
          })
          .catch(err => {
            console.error('Port check failed:', err);
            portStatus.textContent = 'Error checking port';
            portStatus.classList.remove('hidden');
            portStatus.classList.add('text-danger');
          })
          .finally(() => {
            checkPortBtn.disabled = false;
            checkPortBtn.textContent = 'Check';
          });
      });
    }

    // 2) submit form
    form.addEventListener('submit', e => {
      e.preventDefault();
      msgEl.classList.add('hidden');

      // Show loading overlay
      if (window.loadingOverlay) {
        window.loadingOverlay.show('Deploying honeypot...');
      }

      // Get form data
      const formData = new FormData(form);
      
      // Build payload
      const payload = {
        type: formData.get('type'),
        port: Number(formData.get('port')),
        cpu_period: Number(formData.get('cpu_period')),
        cpu_quota: Number(formData.get('cpu_quota')),
        memory_limit: formData.get('memory_limit'),
        memory_swap_limit: formData.get('memory_swap_limit'),
        banner: formData.get('banner') || "",
        authentication: {
          allowed_users: []
        }
      };
      
      // Add authentication if present
      const authEntries = document.querySelectorAll('.authentication-entry');
      authEntries.forEach((entry, index) => {
        const username = formData.get(`auth_username_${index}`);
        const password = formData.get(`auth_password_${index}`);
        if (username && password) {
          payload.authentication.allowed_users.push({
            username: username,
            password: password
          });
        }
      });

      // Show loading state
      const deployBtn = document.getElementById('deploy-btn');
      const deployText = document.getElementById('deploy-text');
      const deploySpinner = document.getElementById('deploy-spinner');
      
      if (deployBtn && deployText && deploySpinner) {
        deployBtn.disabled = true;
        deployText.textContent = "DEPLOYING...";
        deploySpinner.classList.remove("hidden");
      }

      fetch('/api/honeypot/create', {
        method: 'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      })
      .then(r => r.json().then(b => ({status:r.status, body:b})))
      .then(({status,body})=> {
        msgEl.textContent = status===201
          ? '✅ Honeypot created successfully! Redirecting...'
          : `❌ ${body.detail||body.error||'Failed to create honeypot'}`;
        msgEl.classList.remove('hidden');
        msgEl.classList.toggle('text-green-400', status===201);
        msgEl.classList.toggle('text-red-400', status!==201);
        
        if (status === 201) {
          setTimeout(() => {
            window.location.href = '/honeypots';
          }, 1500);
        } else {
          // Reset button on error
          if (deployBtn && deployText && deploySpinner) {
            deployBtn.disabled = false;
            deployText.textContent = "DEPLOY HONEYPOT";
            deploySpinner.classList.add("hidden");
          }
          
          // Hide loading overlay on error
          if (window.loadingOverlay) {
            window.loadingOverlay.hide(true);
          }
        }
      })
      .catch(() => {
        msgEl.textContent = '❌ Network error';
        msgEl.classList.remove('hidden','text-green-400');
        msgEl.classList.add('text-red-400');
        
        // Reset button
        if (deployBtn && deployText && deploySpinner) {
          deployBtn.disabled = false;
          deployText.textContent = "DEPLOY HONEYPOT";
          deploySpinner.classList.add("hidden");
        }
        
        // Hide loading overlay on error
        if (window.loadingOverlay) {
          window.loadingOverlay.hide(true);
        }
      });
    });
  }

  // Mobile menu functionality
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  if (mobileMenuButton) {
    const mobileMenu = document.getElementById('mobile-menu');
    mobileMenuButton.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      // Rest of the existing mobile menu code...
    });
  }
  
  // Add global page transition handling
  document.querySelectorAll('a').forEach(link => {
    // Only handle internal links that aren't # or javascript: links
    if (link.href && 
        link.href.startsWith(window.location.origin) && 
        !link.href.includes('#') && 
        !link.href.startsWith('javascript:') &&
        !link.classList.contains('no-loader')) {
      
      link.addEventListener('click', (e) => {
        // Don't handle special function links
        if (link.getAttribute('target') === '_blank' || 
            link.getAttribute('download') || 
            e.ctrlKey || e.metaKey) {
          return;
        }
        
        e.preventDefault();
        
        // Show loading overlay for page navigation
        if (window.loadingOverlay) {
          window.loadingOverlay.show('Loading page...');
        }
        
        // Navigate after small delay to ensure loading overlay is visible
        setTimeout(() => {
          window.location.href = link.href;
        }, 300);
      });
    }
  });
});

// Listen for browser back/forward navigation
window.addEventListener('beforeunload', () => {
  // Show loading overlay when navigating away
  if (window.loadingOverlay) {
    window.loadingOverlay.show('Loading...');
  }
});
