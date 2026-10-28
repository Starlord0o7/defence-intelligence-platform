
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [reports, setReports] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedReport, setSelectedReport] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  async function loadDashboard(query = "") {
    try {
      setError("");
      setLoading(true);

      const reportsResponse = await fetch(
        `${API_URL}/reports?q=${encodeURIComponent(query)}`
      );

      const analyticsResponse = await fetch(`${API_URL}/analytics`);

      if (!reportsResponse.ok || !analyticsResponse.ok) {
        throw new Error("The backend returned an error.");
      }

      const reportsData = await reportsResponse.json();
      const analyticsData = await analyticsResponse.json();

      setReports(reportsData);
      setAnalytics(analyticsData);
    } catch (err) {
      setError(
        "Cannot connect to the backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadDashboard(search);
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  async function analyzeReport(report) {
    try {
      setSelectedReport(report);
      setAnalysis(null);
      setAnalyzing(true);

      const response = await fetch(
        `${API_URL}/analyze/${report.id}`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error("Analysis request failed.");
      }

      setAnalysis(await response.json());
    } catch {
      setAnalysis({
        limitations: "Unable to run the demonstration analysis. Check the backend."
      });
    } finally {
      setAnalyzing(false);
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

        <div className="sidebar-footer">
          <span className="status-dot" />
          Backend connection
          <strong>Local demo</strong>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="breadcrumb">Workspace / Overview</div>
            <h1>Intelligence Dashboard</h1>
            <p>Monitor and review demonstration reports in one place.</p>
          </div>
          <div className="demo-badge">DEMO ENVIRONMENT</div>
        </header>

        <section className="notice">
          <strong>Demonstration data</strong>
          <span>
            All current reports are synthetic examples, not real intelligence
            or validated threat assessments.
          </span>
        </section>

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

        <section className="reports-section">
          <div className="section-heading">
            <div>
              <h2>Intelligence Reports</h2>
              <p>Search and inspect available demonstration records.</p>
            </div>
            <span className="report-count">{reports.length} results</span>
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
            <p className="message">No reports match your search.</p>
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
                      className={`priority ${report.priority.toLowerCase()}`}
                    >
                      {report.priority}
                    </span>
                    <button onClick={() => analyzeReport(report)}>
                      Analyse
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

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
              <>
                <p>
                  <strong>Priority:</strong>{" "}
                  {analysis.priority ?? selectedReport.priority}
                </p>
                <p>
                  <strong>Method:</strong>{" "}
                  {analysis.method ?? "Unavailable"}
                </p>
                <p className="analysis-limit">
                  {analysis.limitations}
                </p>
              </>
            ) : null}
          </section>
        )}

        <footer>
          Defence Intelligence & Threat Analysis Platform
          <span>Prototype v0.1.0</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
