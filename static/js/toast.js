function showToast(title, message, type = 'normal', duration = 3000) {
    const toastComponent = document.getElementById('toast-component');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');
    
    if (!toastComponent) return;

    // Remove all type classes first
    toastComponent.classList.remove(
        'bg-red-50', 'border-red-500',
        'bg-green-50', 'border-green-500',
        'bg-blue-50', 'border-blue-500',
        'bg-white', 'border-gray-300'
    );

    toastTitle.classList.remove('text-red-600', 'text-green-600', 'text-blue-600', 'text-gray-800');
    toastMessage.classList.remove('text-red-700', 'text-green-700', 'text-blue-700', 'text-gray-600');
    toastIcon.classList.remove('text-red-500', 'text-green-500', 'text-blue-500', 'text-gray-500');

    // Set type styles and icon
    if (type === 'success') {
        toastComponent.classList.add('bg-green-50', 'border-green-500', 'border-2');
        toastTitle.classList.add('text-green-600');
        toastMessage.classList.add('text-green-700');
        toastIcon.classList.add('text-green-500');
        toastIcon.textContent = '✓';
    } else if (type === 'error') {
        toastComponent.classList.add('bg-red-50', 'border-red-500', 'border-2');
        toastTitle.classList.add('text-red-600');
        toastMessage.classList.add('text-red-700');
        toastIcon.classList.add('text-red-500');
        toastIcon.textContent = '✕';
    } else if (type === 'info') {
        toastComponent.classList.add('bg-blue-50', 'border-blue-500', 'border-2');
        toastTitle.classList.add('text-blue-600');
        toastMessage.classList.add('text-blue-700');
        toastIcon.classList.add('text-blue-500');
        toastIcon.textContent = 'ℹ';
    } else {
        toastComponent.classList.add('bg-white', 'border-gray-300', 'border');
        toastTitle.classList.add('text-gray-800');
        toastMessage.classList.add('text-gray-600');
        toastIcon.classList.add('text-gray-500');
        toastIcon.textContent = '●';
    }

    toastTitle.textContent = title;
    toastMessage.textContent = message;

    // Show toast
    toastComponent.classList.remove('opacity-0', 'translate-y-64');
    toastComponent.classList.add('opacity-100', 'translate-y-0');

    // Hide toast after duration
    setTimeout(() => {
        toastComponent.classList.remove('opacity-100', 'translate-y-0');
        toastComponent.classList.add('opacity-0', 'translate-y-64');
    }, duration);
}