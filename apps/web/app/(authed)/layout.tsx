import { redirect } from "next/navigation";

import { Sidebar } from "@/components/sidebar";
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
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1">{children}</div>
    </div>
  );
}
