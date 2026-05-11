import { redirect } from "next/navigation";

import { Sidebar } from "@/components/sidebar";
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
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1">{children}</div>
      </div>
    </ToastProvider>
  );
}
