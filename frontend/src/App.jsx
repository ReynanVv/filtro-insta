import React, { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const statusCopy = {
  ALLOW: {
    title: "Conteúdo aprovado",
    body: "A análise automática não encontrou evidência suficiente para bloquear a publicação.",
  },
  REVIEW: {
    title: "Revisão necessária",
    body: "O conteúdo está próximo do limite da política e deve passar por uma segunda análise.",
  },
  BLOCK: {
    title: "Publicação bloqueada",
    body: "A análise detectou conteúdo explícito com confiança suficiente para impedir a publicação.",
  },
};

function App() {
  const [file, setFile] = useState(null);
  const [caption, setCaption] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const isVideo = useMemo(() => file?.type?.startsWith("video/"), [file]);

  async function analyzeAndPublish() {
    if (!file || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const form = new FormData();
      form.append("file", file);

      const response = await fetch(`${API_URL}/api/moderate`, {
        method: "POST",
        body: form,
      });

      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || "Não foi possível analisar o arquivo.");
      }

      setResult(body);
    } catch (err) {
      setError(err.message || "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setCaption("");
    setResult(null);
    setError("");
  }

  return (
    <main className="app-shell">
      <section className="phone-frame">
        <header className="topbar">
          <button className="ghost-button" onClick={reset} aria-label="Limpar">
            ×
          </button>
          <strong>Nova publicação</strong>
          <button
            className="share-button"
            disabled={!file || loading}
            onClick={analyzeAndPublish}
          >
            {loading ? "Analisando…" : "Compartilhar"}
          </button>
        </header>

        <div className="composer">
          <label className={`media-picker ${previewUrl ? "has-media" : ""}`}>
            {previewUrl ? (
              isVideo ? (
                <video src={previewUrl} controls playsInline />
              ) : (
                <img src={previewUrl} alt="Prévia da publicação" />
              )
            ) : (
              <div className="empty-state">
                <span className="camera-icon">＋</span>
                <strong>Selecionar foto ou vídeo</strong>
                <small>O arquivo será analisado antes da publicação.</small>
              </div>
            )}
            <input
              type="file"
              accept="image/*,video/*"
              onChange={(event) => {
                setFile(event.target.files?.[0] || null);
                setResult(null);
                setError("");
              }}
            />
          </label>

          <div className="caption-row">
            <div className="avatar">R</div>
            <textarea
              value={caption}
              onChange={(event) => setCaption(event.target.value)}
              placeholder="Escreva uma legenda…"
              rows={3}
            />
          </div>
        </div>

        <div className="privacy-note">
          <span>🛡️</span>
          <div>
            <strong>Filtro pré-publicação</strong>
            <p>
              Neste MVP, o conteúdo é enviado somente para a API local de moderação.
            </p>
          </div>
        </div>

        {error && <div className="alert error">{error}</div>}

        {result && (
          <section className={`result-card ${result.decision.toLowerCase()}`}>
            <div className="result-heading">
              <span className="status-dot" />
              <div>
                <strong>{statusCopy[result.decision]?.title || result.decision}</strong>
                <p>{statusCopy[result.decision]?.body}</p>
              </div>
            </div>

            <dl>
              <div>
                <dt>Confiança</dt>
                <dd>{Math.round((result.score || 0) * 100)}%</dd>
              </div>
              <div>
                <dt>Frames analisados</dt>
                <dd>{result.sampled_frames}</dd>
              </div>
              <div>
                <dt>Tempo</dt>
                <dd>{result.processing_ms} ms</dd>
              </div>
            </dl>

            {result.reasons?.length > 0 && (
              <div className="reasons">
                <small>Motivos principais</small>
                {result.reasons.map((reason) => (
                  <code key={reason}>{reason}</code>
                ))}
              </div>
            )}
          </section>
        )}
      </section>
    </main>
  );
}

export default App;
