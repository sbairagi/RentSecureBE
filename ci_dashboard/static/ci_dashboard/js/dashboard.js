/**
 * CI Dashboard JavaScript
 * Handles auto-refresh, SSE log streaming, and UI interactions.
 */

const CI_Dashboard = (function () {
    'use strict';

    // Auto-refresh for running workflows
    let refreshInterval: number | null = null;
    const REFRESH_DELAY = 10000; // 10 seconds

    function startAutoRefresh() {
        if (refreshInterval) return;
        refreshInterval = window.setInterval(() => {
            if (document.querySelector('[data-running]')) {
                location.reload();
            }
        }, REFRESH_DELAY);
    }

    function stopAutoRefresh() {
        if (refreshInterval) {
            window.clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }

    // SSE Log Streaming
    let eventSource: EventSource | null = null;

    function connectSSE(url: string) {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource(url);

        eventSource.addEventListener('log', (event) => {
            const entry = JSON.parse(event.data);
            appendLogEntry(entry);
        });

        eventSource.addEventListener('end', () => {
            eventSource.close();
            eventSource = null;
            stopAutoRefresh();
            // Reload to show final state
            setTimeout(() => location.reload(), 1000);
        });

        eventSource.onerror = () => {
            eventSource?.close();
            eventSource = null;
            // Retry after 3 seconds
            setTimeout(() => connectSSE(url), 3000);
        };
    }

    function appendLogEntry(entry: { id: number; content: string; stream: string; timestamp: string }) {
        const container = document.getElementById('log-container');
        if (!container) return;

        const entriesDiv = container.querySelector('.log-entries');
        if (!entriesDiv) return;

        const div = document.createElement('div');
        div.className = `log-entry log-${entry.stream}`;
        const time = new Date(entry.timestamp).toLocaleTimeString();
        div.innerHTML = `<span class="log-time">${time}</span><span class="log-content">${escapeHtml(entry.content)}</span>`;
        entriesDiv.appendChild(div);

        // Auto-scroll if enabled
        const autoScroll = document.getElementById('auto-scroll-status');
        if (autoScroll && autoScroll.textContent === 'ON') {
            container.scrollTop = container.scrollHeight;
        }
    }

    function escapeHtml(text: string): string {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Auto-scroll toggle
    function toggleAutoScroll() {
        const status = document.getElementById('auto-scroll-status');
        if (status) {
            status.textContent = status.textContent === 'ON' ? 'OFF' : 'ON';
        }
    }

    // Download logs
    function downloadLogs(runId: string) {
        window.location.href = `/ci/logs/${runId}/download/`;
    }

    // Initialize on DOM ready
    function init() {
        startAutoRefresh();

        // Global button handlers
        document.addEventListener('click', (event) => {
            const target = event.target as HTMLElement;
            if (target.id === 'btn-auto-scroll') {
                toggleAutoScroll();
            }
        });
    }

    // Export public methods
    return {
        init,
        connectSSE,
        appendLogEntry,
        toggleAutoScroll,
        downloadLogs,
        startAutoRefresh,
        stopAutoRefresh,
    };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', CI_Dashboard.init);
