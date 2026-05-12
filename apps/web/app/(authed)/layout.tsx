import { redirect } from "next/navigation";

import { AppShell } from "@/components/shell/app-shell";
import { ToastProvider } from "@/components/ui/toast";
import { readDevSession } from "@/lib/session";

export default function AuthedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  if (!readDevSession()) {
    redirect("/login");
  }
  return (
    <ToastProvider>
      <AppShell>{children}</AppShell>
    </ToastProvider>
  );
}
