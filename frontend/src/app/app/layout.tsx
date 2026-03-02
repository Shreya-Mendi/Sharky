import Sidebar from "@/components/layout/Sidebar";
import AppTopBar from "@/components/layout/AppTopBar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-60 transition-all duration-300">
        <AppTopBar />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
