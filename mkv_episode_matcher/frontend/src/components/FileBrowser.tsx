import React, { useState, useEffect } from 'react';

interface FileEntry {
    name: string;
    path: string;
    is_dir: boolean;
    size: number | null;
}

interface FileBrowserProps {
    onSelectionChange?: (files: string[]) => void;
    onDirectorySelect?: (path: string) => void;
}

const FileBrowser: React.FC<FileBrowserProps> = ({ onSelectionChange, onDirectorySelect }) => {
    const [currentPath, setCurrentPath] = useState<string>('');
    const [entries, setEntries] = useState<FileEntry[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

    const fetchDirectory = async (path: string) => {
        setLoading(true);
        try {
            const url = path ? `/scan/browse?path=${encodeURIComponent(path)}` : '/scan/browse';
            const res = await fetch(url);
            if (!res.ok) throw new Error('Failed to fetch');
            const data = await res.json();
            setEntries(data);
            if (path) setCurrentPath(path);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDirectory('');
    }, []);

    const handleNavigate = (entry: FileEntry) => {
        if (entry.is_dir) {
            fetchDirectory(entry.path);
        }
    };

    const navigateUp = () => {
        if (!currentPath) return;

        if (currentPath.match(/^[a-zA-Z]:\\?$/)) {
            fetchDirectory('');
            setCurrentPath('');
            return;
        }

        const sep = currentPath.includes('\\') ? '\\' : '/';
        const parent = currentPath.substring(0, currentPath.lastIndexOf(sep));

        if (!parent) {
            fetchDirectory('');
            setCurrentPath('');
            return;
        }

        if (parent.match(/^[a-zA-Z]:$/)) {
            fetchDirectory(parent + '\\');
        } else {
            fetchDirectory(parent);
        }
    };

    const toggleSelection = (entry: FileEntry) => {
        if (entry.is_dir) return;

        const newSelection = new Set(selectedFiles);
        if (newSelection.has(entry.path)) {
            newSelection.delete(entry.path);
        } else {
            newSelection.add(entry.path);
        }
        setSelectedFiles(newSelection);
        if (onSelectionChange) {
            onSelectionChange(Array.from(newSelection));
        }
    };

    return (
        <div className="h-full flex flex-col bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-color)] overflow-hidden">
            {/* Toolbar */}
            <div className="flex-shrink-0 p-4 bg-[var(--bg-tertiary)]/50 border-b border-[var(--border-color)]">
                <div className="flex items-center gap-3 mb-3">
                    <button
                        onClick={navigateUp}
                        className="px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-muted)] hover:text-white hover:border-[var(--accent-primary)] transition-all disabled:opacity-40"
                        disabled={!currentPath}
                        title="Go Up"
                    >
                        ⬆️
                    </button>
                    <div className="flex-1 px-4 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg font-mono text-sm text-[var(--text-muted)] truncate">
                        {currentPath || '📁 Select a drive'}
                    </div>
                </div>

                <div className="flex items-center justify-between">
                    <span className="text-sm text-[var(--text-muted)]">
                        {selectedFiles.size > 0 ? (
                            <span className="text-[var(--accent-secondary)] font-medium">{selectedFiles.size} file{selectedFiles.size !== 1 && 's'} selected</span>
                        ) : (
                            'No files selected'
                        )}
                    </span>

                    {onDirectorySelect && (
                        <button
                            onClick={() => onDirectorySelect(currentPath)}
                            disabled={!currentPath}
                            className="btn btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            Scan This Folder 🔍
                        </button>
                    )}
                </div>
            </div>

            {/* File List */}
            <div className="flex-1 overflow-auto p-3">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64 text-[var(--text-muted)]">
                        <div className="text-4xl animate-spin mb-3">⏳</div>
                        <div className="text-sm">Loading...</div>
                    </div>
                ) : entries.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-64 text-[var(--text-muted)]">
                        <div className="text-5xl mb-3 opacity-30">📂</div>
                        <div className="text-sm">Empty directory</div>
                    </div>
                ) : (
                    <div className="grid gap-2">
                        {entries.map((entry) => (
                            <div
                                key={entry.path}
                                onClick={() => entry.is_dir ? handleNavigate(entry) : (onSelectionChange && toggleSelection(entry))}
                                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all duration-150 border
                                    ${selectedFiles.has(entry.path)
                                        ? 'bg-[var(--accent-primary)]/15 border-[var(--accent-primary)]/40'
                                        : 'border-transparent hover:bg-[var(--bg-tertiary)] hover:border-[var(--border-color)]'
                                    }`}
                            >
                                <span className="text-2xl flex-shrink-0">
                                    {entry.is_dir ? '📁' : (entry.name.toLowerCase().endsWith('.mkv') ? '🎬' : '📄')}
                                </span>
                                <div className="flex-1 min-w-0">
                                    <div className="font-medium text-[var(--text-primary)] truncate">{entry.name}</div>
                                    {entry.size !== null && (
                                        <div className="text-xs text-[var(--text-muted)]">
                                            {(entry.size / (1024 * 1024)).toFixed(1)} MB
                                        </div>
                                    )}
                                </div>
                                {entry.is_dir && (
                                    <span className="text-[var(--text-muted)] opacity-50">→</span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FileBrowser;
