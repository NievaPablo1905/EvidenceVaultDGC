import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCases, createCase, type Case } from "../api";
import { Alert, Spinner, Modal, useError } from "../components";

export default function Cases() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const { error, clearError, handleError } = useError();

  // Create form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [legalBasis, setLegalBasis] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchCases = async () => {
    try {
      const data = await listCases();
      setCases(data);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreating(true);
    try {
      await createCase({ title, description: description || undefined, legal_basis: legalBasis || undefined });
      setShowModal(false);
      setTitle("");
      setDescription("");
      setLegalBasis("");
      setLoading(true);
      await fetchCases();
    } catch (err: unknown) {
      const axErr = err as { response?: { data?: { detail?: string } } };
      setCreateError(axErr?.response?.data?.detail ?? "Error al crear el caso.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h2 className="page-title">📁 Casos</h2>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Nuevo Caso
        </button>
      </div>

      {error && <Alert message={error} onClose={clearError} />}

      {loading ? (
        <Spinner />
      ) : cases.length === 0 ? (
        <div className="card">
          <p className="empty-msg">No hay casos registrados. Cree el primero.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Título</th>
                  <th>Base Legal</th>
                  <th>Creado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td>
                      <Link to={`/cases/${c.id}`}>{c.title}</Link>
                    </td>
                    <td className="text-muted">{c.legal_basis ?? "—"}</td>
                    <td className="text-muted text-sm">
                      {new Date(c.created_at).toLocaleString("es-AR")}
                    </td>
                    <td>
                      <Link to={`/cases/${c.id}`} className="btn btn-secondary btn-sm">
                        Ver
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && (
        <Modal title="Nuevo Caso" onClose={() => setShowModal(false)}>
          {createError && <Alert message={createError} onClose={() => setCreateError(null)} />}
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label className="form-label">Título *</label>
              <input
                className="form-control"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                placeholder="Ej: Caso 2026-001"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Descripción</label>
              <textarea
                className="form-control"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Descripción del caso..."
              />
            </div>
            <div className="form-group">
              <label className="form-label">Base Legal</label>
              <input
                className="form-control"
                value={legalBasis}
                onChange={(e) => setLegalBasis(e.target.value)}
                placeholder="Ej: Ley 27411 / Art. 309 sexies CPPN"
              />
            </div>
            <div className="gap-row mt-2">
              <button type="submit" className="btn btn-primary" disabled={creating}>
                {creating ? "Creando..." : "Crear Caso"}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancelar
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
