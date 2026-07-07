export default function ProtectedTemplate({ children }: { children: React.ReactNode }) {
  return <div className="page-enter">{children}</div>
}
