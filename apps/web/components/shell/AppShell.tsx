import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppShellProps {
  userName: string | null;
  tenantName: string | null;
  role: string | null;
  children: React.ReactNode;
}

export function AppShell({
  userName,
  tenantName,
  role,
  children,
}: AppShellProps): React.ReactElement {
  return (
    <div className="flex min-h-screen bg-cream">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Topbar userName={userName} tenantName={tenantName} role={role} />
        <main className="flex-1 px-6 py-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
