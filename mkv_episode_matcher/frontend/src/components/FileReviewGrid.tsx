import React from 'react';

interface ScannedFile {
    path: string;
    name: string;
    series: string | null;
    season: number | null;
    is_processed: boolean;
}

interface FileReviewGridProps {
    files: ScannedFile[];
    onRemove: (path: string) => void;
}

const FileReviewGrid: React.FC<FileReviewGridProps> = ({ files, onRemove }) => {
    return (
        <div className="flex flex-col h-full bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-color)]">
            <div className="grid grid-cols-12 gap-4 p-4 border-b border-[var(--border-color)] font-medium text-sm text-muted uppercase">
                <div className="col-span-6">File</div>
                <div className="col-span-3">Detected Context</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-1 text-right">Action</div>
            </div>

            <div className="flex-1 overflow-auto divide-y divide-[var(--border-color)]">
                {files.map((file) => (
                    <div key={file.path} className="grid grid-cols-12 gap-4 p-4 items-center hover:bg-[var(--bg-tertiary)] transition-colors">

                        {/* File Info */}
                        <div className="col-span-6 min-w-0">
                            <div className="font-medium truncate" title={file.name}>{file.name}</div>
                            <div className="text-xs text-muted truncate" title={file.path}>{file.path}</div>
                        </div>

                        {/* Context */}
                        <div className="col-span-3">
                            {file.series ? (
                                <div className="flex flex-col">
                                    <span className="text-green-400 font-medium">{file.series}</span>
                                    <span className="text-xs text-muted">Season {file.season}</span>
                                </div>
                            ) : (
                                <span className="text-yellow-500 text-sm">Unknown Series</span>
                            )}
                        </div>

                        {/* Status */}
                        <div className="col-span-2">
                            {file.is_processed ? (
                                <span className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-400">Processed</span>
                            ) : (
                                <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">New</span>
                            )}
                        </div>

                        {/* Action */}
                        <div className="col-span-1 text-right">
                            <button
                                onClick={() => onRemove(file.path)}
                                className="text-red-400 hover:text-red-300 hover:bg-red-900/20 p-1 rounded transition-colors"
                                title="Remove from selection"
                            >
                                ✖
                            </button>
                        </div>

                    </div>
                ))}

                {files.length === 0 && (
                    <div className="p-8 text-center text-muted">
                        No MKV files found in this directory.
                    </div>
                )}
            </div>
        </div>
    );
};

export default FileReviewGrid;
