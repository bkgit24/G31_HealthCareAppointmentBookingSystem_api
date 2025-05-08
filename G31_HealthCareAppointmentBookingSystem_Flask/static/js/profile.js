function toggleSection(id) {
    const content = document.getElementById(`${id}-content`);
    const icon = document.getElementById(`${id}-icon`);
    content.classList.toggle('hidden');
    icon.style.transform = content.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
}

document.getElementById('notificationBtn').addEventListener('click', function() {
    const dialog = document.createElement('div');
    dialog.className = 'notification-overlay';
    dialog.innerHTML = `
        <div class="notification-dialog">
            <div class="notification-header">
                <h3 class="notification-title">Notifications</h3>
                <button class="close-button" onclick="this.closest('.notification-overlay').remove()">
                    <i class="ri-close-line close-icon"></i>
                </button>
            </div>
            <div class="notification-list">
                <div class="notification-item">
                    <div class="notification-icon-container">
                        <i class="ri-calendar-check-line notification-item-icon"></i>
                    </div>
                    <div class="notification-content">
                        <p class="notification-item-title">Appointment Reminder</p>
                        <p class="notification-item-message">Your appointment with Dr. Parker is tomorrow at 10:30 AM</p>
                        <p class="notification-item-time">2 hours ago</p>
                    </div>
                </div>
                <div class="notification-item">
                    <div class="notification-icon-container">
                        <i class="ri-medicine-bottle-line notification-item-icon"></i>
                    </div>
                    <div class="notification-content">
                        <p class="notification-item-title">Prescription Ready</p>
                        <p class="notification-item-message">Your prescription refill is ready for pickup</p>
                        <p class="notification-item-time">1 day ago</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(dialog);
});

document.addEventListener('DOMContentLoaded', function() {
    // Get all action buttons
    const actionButtons = document.querySelectorAll('.action-button');
    
    // Add event listeners to each button
    actionButtons.forEach(button => {
      button.addEventListener('click', function() {
        // Get the title text
        const titleText = this.querySelector('.action-title').textContent.trim();
        
        // Determine which popup to show
        if (titleText === 'Prescriptions') {
          document.getElementById('prescriptions-popup').classList.add('active');
          document.body.style.overflow = 'hidden';
        } else if (titleText === 'Insurance Info') {
          document.getElementById('insurance-popup').classList.add('active');
          document.body.style.overflow = 'hidden';
        }
      });
    });
    
    // Close popup when close button is clicked
    document.querySelectorAll('.popup-close').forEach(button => {
      button.addEventListener('click', function() {
        this.closest('.popup-overlay').classList.remove('active');
        document.body.style.overflow = '';
      });
    });
    
    // Close popup when clicking outside the card
    document.querySelectorAll('.popup-overlay').forEach(overlay => {
      overlay.addEventListener('click', function(event) {
        if (event.target === this) {
          this.classList.remove('active');
          document.body.style.overflow = '';
        }
      });
    });
  });