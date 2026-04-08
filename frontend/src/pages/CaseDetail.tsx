import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getCase,
  listEvidence,
  uploadEvidence,
  downloadEvidenceUrl,
  type Case,
  type EvidenceItem,
} from "../api";
import { Alert, Spinner, Modal, useError } from "../components";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function downloadWithAuth(url: string, filename: string) {
  const token = localStorage.getItem("token") ?? "";
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`Error al descargar: ${response.statusText}`);
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(objectUrl);
}

export default function CaseDetail() {
  const { caseId } = useParams<{ caseId: string }>();
  const id = Number(caseId);

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { error, clearError, handleError } = useError();

  const [showUpload, setShowUpload] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [srcDesc, setSrcDesc] = useState("");
  const [toolName, setToolName] = useState("");
  const [toolVer, setToolVer] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [selectedItem, setSelectedItem] = useState<EvidenceItem | null>(null);
  const [downloading, setDownloading] = useState<number | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [c, ev] = await Promise.all([getCase(id), listEvidence(id)]);
      setCaseData(c);
      setEvidence(ev);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      await uploadEvidence(id, file, srcDesc, toolName, toolVer);
      setShowUpload(false);
      setFile(null);
      setSrcDesc("");
      setToolName("");
      setToolVer("");
      setLoading(true);
      await fetchData();
    } catch (err: unknown) {
      const axErr = err as { response?: { data?: { detail?: string } } };
      setUploadError(axErr?.response?.data?.detail ?? "Error al subir el archivo.");
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (item: EvidenceItem) => {
    setDownloadError(null);
    setDownloading(item.id);
    try {
      await downloadWithAuth(downloadEvidenceUrl(id, item.id), item.original_filename);
    } catch (err: unknown) {
      setDownloadError(err instanceof Error ? err.message : "Error al descargar.");
    } finally {
      setDownloading(null);
    }
  };

  if (loading) return <Spinner />;

  return (
    <>
      <div className="page-header">
        <div>
          <Link to="/cases" className="text-muted text-sm">
            ← Volver a Casos
          </Link>
          <h2 className="page-title mt-1">{caseData?.title}</h2>
          {caseData?.legal_basis && (
            <p className="text-muted text-sm">{caseData.legal_basis}</p>
          )}
          {caseData?.description && (
            <p className="text-sm mt-1">{caseData.description}</p>
          )}
        </div>
        <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
          ↑ Subir Evidencia
        </button>
      </div>

      {error && <Alert message={error} onClose={clearError} />}
      {downloadError && <Alert message={downloadError} onClose={() => setDownloadError(null)} />}

      <div className="card">
        <div className="card-title">Evidencias ({evidence.length})</div>
        {evidence.length === 0 ? (
          <p className="empty-msg">No hay evidencias. Suba la primera.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Archivo</th>
                  <th>Tamaño</th>
                  <th>Fuente</th>
                  <th>Herramienta</th>
                  <th>Ingresado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {evidence.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelectedItem(item)}
                        style={{ textAlign: "left" }}
                      >
                        {item.original_filename}
                      </button>
                    </td>
                    <td className="text-sm">{formatBytes(item.size_bytes)}</td>
                    <td className="text-sm text-muted">{item.source_description ?? "—"}</td>
                    <td className="text-sm text-muted">
                      {item.tool_name
                        ? `${item.tool_name}${item.tool_version ? ` v${item.tool_version}` : ""}`
                        : "—"}
                    </td>
                    <td className="text-sm text-muted">
                      {new Date(item.acquired_at).toLocaleString("es-AR")}
                    </td>
                    <td>
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() => handleDownload(item)}
                        disabled={downloading === item.id}
                      >
                        {downloading === item.id ? "..." : "↓ Descargar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <Modal title="Subir Evidencia" onClose={() => setShowUpload(false)}>
          {uploadError && <Alert message={uploadError} onClose={() => setUploadError(null)} />}
          <form onSubmit={handleUpload}>
            <div className="form-group">
              <label className="form-label">Archivo *</label>
              <input
                className="form-control"
                type="file"
                required
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <p className="text-muted text-sm mt-1">
                Soportado: pdf, zip, pcap, jpg, png, log, txt y cualquier otro tipo.
              </p>
            </div>
            <div className="form-group">
              <label className="form-label">Descripción / Fuente</label>
              <input
                className="form-control"
                value={srcDesc}
                onChange={(e) => setSrcDesc(e.target.value)}
                placeholder="Ej: Captura de red — dispositivo ID-001"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Herramienta</label>
              <input
                className="form-control"
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
                placeholder="Ej: tcpdump, Cellebrite, FTK..."
              />
            </div>
            <div className="form-group">
              <label className="form-label">Versión Herramienta</label>
              <input
                className="form-control"
                value={toolVer}
                onChange={(e) => setToolVer(e.target.value)}
                placeholder="Ej: 4.99.1"
              />
            </div>
            <div className="gap-row mt-2">
              <button type="submit" className="btn btn-primary" disabled={uploading || !file}>
                {uploading ? "Subiendo..." : "Subir Evidencia"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowUpload(false)}
              >
                Cancelar
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Evidence Detail Modal */}
      {selectedItem && (
        <Modal
          title={`Detalle: ${selectedItem.original_filename}`}
          onClose={() => setSelectedItem(null)}
        >
          <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.5rem 1rem" }}>
            <dt className="bold text-sm">ID:</dt>
            <dd className="text-sm">{selectedItem.id}</dd>
            <dt className="bold text-sm">Caso:</dt>
            <dd className="text-sm">{selectedItem.case_id}</dd>
            <dt className="bold text-sm">Archivo:</dt>
            <dd className="text-sm">{selectedItem.original_filename}</dd>
            <dt className="bold text-sm">Tipo MIME:</dt>
            <dd className="text-sm">{selectedItem.mime_type ?? "—"}</dd>
            <dt className="bold text-sm">Tamaño:</dt>
            <dd className="text-sm">{formatBytes(selectedItem.size_bytes)}</dd>
            <dt className="bold text-sm">SHA-256:</dt>
            <dd>
              <span className="hash">{selectedItem.sha256}</span>
            </dd>
            <dt className="bold text-sm">Fuente:</dt>
            <dd className="text-sm">{selectedItem.source_description ?? "—"}</dd>
            <dt className="bold text-sm">Herramienta:</dt>
            <dd className="text-sm">
              {selectedItem.tool_name
                ? `${selectedItem.tool_name}${selectedItem.tool_version ? ` v${selectedItem.tool_version}` : ""}`
                : "—"}
            </dd>
            <dt className="bold text-sm">Ingresado:</dt>
            <dd className="text-sm">
              {new Date(selectedItem.acquired_at).toLocaleString("es-AR")}
            </dd>
          </dl>
          <div className="mt-2">
            <button
              className="btn btn-success"
              onClick={() => handleDownload(selectedItem)}
              disabled={downloading === selectedItem.id}
            >
              {downloading === selectedItem.id ? "Descargando..." : "↓ Descargar Evidencia"}
            </button>
          </div>
          <p className="text-muted text-sm mt-2">
            Verifique integridad comparando el SHA-256 arriba con el hash local del archivo.
          </p>
        </Modal>
      )}
    </>
  );
}
