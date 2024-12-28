document.addEventListener('DOMContentLoaded', function() {
    const profileTrigger = document.querySelector('.profile-trigger');
    const profileSidebar = document.querySelector('.profile-sidebar');
    const closeProfile = document.querySelector('.close-profile');
    const profileOverlay = document.querySelector('.profile-overlay');

    // Open profile sidebar
    profileTrigger.addEventListener('click', function() {
        profileSidebar.classList.add('active');
        profileOverlay.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    });

    // Close profile sidebar
    function closeProfileSidebar() {
        profileSidebar.classList.remove('active');
        profileOverlay.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
    }

    closeProfile.addEventListener('click', closeProfileSidebar);
    profileOverlay.addEventListener('click', closeProfileSidebar);

    // Handle swipe to close
    let touchStartX = 0;
    let touchEndX = 0;

    profileSidebar.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    }, false);

    profileSidebar.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        if (touchStartX < touchEndX && touchEndX - touchStartX > 50) {
            // Swiped right
            closeProfileSidebar();
        }
    }, false);
});