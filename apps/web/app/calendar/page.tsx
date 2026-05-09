import { redirect } from "next/navigation";

import { AppShell } from "@/components/shell/AppShell";
import { ComingSoon } from "@/components/shell/ComingSoon";
import { readDevSession } from "@/lib/session";

export default function CalendarPage(): React.ReactElement {
  const session = readDevSession();
  if (!session) redirect("/login");
  return (
    <AppShell userName={null} tenantName={null} role={null}>
      <ComingSoon
        title="Calendar"
        sprint="Sprint 4"
        description="Month view of due dates and hearings arrives in Sprint 4."
      />
    </AppShell>
  );
}
