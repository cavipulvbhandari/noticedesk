import { redirect } from "next/navigation";

import { AppShell } from "@/components/shell/AppShell";
import { ComingSoon } from "@/components/shell/ComingSoon";
import { readDevSession } from "@/lib/session";

export default function SettingsPage(): React.ReactElement {
  const session = readDevSession();
  if (!session) redirect("/login");
  return (
    <AppShell userName={null} tenantName={null} role={null}>
      <ComingSoon
        title="Settings"
        sprint="Sprint 4"
        description="Profile, firm, users, portal connectors, audit trail, DPDP, billing, and API tokens arrive in Sprint 4."
      />
    </AppShell>
  );
}
