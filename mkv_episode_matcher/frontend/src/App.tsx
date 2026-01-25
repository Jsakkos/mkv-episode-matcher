import { useState, useEffect } from 'react';
import Layout from './components/Layout';
import FileBrowser from './components/FileBrowser';
import FileReviewGrid from './components/FileReviewGrid';
import SettingsView from './components/SettingsView';
import OnboardingModal from './components/OnboardingModal';

interface ScannedFile {
  path: string;
  name: string;
  series: string | null;
  season: number | null;
  is_processed: boolean;
}

interface JobResult {
  original_file: string;
  series: string;
  season: number;
  episode: number;
  title: string;
  confidence: number;
}

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'not_found';
  results?: JobResult[];
  failures?: string[];
  error?: string;
  progress?: { current: number; total: number; filename: string };
  phase?: { name: string; message: string };
}

type WorkflowState = 'IDLE' | 'SCANNING' | 'REVIEW' | 'PROCESSING' | 'DONE';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [workflowState, setWorkflowState] = useState<WorkflowState>('IDLE');
  const [scannedFiles, setScannedFiles] = useState<ScannedFile[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [systemStatus, setSystemStatus] = useState({ status: 'loading', model_loaded: false, version: '...' });
  const [activityLog, setActivityLog] = useState<{ time: string, message: string, type: 'info' | 'success' | 'warning' }[]>([]);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Check if onboarding is needed
  useEffect(() => {
    const checkOnboarding = async () => {
      try {
        const res = await fetch('/system/config/validate');
        if (res.ok) {
          const data = await res.json();
          if (data.needs_onboarding) {
            setShowOnboarding(true);
          }
        }
      } catch (err) {
        console.error('Failed to check config:', err);
      }
    };
    checkOnboarding();
  }, []);

  // Poll system status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('/system/status');
        if (res.ok) {
          const data = await res.json();
          setSystemStatus(data);
        } else {
          setSystemStatus(prev => ({ ...prev, status: 'error' }));
        }
      } catch {
        setSystemStatus(prev => ({ ...prev, status: 'error' }));
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handlers
  const handleFolderSelect = async (path: string) => {
    if (systemStatus.status !== 'ready') {
      alert('Please wait for the system to initialize.');
      return;
    }
    setWorkflowState('SCANNING');
    try {
      const res = await fetch('/scan/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      });
      if (!res.ok) throw new Error('Scan failed');
      const data = await res.json();
      // Filter out already-processed files by default
      const unprocessedFiles = data.files.filter((f: ScannedFile) => !f.is_processed);
      setScannedFiles(unprocessedFiles);
      setWorkflowState('REVIEW');
    } catch (err) {
      console.error(err);
      alert('Failed to scan directory');
      setWorkflowState('IDLE');
    }
  };

  const handleStartMatch = async () => {
    setWorkflowState('PROCESSING');
    setJobStatus(null);
    try {
      const filesToProcess = scannedFiles.map(f => f.path);
      const res = await fetch('/match/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: filesToProcess })
      });
      const data = await res.json();
      setJobId(data.job_id);
    } catch (err) {
      console.error(err);
      alert('Failed to start matching');
      setWorkflowState('REVIEW');
    }
  };

  const handleRemoveFile = (pathToRemove: string) => {
    setScannedFiles(prev => prev.filter(f => f.path !== pathToRemove));
  };

  const resetWorkflow = () => {
    setWorkflowState('IDLE');
    setScannedFiles([]);
    setJobId(null);
    setJobStatus(null);
    setActivityLog([]);
  };

  // WebSocket logic replaces polling
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    let ws: WebSocket;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => console.log('Connected to WebSocket');

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const timestamp = new Date().toLocaleTimeString();

          // Filter messages for current job or general updates
          if (msg.type === 'job_update' && msg.job_id === jobId) {
            setJobStatus(prev => ({ ...prev, status: msg.status } as JobStatus));
            setActivityLog(prev => [...prev.slice(-50), { time: timestamp, message: `Job status: ${msg.status}`, type: 'info' }]);
          }
          else if (msg.type === 'progress' && msg.job_id === jobId) {
            setJobStatus(prev => ({
              ...prev,
              status: 'processing',
              progress: { current: msg.current, total: msg.total, filename: msg.filename }
            } as JobStatus));
          }
          else if (msg.type === 'job_complete' && msg.job_id === jobId) {
            setJobStatus({
              status: 'completed',
              results: msg.results,
              failures: msg.failures
            });
            setActivityLog(prev => [...prev.slice(-50), { time: timestamp, message: `✅ Completed! ${msg.results?.length || 0} matched, ${msg.failures?.length || 0} failed`, type: 'success' }]);
          }
          else if (msg.type === 'job_failed' && msg.job_id === jobId) {
            setJobStatus({ status: 'failed', error: msg.error });
            setActivityLog(prev => [...prev.slice(-50), { time: timestamp, message: `❌ Failed: ${msg.error}`, type: 'warning' }]);
          }
          else if (msg.type === 'phase_update' && msg.job_id === jobId) {
            setJobStatus(prev => ({
              ...prev,
              phase: { name: msg.phase, message: msg.message }
            } as JobStatus));
            setActivityLog(prev => [...prev.slice(-50), { time: timestamp, message: msg.message, type: 'info' }]);
          }
        } catch (err) {
          console.error('WS Error:', err);
        }
      };

      ws.onclose = () => {
        // Reconnect logic could go here
        console.log('WS Disconnected');
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
    };
  }, [jobId]);

  // Render content based on view
  // Render content based on view
  const renderContent = () => {
    if (currentView === 'settings') {
      return <SettingsView />;
    }

    if (currentView === 'help') {
      return (
        <div className="max-w-3xl mx-auto glass-panel p-8 rounded-2xl animate-fade-in">
          <h2 className="text-3xl font-bold mb-6 heading-gradient">Help & Documentation</h2>
          <div className="prose prose-invert max-w-none">
            <p className="text-lg text-muted">Welcome to MKV Episode Matcher! This tool helps you automatically rename and organize your TV show collection.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-8">
              <div className="p-6 rounded-xl bg-[var(--bg-tertiary)]/30 border border-[var(--border-color)]">
                <div className="text-2xl mb-2">📂</div>
                <h4 className="font-bold text-white mb-2">1. Select Folder</h4>
                <p className="text-sm text-muted">Navigate to the folder containing your media files. The tool works best with flat directories.</p>
              </div>
              <div className="p-6 rounded-xl bg-[var(--bg-tertiary)]/30 border border-[var(--border-color)]">
                <div className="text-2xl mb-2">🔍</div>
                <h4 className="font-bold text-white mb-2">2. Scan</h4>
                <p className="text-sm text-muted">Click "Scan This Folder" to detect files. The system will identify MKV files automatically.</p>
              </div>
              <div className="p-6 rounded-xl bg-[var(--bg-tertiary)]/30 border border-[var(--border-color)]">
                <div className="text-2xl mb-2">📋</div>
                <h4 className="font-bold text-white mb-2">3. Review</h4>
                <p className="text-sm text-muted">Check the list of detected episodes. Uncheck any files you don't want to process.</p>
              </div>
              <div className="p-6 rounded-xl bg-[var(--bg-tertiary)]/30 border border-[var(--border-color)]">
                <div className="text-2xl mb-2">✨</div>
                <h4 className="font-bold text-white mb-2">4. Match</h4>
                <p className="text-sm text-muted">Start the process. The AI will listen to the audio, find the episode, and rename the file.</p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // DASHBOARD VIEW
    return (
      <div className="h-full flex flex-col gap-6">

        {/* Header / Actions */}
        <div className="flex items-center justify-between flex-shrink-0">
          <div>
            <h2 className="text-3xl font-bold heading-gradient mb-1">
              {workflowState === 'IDLE' && 'Library Scan'}
              {workflowState === 'SCANNING' && 'Scanning Directory...'}
              {workflowState === 'REVIEW' && 'Review Selection'}
              {(workflowState === 'PROCESSING' || workflowState === 'DONE') && 'Processing Media'}
            </h2>
            <p className="text-[var(--text-muted)] text-sm">
              {workflowState === 'IDLE' && 'Select a directory to begin organizing your library.'}
              {workflowState === 'SCANNING' && 'Please wait while we look for video files...'}
              {workflowState === 'REVIEW' && `Found ${scannedFiles.length} MKV files ready for analysis.`}
              {workflowState === 'PROCESSING' && 'Matching audio against reference subtitles...'}
            </p>
          </div>

          <div className="flex gap-3">
            {workflowState === 'REVIEW' && (
              <>
                <button className="btn btn-secondary" onClick={resetWorkflow}>Cancel</button>
                <button
                  className="btn btn-primary"
                  onClick={handleStartMatch}
                  disabled={scannedFiles.length === 0}
                >
                  Start Matching ✨
                </button>
              </>
            )}

            {(jobStatus?.status === 'completed' || jobStatus?.status === 'failed') && (
              <button className="btn btn-primary" onClick={resetWorkflow}>Start New Scan</button>
            )}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 min-h-0 overflow-hidden rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]/40 backdrop-blur-sm">

          {/* STEP 1: IDLE - File Browser */}
          {workflowState === 'IDLE' && (
            <div className="h-full">
              <FileBrowser onDirectorySelect={handleFolderSelect} />
            </div>
          )}

          {/* LOADING STATE - Scanning */}
          {workflowState === 'SCANNING' && (
            <div className="h-full flex flex-col items-center justify-center bg-[var(--bg-primary)]/80 backdrop-blur-md">
              <div className="w-16 h-16 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mb-6"></div>
              <h3 className="text-xl font-bold text-white mb-2">Scanning Directory</h3>
              <p className="text-[var(--text-muted)]">Analyzing file structure...</p>
            </div>
          )}

          {/* STEP 2: REVIEW - Grid */}
          {workflowState === 'REVIEW' && (
            <div className="h-full overflow-auto p-4">
              <FileReviewGrid files={scannedFiles} onRemove={handleRemoveFile} />
            </div>
          )}

          {/* STEP 3: PROCESSING - Results */}
          {(workflowState === 'PROCESSING' || workflowState === 'DONE') && (
            <div className="h-full flex flex-col overflow-hidden p-4">
              {/* Progress Status Bar */}
              <div className="flex-shrink-0 p-4 bg-[var(--bg-tertiary)]/50 rounded-xl border border-[var(--border-color)] mb-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-4">
                    <div className={`w-3 h-3 rounded-full 
                       ${jobStatus?.status === 'completed' ? 'bg-green-500' :
                        jobStatus?.status === 'processing' ? 'bg-indigo-500 animate-pulse' :
                          jobStatus?.status === 'failed' ? 'bg-red-500' : 'bg-gray-500'}
                       ring-4 ring-white/5
                     `}></div>
                    <div>
                      <div className="font-bold text-white text-sm uppercase tracking-wider">
                        {jobStatus?.status || 'INITIALIZING'}
                      </div>
                      {jobStatus?.status === 'processing' && (
                        <div className="text-sm text-[var(--text-muted)] mt-0.5">
                          {jobStatus.phase?.message || (systemStatus.model_loaded ? 'Whisper ASR Ready' : 'Loading ASR Model...')}
                        </div>
                      )}
                    </div>
                  </div>

                  {jobStatus?.results && (
                    <div className="text-right">
                      <div className="text-2xl font-bold text-white">{jobStatus.results.length}</div>
                      <div className="text-sm text-[var(--text-muted)] uppercase">Matched</div>
                    </div>
                  )}
                </div>

                {/* Full-width Progress Bar */}
                {jobStatus?.status === 'processing' && jobStatus.progress && (
                  <div className="w-full">
                    <div className="flex justify-between text-sm text-blue-300 mb-2">
                      <span className="truncate max-w-[70%]">{jobStatus.progress.filename}</span>
                      <span className="flex-shrink-0 ml-4">{Math.round((jobStatus.progress.current / jobStatus.progress.total) * 100)}%</span>
                    </div>
                    <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
                        style={{ width: `${(jobStatus.progress.current / jobStatus.progress.total) * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Results List */}
              <div className="flex-1 overflow-auto space-y-3 pr-2">
                {jobStatus?.results?.map((res, idx) => (
                  <div key={idx} className="group p-4 bg-[var(--bg-tertiary)]/30 hover:bg-[var(--bg-tertiary)]/60 rounded-xl border border-[var(--border-color)] hover:border-[var(--accent-primary)]/30 transition-all">
                    <div className="flex justify-between items-start">
                      <div className="flex items-start gap-4">
                        <div className="text-3xl opacity-50 group-hover:opacity-100 transition-opacity">🎬</div>
                        <div>
                          <div className="font-bold text-[var(--accent-secondary)] text-lg">
                            {res.series}
                          </div>
                          <div className="text-white font-medium flex items-center gap-2">
                            <span>S{res.season.toString().padStart(2, '0')}E{res.episode.toString().padStart(2, '0')}</span>
                            <span className="text-[var(--text-muted)]">•</span>
                            <span>{res.title}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col items-end">
                        <div className={`px-3 py-1 rounded-full text-xs font-bold border ${res.confidence > 0.8 ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
                          }`}>
                          {(res.confidence * 100).toFixed(0)}% MATCH
                        </div>
                        <div className="text-xs text-[var(--text-muted)] mt-2 font-mono">
                          {res.original_file.split(/[/\\]/).pop()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {jobStatus?.failures?.map((f, idx) => (
                  <div key={`fail-${idx}`} className="p-4 bg-red-500/5 rounded-xl border border-red-500/10 hover:border-red-500/30 transition-all">
                    <div className="flex items-center gap-3">
                      <span className="text-red-400 text-xl">⚠️</span>
                      <div>
                        <div className="text-red-400 font-bold">Match Failed</div>
                        <div className="text-sm text-[var(--text-muted)] mt-1 font-mono">{f}</div>
                      </div>
                    </div>
                  </div>
                ))}

                {!jobStatus?.results?.length && !jobStatus?.failures?.length && (
                  <div className="space-y-3">
                    {/* Activity Log Header */}
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider">Activity Log</h4>
                      <span className="text-xs text-[var(--text-muted)]">{activityLog.length} events</span>
                    </div>

                    {/* Activity Log Entries */}
                    <div className="bg-[var(--bg-tertiary)]/30 rounded-xl border border-[var(--border-color)] p-4 max-h-64 overflow-y-auto">
                      {activityLog.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-8 text-[var(--text-muted)] opacity-50">
                          <div className="animate-spin text-3xl mb-3">⌛</div>
                          <div className="text-sm">Waiting for processing to begin...</div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {activityLog.slice().reverse().map((entry, idx) => (
                            <div key={idx} className={`flex items-start gap-3 text-sm ${entry.type === 'success' ? 'text-green-400' :
                              entry.type === 'warning' ? 'text-yellow-400' : 'text-[var(--text-muted)]'
                              }`}>
                              <span className="text-xs opacity-60 font-mono flex-shrink-0">{entry.time}</span>
                              <span className="flex-1">{entry.message}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Current Status Indicator */}
                    {jobStatus?.phase && (
                      <div className="flex items-center gap-3 p-3 bg-indigo-500/10 rounded-lg border border-indigo-500/20">
                        <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></div>
                        <span className="text-indigo-300 text-sm font-medium">{jobStatus.phase.message}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div >
    );
  };

  return (
    <>
      {showOnboarding && (
        <OnboardingModal
          onComplete={() => setShowOnboarding(false)}
          onSkip={() => setShowOnboarding(false)}
        />
      )}
      <Layout currentView={currentView} onNavigate={setCurrentView} systemStatus={systemStatus}>
        {renderContent()}
      </Layout>
    </>
  );
}

export default App;
