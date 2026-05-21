import type { ReactNode } from "react";
import { RefreshCcw, Trash2 } from "lucide-react";

export function Metric({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}

export function Section({
  title,
  actions,
  children,
}: {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="section">
      <div className="section-header">
        <h2>{title}</h2>
        <div className="section-actions">{actions}</div>
      </div>
      {children}
    </section>
  );
}

export function RefreshButton({ onClick, loading }: { onClick: () => void; loading?: boolean }) {
  return (
    <button className="icon-button" onClick={onClick} disabled={loading} title="刷新">
      <RefreshCcw size={16} />
    </button>
  );
}

export function ActionButton({
  children,
  onClick,
  disabled,
  title,
  variant = "default",
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  title?: string;
  variant?: "default" | "danger";
}) {
  return (
    <button className={variant === "danger" ? "button-danger" : ""} onClick={onClick} disabled={disabled} title={title}>
      {children}
    </button>
  );
}

export function ConfirmButton({
  onConfirm,
  disabled,
  message = "确认删除这条研究侧记录？",
}: {
  onConfirm: () => void;
  disabled?: boolean;
  message?: string;
}) {
  return (
    <button
      className="icon-button button-danger"
      onClick={() => {
        if (window.confirm(message)) onConfirm();
      }}
      disabled={disabled}
      title="删除"
    >
      <Trash2 size={15} />
    </button>
  );
}

export function Modal({
  title,
  open,
  onClose,
  children,
}: {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-panel">
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="icon-button" onClick={onClose} title="关闭">
            x
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export function FormRow({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="form-row">
      <span>{label}</span>
      {children}
    </label>
  );
}

export function InlineAlert({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "error" | "success" }) {
  return <div className={`inline-alert inline-alert-${tone}`}>{children}</div>;
}

export function RowActions({ children }: { children: ReactNode }) {
  return <div className="row-actions">{children}</div>;
}

export function StatusPill({ value }: { value?: string | null }) {
  const normalized = (value ?? "unknown").toLowerCase();
  return <span className={`status status-${normalized}`}>{value ?? "unknown"}</span>;
}

export function DataTable<T extends Record<string, unknown>>({
  rows,
  columns,
  empty = "暂无数据",
}: {
  rows: T[];
  columns: Array<{ key: keyof T | string; label: string; render?: (row: T) => ReactNode }>;
  empty?: string;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={String(column.key)}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty-cell">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={String(column.key)}>{column.render ? column.render(row) : formatCell(row[column.key])}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: unknown): ReactNode {
  if (value === null || value === undefined || value === "") return <span className="muted">-</span>;
  if (typeof value === "object") return <code>{JSON.stringify(value)}</code>;
  return String(value);
}

export function StateBlock({ loading, error }: { loading: boolean; error: string | null }) {
  if (loading) return <div className="state">加载中</div>;
  if (error) return <div className="state state-error">{error}</div>;
  return null;
}
