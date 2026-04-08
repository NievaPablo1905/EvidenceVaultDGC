import React, { useState } from "react";
import "./styles.css";

interface Props {
  message: string;
  type?: "error" | "success" | "info";
  onClose?: () => void;
}

export function Alert({ message, type = "error", onClose }: Props) {
  return (
    <div className={`alert alert-${type}`}>
      <span>{message}</span>
      {onClose && (
        <button className="alert-close" onClick={onClose}>
          ×
        </button>
      )}
    </div>
  );
}

interface SpinnerProps {
  text?: string;
}

export function Spinner({ text = "Cargando..." }: SpinnerProps) {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
      <span>{text}</span>
    </div>
  );
}

interface ModalProps {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}

export function Modal({ title, children, onClose }: ModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export function useError() {
  const [error, setError] = useState<string | null>(null);
  const clearError = () => setError(null);
  const handleError = (err: unknown) => {
    if (err instanceof Error) {
      const axErr = err as { response?: { data?: { detail?: string } } };
      setError(axErr.response?.data?.detail ?? err.message);
    } else {
      setError(String(err));
    }
  };
  return { error, clearError, handleError };
}
