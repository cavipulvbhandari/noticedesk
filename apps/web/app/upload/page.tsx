import { redirect } from "next/navigation";

import { AppShell } from "@/components/shell/AppShell";
import { ComingSoon } from "@/components/shell/ComingSoon";
import { readDevSession } from "@/lib/session";

export default function UploadPage(): React.ReactElement {
  const session = readDevSession();
  if (!session) redirect("/login");
  return (
    <AppShell userName={null} tenantName={null} role={null}>
      <ComingSoon
        title="Upload notice"
        sprint="Sprint 2"
        description="Drag-and-drop upload, mobile capture, and the OCR pipeline arrive in Sprint 2."
      />
    </AppShell>
  );
}
