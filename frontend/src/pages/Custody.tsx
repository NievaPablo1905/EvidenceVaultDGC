import { useEffect, useState } from "react";
import { listCustodyEvents, verifyCustodyChain, type CustodyEvent } from "../api";
import { Alert, Spinner, useError } from "../components";

export default function Custody() {
  const [events, setEvents] = useState<CustodyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const { error, clearError, handleError } = useError();

  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    total_events: number;
    errors: string[];
    chain_intact: boolean;
  } | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await listCustodyEvents();
        setEvents(data);
      } catch (err) {
        handleError(err);
      } finally {
        setLoading(false);
      }
    })();
  }, [handleError]);

  const handleVerify = async () => {
    setVerifying(true);
    setVerifyResult(null);
    setVerifyError(null);
    try {
      const result = await verifyCustodyChain();
      setVerifyResult(result);
    } catch (err: unknown) {
      const axErr = err as { response?: { data?: { detail?: string } } };
      setVerifyError(axErr?.response?.data?.detail ?? "Error al verificar la cadena.");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h2 className="page-title">🔗 Cadena de Custodia</h2>
        <button className="btn btn-primary" onClick={handleVerify} disabled={verifying}>
          {verifying ? "Verificando..." : "✅ Verificar Integridad"}
        </button>
      </div>

      {error && <Alert message={error} onClose={clearError} />}
      {verifyError && <Alert message={verifyError} onClose={() => setVerifyError(null)} />}

      {verifyResult && (
        <div
          className={`alert ${verifyResult.chain_intact ? "alert-success" : "alert-error"}`}
          style={{ marginBottom: "1rem" }}
        >
          <div>
            <strong>
              {verifyResult.chain_intact ? "✅ Cadena Íntegra" : "❌ Se detectaron errores"}
            </strong>
            <br />
            <span className="text-sm">
              Total eventos: {verifyResult.total_events} |{" "}
              {verifyResult.chain_intact
                ? "No se encontraron inconsistencias."
                : `${verifyResult.errors.length} error(es) detectado(s).`}
            </span>
            {verifyResult.errors.length > 0 && (
              <ul style={{ marginTop: "0.5rem", paddingLeft: "1.25rem" }}>
                {verifyResult.errors.map((e, i) => (
                  <li key={i} className="text-sm">
                    {e}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {loading ? (
        <Spinner />
      ) : events.length === 0 ? (
        <div className="card">
          <p className="empty-msg">No hay eventos de custodia registrados.</p>
        </div>
      ) : (
        <div className="card">
          <div className="card-title">Eventos ({events.length})</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Acción</th>
                  <th>Actor (rol)</th>
                  <th>Caso</th>
                  <th>Evidencia</th>
                  <th>IP Origen</th>
                  <th>Timestamp (UTC)</th>
                  <th>Hash Evento</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => (
                  <tr key={ev.id}>
                    <td>{ev.id}</td>
                    <td>
                      <span className="badge badge-info">{ev.action}</span>
                    </td>
                    <td className="text-sm">
                      #{ev.actor_id}{" "}
                      <span className="text-muted">({ev.actor_role})</span>
                    </td>
                    <td className="text-sm">{ev.case_id ?? "—"}</td>
                    <td className="text-sm">{ev.evidence_item_id ?? "—"}</td>
                    <td className="text-sm text-muted">{ev.source_ip ?? "—"}</td>
                    <td className="text-sm text-muted">
                      {new Date(ev.timestamp_utc).toLocaleString("es-AR")}
                    </td>
                    <td>
                      <span className="hash" title={ev.event_hash}>
                        {ev.event_hash.slice(0, 16)}…
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
