// Copy wallet address to clipboard
document.addEventListener('DOMContentLoaded', function() {
    const walletAddresses = document.querySelectorAll('code');
    walletAddresses.forEach(address => {
        address.addEventListener('click', function() {
            navigator.clipboard.writeText(this.textContent).then(() => {
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                setTimeout(() => {
                    this.textContent = originalText;
                }, 2000);
            });
        });
        address.style.cursor = 'pointer';
    });

    // Auto-refresh blockchain status every 30 seconds
    if (document.querySelector('.table')) {
        setInterval(() => {
            window.location.reload();
        }, 30000);
    }
}); 