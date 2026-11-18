
import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

async function readApiResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail || data.message || "The request failed."
    );
  }

  return data;
}

function App() {
  const [reports, setReports] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedReport, setSelectedReport] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState("");

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [ragResult, setRagResult] = useState(null);
  const [ragError, setRagError] = useState("");

  // Load reports and analytics.
  async function loadDashboard(query = "") {
    try {
      setError("");
      setLoading(true);

      const [reportsResponse, analyticsResponse] = await Promise.all([
        fetch(`${API_URL}/reports?q=${encodeURIComponent(query)}`),
        fetch(`${API_URL}/analytics`),
      ]);

      const reportsData = await readApiResponse(reportsResponse);
      const analyticsData = await readApiResponse(analyticsResponse);

      setReports(reportsData);
      setAnalytics(analyticsData);
    } catch (err) {
      setError(
        `Cannot load dashboard: ${err.message}. Check that FastAPI is running.`
      );
    } finally {
      setLoading(false);
    }
  }

  // Load indexed documents.
  async function loadDocuments() {
    try {
      const response = await fetch(`${API_URL}/documents`);
      const data = await readApiResponse(response);

      setDocuments(data.documents || []);
      setDocumentsError("");
    } catch (err) {
      setDocumentsError(
        err.message || "Could not load documents."
      );
    } finally {
      setDocumentsLoading(false);
    }
  }

  // Refresh documents manually.
  async function refreshDocuments() {
    setDocumentsLoading(true);
    setDocumentsError("");
    await loadDocuments();
  }

  // Initial document loading.
  // State updates happen after the asynchronous API request.
  useEffect(() => {
    let cancelled = false;

    async function fetchDocuments() {
      try {
        const response = await fetch(`${API_URL}/documents`);
        const data = await readApiResponse(response);

        if (!cancelled) {
          setDocuments(data.documents || []);
          setDocumentsError("");
        }
      } catch (err) {
        if (!cancelled) {
          setDocumentsError(
            err.message || "Could not load documents."
          );
        }
      } finally {
        if (!cancelled) {
          setDocumentsLoading(false);
        }
      }
    }

    fetchDocuments();

    return () => {
      cancelled = true;
    };
  }, []);

  // Search reports with a small delay.
  useEffect(() => {
    const timer = setTimeout(() => {
      loadDashboard(search);
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  // Analyse a selected report.
  async function analyzeReport(report) {
    try {
      setSelectedReport(report);
      setAnalysis(null);
      setAnalyzing(true);

      const response = await fetch(
        `${API_URL}/analyze/${report.id}`,
        { method: "POST" }
      );

      const data = await readApiResponse(response);
      setAnalysis(data);
    } catch (err) {
      setAnalysis({
        limitations: `Unable to run the analysis: ${err.message}`,
      });
    } finally {
      setAnalyzing(false);
    }
  }

  // Upload PDF or TXT documents.
  async function handleUpload(event) {
    event.preventDefault();

    if (!selectedFile) {
      setUploadError("Please select a PDF or TXT file.");
      return;
    }

    if (!/\.(pdf|txt)$/i.test(selectedFile.name)) {
      setUploadError("Only PDF and TXT files are supported.");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setUploadError("File size must not exceed 10 MB.");
      return;
    }

    try {
      setUploading(true);
      setUploadError("");
      setUploadResult(null);

      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(
        `${API_URL}/documents/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await readApiResponse(response);

      setUploadResult(data);
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setDocumentsLoading(true);
      await loadDocuments();
    } catch (err) {
      setUploadError(err.message || "Document upload failed.");
    } finally {
      setUploading(false);
    }
  }

  // Ask a question using local RAG.
  async function handleAsk(event) {
    event.preventDefault();

    if (!question.trim()) {
      setRagError("Please enter a question.");
      return;
    }

    try {
      setAsking(true);
      setRagError("");
      setRagResult(null);

      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
      });

      const data = await readApiResponse(response);
      setRagResult(data);
    } catch (err) {
      setRagError(err.message || "Unable to get an answer.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">DI</div>
          <div>
            <h2>DEFENCE INTEL</h2>
            <span>THREAT ANALYSIS PLATFORM</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">▦ &nbsp; Overview</div>
        <div className="nav-item">◉ &nbsp; Intelligence Reports</div>
        <div className="nav-item">▤ &nbsp; Analytics</div>
        <div className="nav-item">▧ &nbsp; Document Library</div>
        <div className="nav-item">✧ &nbsp; AI Assistant</div>

        <div className="sidebar-footer">
          <span className="status-dot" />
          Backend connection
          <strong>Local API</strong>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="breadcrumb">Workspace / Overview</div>
            <h1>Intelligence Dashboard</h1>
            <p>
              Review reports, process documents and ask questions using
              local AI.
            </p>
          </div>

          <div className="demo-badge">PROTOTYPE ENVIRONMENT</div>
        </header>

        <section className="notice">
          <strong>Prototype data notice</strong>
          <span>
            Dashboard reports are synthetic examples. Uploaded documents
            are processed locally for research and demonstration
            purposes. Automated risk scores are preliminary rule-based
            indicators, not validated threat assessments.
          </span>
        </section>

        {/* Dashboard statistics */}
        <section className="stats">
          <div className="stat-card">
            <div className="stat-top">
              <span>Total Reports</span>
              <span className="stat-icon blue">▤</span>
            </div>
            <strong>{analytics?.total_reports ?? "—"}</strong>
            <small>Reports matching all categories</small>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span>High Priority</span>
              <span className="stat-icon red">!</span>
            </div>
            <strong>{analytics?.high_priority ?? "—"}</strong>
            <small>Demo reports marked high</small>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span>Medium Priority</span>
              <span className="stat-icon amber">◈</span>
            </div>
            <strong>{analytics?.medium_priority ?? "—"}</strong>
            <small>Demo reports marked medium</small>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span>Low Priority</span>
              <span className="stat-icon green">✓</span>
            </div>
            <strong>{analytics?.low_priority ?? "—"}</strong>
            <small>Demo reports marked low</small>
          </div>
        </section>

        {/* Document upload and library */}
        <section className="workspace-grid">
          <div className="tool-panel">
            <div className="panel-heading">
              <div>
                <h2>Document Ingestion</h2>
                <p>Upload PDF or TXT intelligence documents.</p>
              </div>
              <span className="tool-icon">↑</span>
            </div>

            <form onSubmit={handleUpload} className="upload-form">
              <label htmlFor="document-file">
                Select document
              </label>

              <input
                ref={fileInputRef}
                id="document-file"
                type="file"
                accept=".pdf,.txt,application/pdf,text/plain"
                onChange={(event) => {
                  setSelectedFile(event.target.files?.[0] || null);
                  setUploadError("");
                  setUploadResult(null);
                }}
              />

              <small className="form-hint">
                PDF or TXT · Maximum size 10 MB
              </small>

              {selectedFile && (
                <p className="selected-file">
                  Selected: {selectedFile.name}
                </p>
              )}

              {uploadError && (
                <div className="error">{uploadError}</div>
              )}

              <button
                type="submit"
                className="primary-button"
                disabled={uploading || !selectedFile}
              >
                {uploading
                  ? "Processing document..."
                  : "Upload and Process"}
              </button>
            </form>

            {uploadResult && (
              <div className="success-panel">
                <strong>Document processed successfully</strong>
                <p>{uploadResult.filename}</p>
                <p>
                  Pages: {uploadResult.page_count} · Chunks stored:{" "}
                  {uploadResult.chunks_stored}
                </p>

                {uploadResult.threat_assessment && (
                  <p>
                    Preliminary priority:{" "}
                    {uploadResult.threat_assessment.priority} · Score:{" "}
                    {uploadResult.threat_assessment.risk_score}/100
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="tool-panel">
            <div className="panel-heading">
              <div>
                <h2>Document Library</h2>
                <p>
                  Documents indexed in the local vector database.
                </p>
              </div>

              <button
                type="button"
                className="secondary-button"
                onClick={refreshDocuments}
                disabled={documentsLoading}
              >
                Refresh
              </button>
            </div>

            {documentsError && (
              <div className="error">{documentsError}</div>
            )}

            {documentsLoading ? (
              <p className="message">Loading documents...</p>
            ) : documents.length === 0 ? (
              <p className="message">
                No documents found. Upload a PDF or TXT file to begin.
              </p>
            ) : (
              <div className="document-list">
                {documents.map((document, index) => (
                  <div
                    className="document-item"
                    key={
                      document.document_id ||
                      `${document.filename}-${index}`
                    }
                  >
                    <div className="document-symbol">▤</div>

                    <div className="document-details">
                      <strong>{document.filename}</strong>
                      <small>
                        {document.chunks_stored ?? 0} chunks indexed
                      </small>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="library-count">
              {documents.length} document record(s) listed
            </div>
          </div>
        </section>

        {/* RAG question-answering */}
        <section className="tool-panel qa-panel">
          <div className="panel-heading">
            <div>
              <h2>Intelligence AI Assistant</h2>
              <p>
                Ask questions about documents in the vector database.
              </p>
            </div>
            <span className="tool-icon">✧</span>
          </div>

          <form onSubmit={handleAsk} className="question-form">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Example: What military activities were reported near the northern border zone?"
              rows={3}
            />

            <button
              type="submit"
              className="primary-button"
              disabled={asking || !question.trim()}
            >
              {asking
                ? "Searching documents and generating answer..."
                : "Ask AI"}
            </button>
          </form>

          {ragError && <div className="error">{ragError}</div>}

          {ragResult && (
            <div className="answer-panel">
              <h3>Generated Answer</h3>
              <p className="answer-text">{ragResult.answer}</p>

              <div className="source-heading">
                Source References ({ragResult.sources?.length ?? 0})
              </div>

              {ragResult.sources?.length > 0 ? (
                <div className="source-list">
                  {ragResult.sources.map((source, index) => (
                    <div
                      className="source-item"
                      key={`${source.filename}-${source.chunk_index}-${index}`}
                    >
                      <strong>{source.filename}</strong>
                      <small>
                        Page {source.page ?? "N/A"} ·{" "}
                        {source.category ?? "General"} ·{" "}
                        {source.date || "Date unavailable"} · Chunk{" "}
                        {source.chunk_index}
                      </small>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="message">
                  No source references were returned.
                </p>
              )}
            </div>
          )}
        </section>

        {/* Intelligence reports */}
        <section className="reports-section">
          <div className="section-heading">
            <div>
              <h2>Intelligence Reports</h2>
              <p>
                Search and inspect available demonstration records.
              </p>
            </div>

            <span className="report-count">
              {reports.length} results
            </span>
          </div>

          <div className="search-box">
            <span>⌕</span>
            <input
              type="search"
              placeholder="Search by title, category, location..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          {error && <div className="error">{error}</div>}

          {loading ? (
            <p className="message">Loading reports...</p>
          ) : reports.length === 0 ? (
            <p className="message">
              No reports match your search.
            </p>
          ) : (
            <div className="report-list">
              {reports.map((report) => (
                <article className="report-card" key={report.id}>
                  <div className="report-symbol">▤</div>

                  <div className="report-content">
                    <div className="report-meta">
                      <span>{report.category}</span>
                      <span>•</span>
                      <span>{report.location}</span>
                    </div>

                    <h3>{report.title}</h3>
                    <p>{report.summary}</p>
                    <small>Source: {report.source}</small>
                  </div>

                  <div className="report-actions">
                    <span
                      className={`priority ${String(
                        report.priority || "low"
                      ).toLowerCase()}`}
                    >
                      {report.priority}
                    </span>

                    <button
                      onClick={() => analyzeReport(report)}
                    >
                      Analyse
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        {/* Report analysis */}
        {selectedReport && (
          <section className="analysis-panel">
            <button
              className="close-button"
              onClick={() => {
                setSelectedReport(null);
                setAnalysis(null);
              }}
            >
              Close ×
            </button>

            <h2>Demonstration Analysis</h2>
            <h3>{selectedReport.title}</h3>

            {analyzing ? (
              <p>Running demonstration analysis...</p>
            ) : analysis ? (
              <div className="analysis-results">
                <p>
                  <strong>Priority:</strong>{" "}
                  {analysis.priority ?? selectedReport.priority}
                </p>

                <p>
                  <strong>Risk Score:</strong>{" "}
                  {analysis.risk_score ?? "Unavailable"}/100
                </p>

                <p>
                  <strong>Matched Keywords:</strong>{" "}
                  {analysis.matched_keywords?.length
                    ? analysis.matched_keywords.join(", ")
                    : "None"}
                </p>

                <p>
                  <strong>Reasoning:</strong>{" "}
                  {analysis.reasoning ?? "Unavailable"}
                </p>

                <p>
                  <strong>Method:</strong>{" "}
                  {analysis.method ?? "Unavailable"}
                </p>

                <p className="analysis-limit">
                  {analysis.limitations}
                </p>
              </div>
            ) : null}
          </section>
        )}

        <footer>
          Defence Intelligence & Threat Analysis Platform
          <span>Local AI Prototype v0.1.0</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
