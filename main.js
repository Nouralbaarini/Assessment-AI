// Main JavaScript file for Assessment AI Application

document.addEventListener('DOMContentLoaded', function() {
  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      const sidebar = document.querySelector('.sidebar');
      sidebar.classList.toggle('show');
    });
  }

  // Initialize dropdowns
  const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
  dropdownToggles.forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      const dropdown = this.nextElementSibling;
      dropdown.classList.toggle('show');
      
      // Close other dropdowns
      dropdownToggles.forEach(otherToggle => {
        if (otherToggle !== toggle) {
          otherToggle.nextElementSibling.classList.remove('show');
        }
      });
      
      // Close dropdown when clicking outside
      document.addEventListener('click', function closeDropdown(event) {
        if (!event.target.closest('.dropdown')) {
          dropdown.classList.remove('show');
          document.removeEventListener('click', closeDropdown);
        }
      });
    });
  });

  // File upload preview
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', function() {
      const fileNameElement = this.parentElement.querySelector('.file-name');
      if (fileNameElement && this.files.length > 0) {
        fileNameElement.textContent = this.files[0].name;
      }
    });
  });

  // Initialize tooltips
  const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
  tooltips.forEach(tooltip => {
    tooltip.addEventListener('mouseenter', function() {
      const tip = document.createElement('div');
      tip.className = 'tooltip';
      tip.textContent = this.getAttribute('title');
      
      const rect = this.getBoundingClientRect();
      tip.style.top = `${rect.top - 10}px`;
      tip.style.left = `${rect.left + rect.width / 2}px`;
      
      document.body.appendChild(tip);
      
      this.addEventListener('mouseleave', function() {
        document.body.removeChild(tip);
      }, { once: true });
    });
  });

  // AJAX form submissions with CSRF protection
  const ajaxForms = document.querySelectorAll('form[data-ajax="true"]');
  ajaxForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const formData = new FormData(this);
      const url = this.getAttribute('action');
      const method = this.getAttribute('method') || 'POST';
      const submitBtn = this.querySelector('[type="submit"]');
      
      if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
      }
      
      fetch(url, {
        method: method,
        body: formData,
        headers: {
          'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        credentials: 'same-origin'
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          if (data.redirect) {
            window.location.href = data.redirect;
          } else {
            // Show success message
            const successAlert = document.createElement('div');
            successAlert.className = 'alert alert-success';
            successAlert.textContent = data.message || 'Operation completed successfully';
            
            const alertContainer = document.querySelector('.alert-container') || this.parentElement;
            alertContainer.prepend(successAlert);
            
            // Remove alert after 5 seconds
            setTimeout(() => {
              successAlert.remove();
            }, 5000);
          }
        } else {
          // Show error message
          const errorAlert = document.createElement('div');
          errorAlert.className = 'alert alert-danger';
          errorAlert.textContent = data.error || 'An error occurred';
          
          const alertContainer = document.querySelector('.alert-container') || this.parentElement;
          alertContainer.prepend(errorAlert);
        }
      })
      .catch(error => {
        console.error('Error:', error);
        
        // Show error message
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger';
        errorAlert.textContent = 'An unexpected error occurred';
        
        const alertContainer = document.querySelector('.alert-container') || this.parentElement;
        alertContainer.prepend(errorAlert);
      })
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      });
    });
  });

  // Initialize sortable elements for drag and drop
  const sortableContainers = document.querySelectorAll('.sortable');
  if (window.Sortable && sortableContainers.length > 0) {
    sortableContainers.forEach(container => {
      new Sortable(container, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        dragClass: 'sortable-drag',
        handle: '.drag-handle',
        onEnd: function(evt) {
          // Update positions after drag
          const items = container.querySelectorAll('.sortable-item');
          const positions = Array.from(items).map((item, index) => {
            return {
              id: item.dataset.id,
              position: index
            };
          });
          
          // Send updated positions to server if endpoint is specified
          const updateUrl = container.dataset.updateUrl;
          if (updateUrl) {
            fetch(updateUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
              },
              body: JSON.stringify({ positions: positions }),
              credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
              if (!data.success) {
                console.error('Error updating positions:', data.error);
              }
            })
            .catch(error => {
              console.error('Error:', error);
            });
          }
        }
      });
    });
  }

  // Initialize charts if Chart.js is available and there are chart containers
  const chartContainers = document.querySelectorAll('.chart-container');
  if (window.Chart && chartContainers.length > 0) {
    chartContainers.forEach(container => {
      const canvas = container.querySelector('canvas');
      if (!canvas) return;
      
      const chartType = container.dataset.chartType || 'bar';
      const chartData = JSON.parse(container.dataset.chartData || '{}');
      const chartOptions = JSON.parse(container.dataset.chartOptions || '{}');
      
      new Chart(canvas, {
        type: chartType,
        data: chartData,
        options: chartOptions
      });
    });
  }

  // Admin website customization drag and drop
  const sectionDropzones = document.querySelectorAll('.section-dropzone');
  if (window.Sortable && sectionDropzones.length > 0) {
    sectionDropzones.forEach(dropzone => {
      new Sortable(dropzone, {
        group: 'sections',
        animation: 150,
        ghostClass: 'dropzone-ghost',
        chosenClass: 'dropzone-chosen',
        dragClass: 'dropzone-drag',
        onEnd: function(evt) {
          // Save layout after drag
          const layoutId = dropzone.dataset.layoutId;
          const sectionIds = Array.from(dropzone.querySelectorAll('.section-item'))
            .map(item => item.dataset.sectionId);
          
          if (layoutId) {
            fetch('/api/save-layout', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
              },
              body: JSON.stringify({
                layout_id: layoutId,
                sections: sectionIds
              }),
              credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
              if (!data.success) {
                console.error('Error saving layout:', data.error);
              }
            })
            .catch(error => {
              console.error('Error:', error);
            });
          }
        }
      });
    });
  }
});

// Function to mark student work via AJAX
function markStudentWork(workId) {
  const markBtn = document.querySelector(`button[data-work-id="${workId}"]`);
  if (markBtn) {
    markBtn.disabled = true;
    markBtn.innerHTML = '<span class="spinner"></span> Marking...';
  }
  
  fetch('/api/mark-work', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
    },
    body: JSON.stringify({ work_id: workId }),
    credentials: 'same-origin'
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      window.location.href = `/teacher/assessments/${data.assessment_id}/student-work/${workId}`;
    } else {
      alert('Error marking work: ' + (data.error || 'Unknown error'));
      if (markBtn) {
        markBtn.disabled = false;
        markBtn.innerHTML = 'Mark Work';
      }
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('An unexpected error occurred while marking the work');
    if (markBtn) {
      markBtn.disabled = false;
      markBtn.innerHTML = 'Mark Work';
    }
  });
}

// Function to generate analytics via AJAX
function generateAnalytics(assessmentId) {
  const analyticsBtn = document.querySelector(`button[data-assessment-id="${assessmentId}"]`);
  if (analyticsBtn) {
    analyticsBtn.disabled = true;
    analyticsBtn.innerHTML = '<span class="spinner"></span> Generating...';
  }
  
  fetch('/api/generate-analytics', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
    },
    body: JSON.stringify({ assessment_id: assessmentId }),
    credentials: 'same-origin'
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Generate recommendations after analytics
      generateRecommendations(data.analytics_id);
    } else {
      alert('Error generating analytics: ' + (data.error || 'Unknown error'));
      if (analyticsBtn) {
        analyticsBtn.disabled = false;
        analyticsBtn.innerHTML = 'Generate Analytics';
      }
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('An unexpected error occurred while generating analytics');
    if (analyticsBtn) {
      analyticsBtn.disabled = false;
      analyticsBtn.innerHTML = 'Generate Analytics';
    }
  });
}

// Function to generate recommendations via AJAX
function generateRecommendations(analyticsId) {
  fetch('/api/generate-recommendations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
    },
    body: JSON.stringify({ analytics_id: analyticsId }),
    credentials: 'same-origin'
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      window.location.reload();
    } else {
      alert('Error generating recommendations: ' + (data.error || 'Unknown error'));
      const analyticsBtn = document.querySelector('button[data-analytics-id]');
      if (analyticsBtn) {
        analyticsBtn.disabled = false;
        analyticsBtn.innerHTML = 'Generate Analytics';
      }
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('An unexpected error occurred while generating recommendations');
    const analyticsBtn = document.querySelector('button[data-analytics-id]');
    if (analyticsBtn) {
      analyticsBtn.disabled = false;
      analyticsBtn.innerHTML = 'Generate Analytics';
    }
  });
}
