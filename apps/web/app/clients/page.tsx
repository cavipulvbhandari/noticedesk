import { redirect } from "next/navigation";

import { AppShell } from "@/components/shell/AppShell";
import { ComingSoon } from "@/components/shell/ComingSoon";
import { readDevSession } from "@/lib/session";

export default function ClientsPage(): React.ReactElement {
  const session = readDevSession();
  if (!session) redirect("/login");
  return (
    <AppShell userName={null} tenantName={null} role={null}>
      <ComingSoon
        title="Clients"
        sprint="Sprint 4"
        description="Client list, two-card detail view, and PAN/GSTIN-validated entry land in Sprint 4."
      />
    </AppShell>
  );
}
