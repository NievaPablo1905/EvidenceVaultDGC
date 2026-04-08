import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { API_BASE } from "./api";

export default function Layout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <div className="layout">
      <nav className="navbar">
        <NavLink to="/cases" className="navbar-brand">
          🔒 Evidence Vault DGC
        </NavLink>
        <NavLink to="/cases" className={({ isActive }) => (isActive ? "active" : "")}>
          Casos
        </NavLink>
        <NavLink to="/custody" className={({ isActive }) => (isActive ? "active" : "")}>
          Custodia
        </NavLink>
        <div className="navbar-right">
          <span className="api-badge">API: {API_BASE}</span>
          <button className="btn btn-danger btn-sm" onClick={handleLogout}>
            Salir
          </button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
