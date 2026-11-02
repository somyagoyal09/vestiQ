import { useState } from "react";

const MAX_PASSWORD_BYTES = 72;
const encoder = new TextEncoder();

export default function SetPassword({ apiUrl, token }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState({ type: "", text: "" });

  const submit = async (event) => {
    event.preventDefault();

    if (newPassword.length < 8) {
      setStatus({ type: "error", text: "Password must be at least 8 characters." });
      return;
    }
    if (encoder.encode(newPassword).length > MAX_PASSWORD_BYTES) {
      setStatus({ type: "error", text: "New password must be 72 bytes or fewer." });
      return;
    }
    if (currentPassword && encoder.encode(currentPassword).length > MAX_PASSWORD_BYTES) {
      setStatus({ type: "error", text: "Current password must be 72 bytes or fewer." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setStatus({ type: "error", text: "Passwords do not match." });
      return;
    }

    setBusy(true);
    setStatus({ type: "", text: "" });
    try {
      const response = await fetch(`${apiUrl}/auth/set-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          new_password: newPassword,
          current_password: currentPassword || null,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setStatus({
          type: "error",
          text: typeof data.detail === "string" ? data.detail : "Unable to save password.",
        });
        return;
      }
      setStatus({ type: "success", text: data.message || "Password saved." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      console.error("Set password error:", error);
      setStatus({ type: "error", text: "Unable to connect to backend." });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card border-0 shadow-sm mt-3">
      <div className="card-body">
        <h5 className="fw-bold">Email & password login</h5>
        <p className="text-muted small mb-3">
          Set a password to log in with your email as well as Google. If you already have a password, enter it first.
        </p>
        <form onSubmit={submit}>
          <input
            type="password"
            className="form-control mb-2"
            placeholder="Current password (only if you already have one)"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            autoComplete="current-password"
          />
          <input
            type="password"
            className="form-control mb-2"
            placeholder="New password (8 to 72 bytes)"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
          />
          <input
            type="password"
            className="form-control mb-3"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
          />
          <button type="submit" className="btn btn-dark" disabled={busy}>
            {busy ? "Saving..." : "Save password"}
          </button>
        </form>
        {status.text && (
          <div className={`small mt-3 ${status.type === "error" ? "text-danger" : "text-success"}`}>
            {status.text}
          </div>
        )}
      </div>
    </div>
  );
}