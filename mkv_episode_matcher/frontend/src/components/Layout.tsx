import React from 'react';
import Sidebar from './Sidebar';

interface LayoutProps {
    children: React.ReactNode;
    currentView?: string;
    onNavigate?: (view: string) => void;
    systemStatus: {
        status: string;
        model_loaded: boolean;
        version: string;
    };
}

const Layout: React.FC<LayoutProps> = ({ children, currentView = 'dashboard', onNavigate, systemStatus }) => {
    return (
        <div className="flex h-screen w-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans overflow-hidden">
            {/* Sidebar */}
            {onNavigate && (
                <Sidebar
                    currentView={currentView}
                    onNavigate={onNavigate}
                    systemStatus={systemStatus}
                />
            )}

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
                {/* Background ambient effects */}
                <div className="absolute inset-0 pointer-events-none overflow-hidden">
                    <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[100px]"></div>
                    <div className="absolute bottom-[-20%] left-[-10%] w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[100px]"></div>
                </div>

                {/* Content Container */}
                <div className="flex-1 overflow-auto p-6 lg:p-8 relative z-10">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
