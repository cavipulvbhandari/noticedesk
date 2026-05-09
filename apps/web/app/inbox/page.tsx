import { redirect } from "next/navigation";

import { AppShell } from "@/components/shell/AppShell";
import { ComingSoon } from "@/components/shell/ComingSoon";
import { readDevSession } from "@/lib/session";

export default function InboxPage(): React.ReactElement {
  const session = readDevSession();
  if (!session) redirect("/login");
  return (
    <AppShell userName={null} tenantName={null} role={null}>
      <ComingSoon
        title="Inbox"
        sprint="Sprint 2"
        description="Document upload, OCR pipeline, and email forwarding land here in Sprint 2. Notice routing decisions surface in Sprint 3."
      />
    </AppShell>
  );
}
