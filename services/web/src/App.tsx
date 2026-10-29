import { ConsoleShell } from "@/components/console-shell";
import { LoginScreen } from "@/components/login-screen";
import { ErrorState } from "@/components/states";
import { Skeleton } from "@/components/ui/skeleton";
import { useSession } from "@/hooks/use-session";
import { describeError } from "@/lib/network-format";

export function App() {
  const session = useSession();
  if (session.isPending) {
    return (
      <div className="grid min-h-dvh place-items-center px-4" aria-busy="true">
        <Skeleton className="h-64 w-full max-w-sm rounded-xl" />
      </div>
    );
  }
  if (session.isError) {
    return (
      <main className="grid min-h-dvh place-items-center px-4">
        <h1 className="sr-only">ServicioCerca · Consola de operación</h1>
        <ErrorState message={describeError(session.error)} onRetry={() => void session.refetch()} />
      </main>
    );
  }
  return session.data ? <ConsoleShell role={session.data} /> : <LoginScreen />;
}
