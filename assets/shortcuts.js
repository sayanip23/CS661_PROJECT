document.addEventListener('keydown', function(e) {
    // Check if the user is typing in an input field (we don't want to override shortcuts here unless it's Ctrl+K)
    const isInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA';

    // Ctrl + K or Cmd + K (Command Palette)
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault(); // Prevent browser search bar
        
        // Find the command palette toggle button (hidden in layout) and click it
        const toggleBtn = document.getElementById('cmd-palette-toggle');
        if (toggleBtn) {
            toggleBtn.click();
        }
    }
    
    // Ctrl + D (Toggle Theme)
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        const themeBtn = document.getElementById('theme-toggle-btn');
        if (themeBtn) {
            themeBtn.click();
        }
    }
    
    // Ctrl + F (Focus Search)
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f' && !isInput) {
        e.preventDefault();
        const searchInput = document.querySelector('#global-search-input input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // ESC (Close Modals/Drawers or Clear Focus)
    if (e.key === 'Escape') {
        if (isInput) {
            e.target.blur();
        }
    }
});
