import Sidebar from "@/components/layout/Sidebar";
import AppTopBar from "@/components/layout/AppTopBar";
import OnboardingModal from "@/components/ui/OnboardingModal";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-0 md:ml-60 transition-all duration-300">
        <AppTopBar />
        <main className="p-4 md:p-6">{children}</main>
      </div>
      <OnboardingModal />
    </div>
  );
}
