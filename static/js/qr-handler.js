// QR code handling script
document.addEventListener('DOMContentLoaded', function() {
  // Get elements
  const qrCodeSection = document.getElementById('qr-code-section');
  const qrCodeImage = document.getElementById('qr-code-image');
  const countdownDisplay = document.getElementById('countdown-display');
  const generateButton = document.getElementById('generate-qr-button');
  
  // Function to refresh QR code via AJAX
  function refreshQRCode() {
    // Get session info from URL
    const urlPath = window.location.pathname;
    const pathParts = urlPath.split('/');
    
    // Find course_id and session_id from URL
    let courseId, sessionId;
    for(let i = 0; i < pathParts.length; i++) {
      if(pathParts[i] === 'course' || pathParts[i] === 'courses') {
        courseId = pathParts[i+1];
      }
      if(pathParts[i] === 'session' || pathParts[i] === 'sessions') {
        sessionId = pathParts[i+1];
      }
    }
    
    if(!courseId || !sessionId) {
      console.error('Could not determine course or session ID');
      return;
    }
    
    console.log(`Refreshing QR code for course: ${courseId}, session: ${sessionId}`);
    
    // Make AJAX call to refresh QR code
    fetch(`/courses/${courseId}/sessions/${sessionId}/refresh-qr/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: 'duration=10'
    })
    .then(response => {
      if(!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if(data.success) {
        console.log('QR code refreshed successfully');
        // If there's a QR image placeholder, update it
        if(qrCodeImage) {
          qrCodeImage.src = data.qr_image;
          
          // Remove any expired message
          const expiredMessage = document.querySelector('.alert-warning');
          if(expiredMessage) {
            expiredMessage.remove();
          }
          
          // Reset countdown if it exists
          if(countdownDisplay) {
            timeLeft = 10;
            countdownDisplay.textContent = timeLeft;
          }
        }
      } else {
        console.error('Failed to generate QR code:', data.error || 'Unknown error');
      }
    })
    .catch(error => {
      console.error('Error generating QR code:', error);
    });
  }
  
  // If generate button exists, attach click handler
  if (generateButton) {
    generateButton.addEventListener('click', function(e) {
      e.preventDefault();
      refreshQRCode();
    });
  }
  
  // Helper function to get CSRF token
  function getCookie(name) {
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
  
  // Countdown functionality with auto-refresh for QR display page
  if (countdownDisplay && qrCodeSection) {
    let timeLeft = parseInt(countdownDisplay.textContent) || 10;
    let refreshInterval = setInterval(function() {
      timeLeft--;
      countdownDisplay.textContent = timeLeft;
      
      // Change color when time is running out
      if (timeLeft <= 3) {
        countdownDisplay.style.color = 'red';
      } else {
        countdownDisplay.style.color = '';
      }
      
      // When countdown reaches zero, refresh the QR code
      if (timeLeft <= 0) {
        console.log('Countdown reached zero, refreshing QR code...');
        refreshQRCode();
        timeLeft = 10; // Reset countdown
      }
    }, 1000);
  }
});
