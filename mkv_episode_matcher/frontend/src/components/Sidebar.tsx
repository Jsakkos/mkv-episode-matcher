import React from 'react';

interface SidebarProps {
    currentView: string;
    onNavigate: (view: string) => void;
    systemStatus: {
        status: string;
        model_loaded: boolean;
        version: string;
    };
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onNavigate, systemStatus }) => {
    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: '📺' },
        { id: 'settings', label: 'Settings', icon: '⚙️' },
        { id: 'help', label: 'Help', icon: '❓' },
    ];

    const getStatusColor = () => {
        switch (systemStatus.status) {
            case 'ready': return 'green';
            case 'loading': return 'blue';
            default: return 'red';
        }
    };

    const statusColor = getStatusColor();

    const handleShutdown = async () => {
        if (confirm('Are you sure you want to shut down the server?')) {
            try {
                await fetch('/system/shutdown', { method: 'POST' });
                // Force reload/close window or show disconnected state
                document.body.innerHTML = `
                    <div style="height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0f172a; color: white; font-family: system-ui, sans-serif;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">😴</div>
                        <h1 style="font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;">Server Shutdown</h1>
                        <p style="color: #94a3b8;">You can close this window now.</p>
                    </div>
                `;
            } catch (err) {
                console.error('Shutdown failed:', err);
                alert('Failed to shut down server');
            }
        }
    };

    return (
        <aside className="w-72 flex-shrink-0 flex flex-col bg-[var(--glass-bg)] backdrop-blur-xl border-r border-[var(--glass-border)]">
            {/* Logo Section */}
            <div className="p-6 border-b border-[var(--border-color)]">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
                    MKV Matcher
                </h1>
                <p className="text-xs text-[var(--text-muted)] mt-1">Episode Identifier v{systemStatus.version}</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2">
                {menuItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200
                            ${currentView === item.id
                                ? 'bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)] text-white shadow-lg shadow-indigo-500/25'
                                : 'text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]'
                            }`}
                    >
                        <span className="text-xl">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                    </button>
                ))}
            </nav>

            {/* System Status */}
            <div className="p-4 border-t border-[var(--border-color)]">
                <div className={`p-4 rounded-xl border bg-${statusColor}-500/10 border-${statusColor}-500/20`}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className={`w-2.5 h-2.5 rounded-full bg-${statusColor}-400 ${systemStatus.status === 'loading' ? 'animate-pulse' : ''} shadow-[0_0_8px_rgba(74,222,128,0.5)]`} />
                        <span className={`text-sm font-bold uppercase tracking-wide text-${statusColor}-400`}>
                            {systemStatus.status === 'ready' ? 'System Ready' :
                                systemStatus.status === 'loading' ? 'Initializing' : 'Error'}
                        </span>
                    </div>
                    <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                        {systemStatus.status === 'ready'
                            ? 'ASR engine loaded and ready.'
                            : systemStatus.status === 'loading'
                                ? 'Loading Whisper ASR model...'
                                : 'Failed to load resources.'}
                    </p>
                </div>
            </div>

            {/* Shutdown Button */}
            <div className="p-4 pt-0">
                <button
                    onClick={handleShutdown}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition-all text-sm font-medium"
                >
                    <span>🔴</span>
                    <span>Shut Down Server</span>
                </button>
            </div>
        </aside >
    );
};

export default Sidebar;
