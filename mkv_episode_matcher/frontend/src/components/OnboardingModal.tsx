import React, { useState } from 'react';

interface OnboardingModalProps {
    onComplete: () => void;
    onSkip?: () => void;
}

interface Config {
    open_subtitles_api_key?: string;
    open_subtitles_username?: string;
    open_subtitles_password?: string;
    tmdb_api_key?: string;
    sub_provider?: string;
}

const OnboardingModal: React.FC<OnboardingModalProps> = ({ onComplete, onSkip }) => {
    const [step, setStep] = useState(1);
    const [config, setConfig] = useState<Config>({
        sub_provider: 'opensubtitles',
        open_subtitles_api_key: '',
        open_subtitles_username: '',
        open_subtitles_password: '',
        tmdb_api_key: '',
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const totalSteps = 3;

    const handleChange = (field: keyof Config, value: string) => {
        setConfig(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        setSaving(true);
        setError(null);

        try {
            const res = await fetch('/system/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            });

            const data = await res.json();
            if (data.status === 'success') {
                onComplete();
            } else {
                throw new Error(data.message || 'Failed to save configuration');
            }
        } catch (err) {
            setError(String(err));
        } finally {
            setSaving(false);
        }
    };

    const canProceed = () => {
        if (step === 2) {
            // OpenSubtitles API key is required
            return config.open_subtitles_api_key && config.open_subtitles_api_key.length > 10;
        }
        return true;
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
            <div className="w-full max-w-2xl mx-4 glass-panel rounded-2xl overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-6">
                    <h2 className="text-2xl font-bold text-white">Welcome to MKV Episode Matcher</h2>
                    <p className="text-indigo-200 mt-1">Let's get you set up in just a few steps</p>

                    {/* Progress Indicators */}
                    <div className="flex gap-2 mt-4">
                        {Array.from({ length: totalSteps }).map((_, idx) => (
                            <div
                                key={idx}
                                className={`h-1.5 flex-1 rounded-full transition-all ${idx + 1 <= step ? 'bg-white' : 'bg-white/30'
                                    }`}
                            />
                        ))}
                    </div>
                </div>

                {/* Content */}
                <div className="p-8">
                    {/* Step 1: Welcome */}
                    {step === 1 && (
                        <div className="space-y-6 animate-fade-in">
                            <div className="text-center">
                                <div className="text-6xl mb-4">🎬</div>
                                <h3 className="text-2xl font-bold text-white mb-3">Automatic Episode Matching</h3>
                                <p className="text-[var(--text-muted)] max-w-md mx-auto">
                                    This tool uses advanced speech recognition to identify TV episodes by matching audio against subtitle transcripts.
                                </p>
                            </div>

                            <div className="grid grid-cols-3 gap-4 mt-8">
                                <div className="text-center p-4 bg-[var(--bg-tertiary)]/30 rounded-xl">
                                    <div className="text-3xl mb-2">🎤</div>
                                    <div className="text-sm text-white font-medium">Whisper ASR</div>
                                    <div className="text-xs text-[var(--text-muted)]">State-of-the-art speech recognition</div>
                                </div>
                                <div className="text-center p-4 bg-[var(--bg-tertiary)]/30 rounded-xl">
                                    <div className="text-3xl mb-2">📝</div>
                                    <div className="text-sm text-white font-medium">Subtitle Matching</div>
                                    <div className="text-xs text-[var(--text-muted)]">Compares against reference subtitles</div>
                                </div>
                                <div className="text-center p-4 bg-[var(--bg-tertiary)]/30 rounded-xl">
                                    <div className="text-3xl mb-2">✨</div>
                                    <div className="text-sm text-white font-medium">Smart Renaming</div>
                                    <div className="text-xs text-[var(--text-muted)]">Automatically renames your files</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Step 2: OpenSubtitles Setup */}
                    {step === 2 && (
                        <div className="space-y-6 animate-fade-in">
                            <div>
                                <h3 className="text-xl font-bold text-white mb-2">OpenSubtitles API Setup</h3>
                                <p className="text-[var(--text-muted)] text-sm">
                                    We need access to OpenSubtitles to download reference subtitles for matching.
                                </p>
                            </div>

                            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                                <div className="flex items-start gap-3">
                                    <span className="text-amber-400 text-xl">💡</span>
                                    <div className="text-sm text-amber-200">
                                        <strong>Don't have an API key?</strong>
                                        <p className="mt-1 text-amber-300/80">
                                            Get one free at{' '}
                                            <a
                                                href="https://www.opensubtitles.com/consumers"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="underline hover:text-white"
                                            >
                                                opensubtitles.com/consumers
                                            </a>
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-muted">API Key *</label>
                                    <input
                                        type="password"
                                        value={config.open_subtitles_api_key || ''}
                                        onChange={(e) => handleChange('open_subtitles_api_key', e.target.value)}
                                        placeholder="Enter your OpenSubtitles API key"
                                        className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-muted">Username (optional)</label>
                                        <input
                                            type="text"
                                            value={config.open_subtitles_username || ''}
                                            onChange={(e) => handleChange('open_subtitles_username', e.target.value)}
                                            placeholder="Username"
                                            className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-muted">Password (optional)</label>
                                        <input
                                            type="password"
                                            value={config.open_subtitles_password || ''}
                                            onChange={(e) => handleChange('open_subtitles_password', e.target.value)}
                                            placeholder="Password"
                                            className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Step 3: TMDb (Optional) */}
                    {step === 3 && (
                        <div className="space-y-6 animate-fade-in">
                            <div>
                                <h3 className="text-xl font-bold text-white mb-2">TMDb API Key (Optional)</h3>
                                <p className="text-[var(--text-muted)] text-sm">
                                    TMDb provides enhanced episode metadata like titles. This step is optional.
                                </p>
                            </div>

                            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                                <div className="flex items-start gap-3">
                                    <span className="text-blue-400 text-xl">ℹ️</span>
                                    <div className="text-sm text-blue-200">
                                        <strong>Get a free API key at</strong>
                                        <p className="mt-1 text-blue-300/80">
                                            <a
                                                href="https://www.themoviedb.org/settings/api"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="underline hover:text-white"
                                            >
                                                themoviedb.org/settings/api
                                            </a>
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted">TMDb API Key</label>
                                <input
                                    type="password"
                                    value={config.tmdb_api_key || ''}
                                    onChange={(e) => handleChange('tmdb_api_key', e.target.value)}
                                    placeholder="Enter your TMDb API key (optional)"
                                    className="w-full bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="mt-8 p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
                                <div className="flex items-center gap-3">
                                    <span className="text-green-400 text-2xl">✅</span>
                                    <div>
                                        <div className="text-green-400 font-bold">You're all set!</div>
                                        <div className="text-sm text-green-300/80">Click "Complete Setup" to start using MKV Episode Matcher</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-8 py-4 border-t border-[var(--border-color)] flex justify-between items-center">
                    <div>
                        {step > 1 && (
                            <button
                                onClick={() => setStep(s => s - 1)}
                                className="px-4 py-2 text-[var(--text-muted)] hover:text-white transition-colors"
                            >
                                ← Back
                            </button>
                        )}
                    </div>

                    <div className="flex gap-3">
                        {onSkip && step === 1 && (
                            <button
                                onClick={onSkip}
                                className="px-4 py-2 text-[var(--text-muted)] hover:text-white transition-colors"
                            >
                                Skip for now
                            </button>
                        )}

                        {step < totalSteps ? (
                            <button
                                onClick={() => setStep(s => s + 1)}
                                disabled={!canProceed()}
                                className={`btn btn-primary px-6 py-2 ${!canProceed() ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                Continue →
                            </button>
                        ) : (
                            <button
                                onClick={handleSave}
                                disabled={saving}
                                className={`btn btn-primary px-6 py-2 ${saving ? 'opacity-70 cursor-wait' : ''}`}
                            >
                                {saving ? 'Saving...' : 'Complete Setup ✨'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OnboardingModal;
